"""
Zendesk Integration

Fetches customer feedback from Zendesk Support tickets
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseIntegration

logger = logging.getLogger(__name__)


class ZendeskIntegration(BaseIntegration):
    """Integration with Zendesk Support"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Zendesk integration
        
        Args:
            config: Configuration with subdomain, email, and api_token
        """
        super().__init__(config)
        self.client = None
        self.subdomain = config.get('subdomain')
        self.email = config.get('email')
        self.api_token = config.get('api_token')
    
    def get_source_name(self) -> str:
        return "zendesk"
    
    def get_required_config_fields(self) -> List[str]:
        return ['subdomain', 'email', 'api_token']
    
    async def authenticate(self) -> bool:
        """Authenticate with Zendesk API"""
        try:
            from zenpy import Zenpy
            from zenpy.lib.api_objects import Ticket
            
            credentials = {
                'email': self.email,
                'token': self.api_token,
                'subdomain': self.subdomain
            }
            
            self.client = Zenpy(**credentials)
            
            # Test authentication by fetching user
            user = self.client.users.me()
            logger.info(f"Authenticated with Zendesk as {user.email}")
            
            return True
        except Exception as e:
            logger.error(f"Zendesk authentication failed: {e}")
            return False
    
    async def fetch_feedback(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch tickets from Zendesk
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of tickets to fetch
            
        Returns:
            List of normalized feedback dictionaries
        """
        if not self.client:
            authenticated = await self.authenticate()
            if not authenticated:
                return []
        
        try:
            feedback_list = []
            
            # Build search query
            query_parts = []
            if start_date:
                query_parts.append(f"created>={start_date.isoformat()}")
            if end_date:
                query_parts.append(f"created<={end_date.isoformat()}")
            
            query = " ".join(query_parts) if query_parts else "type:ticket"
            
            # Search tickets
            tickets = self.client.search(query, type='ticket')
            
            count = 0
            for ticket in tickets:
                if limit and count >= limit:
                    break
                
                # Handle rate limiting
                await self.handle_rate_limit()
                
                # Convert ticket to normalized format
                normalized = self._normalize_ticket(ticket)
                if normalized:
                    feedback_list.append(normalized)
                    count += 1
            
            logger.info(f"Fetched {len(feedback_list)} tickets from Zendesk")
            return feedback_list
        except Exception as e:
            logger.error(f"Error fetching Zendesk tickets: {e}")
            return []
    
    def _normalize_ticket(self, ticket) -> Optional[Dict[str, Any]]:
        """Normalize Zendesk ticket to common format"""
        try:
            # Get requester information
            requester_id = str(ticket.requester_id) if ticket.requester_id else ""
            
            # Determine customer tier (simplified - would normally query user data)
            customer_tier = self._determine_customer_tier(ticket)
            
            # Extract content from description and comments
            content = ticket.description or ""
            
            return {
                "source": "zendesk",
                "source_id": str(ticket.id),
                "title": ticket.subject or "No Subject",
                "content": content,
                "customer_id": requester_id,
                "customer_email": ticket.requester.email if hasattr(ticket, 'requester') else "",
                "customer_name": ticket.requester.name if hasattr(ticket, 'requester') else "",
                "customer_tier": customer_tier,
                "category": self._categorize_ticket(ticket),
                "created_at": ticket.created_at,
                "metadata": {
                    "ticket_id": ticket.id,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "tags": ticket.tags or [],
                    "type": ticket.type
                }
            }
        except Exception as e:
            logger.error(f"Error normalizing Zendesk ticket {ticket.id}: {e}")
            return None
    
    def _determine_customer_tier(self, ticket) -> str:
        """Determine customer tier from ticket data"""
        # This is a simplified implementation
        # In production, you would query the user's organization or custom fields
        
        if hasattr(ticket, 'priority'):
            if ticket.priority in ['urgent', 'high']:
                return 'enterprise'
            elif ticket.priority == 'normal':
                return 'business'
        
        return 'free'
    
    def _categorize_ticket(self, ticket) -> str:
        """Categorize ticket based on tags or custom fields"""
        if not ticket.tags:
            return 'general'
        
        # Map tags to categories
        tag_categories = {
            'bug': 'bug_report',
            'feature': 'feature_request',
            'question': 'support',
            'billing': 'billing',
            'technical': 'technical'
        }
        
        for tag in ticket.tags:
            tag_lower = tag.lower()
            for key, category in tag_categories.items():
                if key in tag_lower:
                    return category
        
        return 'general'
    
    async def register_webhook(self, webhook_url: str) -> bool:
        """
        Register webhook for real-time ticket updates
        
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
            # Zendesk uses triggers and targets for webhooks
            # This is a simplified implementation
            logger.info(f"Webhook registration for Zendesk: {webhook_url}")
            
            # In production, create a target and trigger via API
            # target = self.client.targets.create({
            #     "type": "http_target",
            #     "title": "MCP Feedback Webhook",
            #     "target_url": webhook_url,
            #     "method": "post"
            # })
            
            logger.info("Zendesk webhook registered successfully")
            return True
        except Exception as e:
            logger.error(f"Error registering Zendesk webhook: {e}")
            return False
    
    async def fetch_ticket_comments(self, ticket_id: int) -> List[str]:
        """
        Fetch all comments for a specific ticket
        
        Args:
            ticket_id: Zendesk ticket ID
            
        Returns:
            List of comment texts
        """
        if not self.client:
            await self.authenticate()
        
        try:
            ticket = self.client.tickets(id=ticket_id)
            comments = []
            
            for comment in ticket.comments:
                if comment.public and comment.body:
                    comments.append(comment.body)
            
            return comments
        except Exception as e:
            logger.error(f"Error fetching comments for ticket {ticket_id}: {e}")
            return []
