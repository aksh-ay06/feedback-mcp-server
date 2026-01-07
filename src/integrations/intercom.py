"""
Intercom Integration

Fetches customer feedback from Intercom conversations
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseIntegration

logger = logging.getLogger(__name__)


class IntercomIntegration(BaseIntegration):
    """Integration with Intercom"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Intercom integration
        
        Args:
            config: Configuration with access_token
        """
        super().__init__(config)
        self.client = None
        self.access_token = config.get('access_token')
    
    def get_source_name(self) -> str:
        return "intercom"
    
    def get_required_config_fields(self) -> List[str]:
        return ['access_token']
    
    async def authenticate(self) -> bool:
        """Authenticate with Intercom API"""
        try:
            from intercom.client import Client
            
            self.client = Client(personal_access_token=self.access_token)
            
            # Test authentication
            me = self.client.admins.me()
            logger.info(f"Authenticated with Intercom as {me.name}")
            
            return True
        except Exception as e:
            logger.error(f"Intercom authentication failed: {e}")
            return False
    
    async def fetch_feedback(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch conversations from Intercom
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of conversations to fetch
            
        Returns:
            List of normalized feedback dictionaries
        """
        if not self.client:
            authenticated = await self.authenticate()
            if not authenticated:
                return []
        
        try:
            feedback_list = []
            
            # Build filter parameters
            filters = {}
            if start_date:
                filters['created_at_after'] = int(start_date.timestamp())
            if end_date:
                filters['created_at_before'] = int(end_date.timestamp())
            
            # Fetch conversations
            conversations = self.client.conversations.find_all(**filters)
            
            count = 0
            for conversation in conversations:
                if limit and count >= limit:
                    break
                
                await self.handle_rate_limit()
                
                # Convert conversation to normalized format
                normalized = self._normalize_conversation(conversation)
                if normalized:
                    feedback_list.append(normalized)
                    count += 1
            
            logger.info(f"Fetched {len(feedback_list)} conversations from Intercom")
            return feedback_list
        except Exception as e:
            logger.error(f"Error fetching Intercom conversations: {e}")
            return []
    
    def _normalize_conversation(self, conversation) -> Optional[Dict[str, Any]]:
        """Normalize Intercom conversation to common format"""
        try:
            # Extract user information
            user = conversation.user
            customer_id = str(user.id) if user else ""
            customer_email = user.email if user and hasattr(user, 'email') else ""
            customer_name = user.name if user and hasattr(user, 'name') else ""
            
            # Determine customer tier
            customer_tier = self._determine_customer_tier(user)
            
            # Extract conversation content
            title = conversation.source.subject if hasattr(conversation.source, 'subject') else "Intercom Conversation"
            
            # Combine all parts into content
            content_parts = []
            for part in conversation.conversation_parts:
                if hasattr(part, 'body'):
                    content_parts.append(part.body)
            
            content = "\n\n".join(content_parts) if content_parts else ""
            
            # If no parts, use the initial message
            if not content and hasattr(conversation, 'source') and hasattr(conversation.source, 'body'):
                content = conversation.source.body
            
            return {
                "source": "intercom",
                "source_id": str(conversation.id),
                "title": title,
                "content": content,
                "customer_id": customer_id,
                "customer_email": customer_email,
                "customer_name": customer_name,
                "customer_tier": customer_tier,
                "category": self._categorize_conversation(conversation),
                "created_at": datetime.fromtimestamp(conversation.created_at),
                "metadata": {
                    "conversation_id": conversation.id,
                    "state": conversation.state,
                    "tags": [tag.name for tag in getattr(conversation, 'tags', [])],
                    "assignee": conversation.assignee.id if conversation.assignee else None
                }
            }
        except Exception as e:
            logger.error(f"Error normalizing Intercom conversation {conversation.id}: {e}")
            return None
    
    def _determine_customer_tier(self, user) -> str:
        """Determine customer tier from user data"""
        if not user:
            return 'free'
        
        # Check custom attributes
        if hasattr(user, 'custom_attributes'):
            plan = user.custom_attributes.get('plan', '').lower()
            
            if 'enterprise' in plan:
                return 'enterprise'
            elif 'business' in plan or 'professional' in plan:
                return 'business'
            elif 'pro' in plan:
                return 'professional'
        
        return 'free'
    
    def _categorize_conversation(self, conversation) -> str:
        """Categorize conversation based on tags"""
        if not hasattr(conversation, 'tags') or not conversation.tags:
            return 'general'
        
        # Map tags to categories
        tag_categories = {
            'bug': 'bug_report',
            'feature': 'feature_request',
            'question': 'support',
            'billing': 'billing',
            'technical': 'technical',
            'feedback': 'feedback'
        }
        
        for tag in conversation.tags:
            tag_name = tag.name.lower()
            for key, category in tag_categories.items():
                if key in tag_name:
                    return category
        
        return 'general'
    
    async def register_webhook(self, webhook_url: str) -> bool:
        """
        Register webhook for real-time conversation updates
        
        Args:
            webhook_url: URL to receive webhook notifications
            
        Returns:
            True if webhook registered successfully
        """
        if not self.client:
            authenticated = await self.authenticate()
            if not authenticated:
                return False
        
        try:
            # Register webhook subscription
            subscription = self.client.subscriptions.create(
                url=webhook_url,
                topics=['conversation.user.created', 'conversation.user.replied']
            )
            
            logger.info(f"Intercom webhook registered: {subscription.id}")
            return True
        except Exception as e:
            logger.error(f"Error registering Intercom webhook: {e}")
            return False
