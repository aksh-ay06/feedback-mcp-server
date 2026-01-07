"""
Base Integration Class

Abstract base class for all data source integrations
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from time import sleep

logger = logging.getLogger(__name__)


class BaseIntegration(ABC):
    """Abstract base class for data source integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize integration
        
        Args:
            config: Configuration dictionary with credentials and settings
        """
        self.config = config
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the data source
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def fetch_feedback(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch feedback from the data source
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of items to fetch
            
        Returns:
            List of feedback dictionaries in normalized format
        """
        pass
    
    @abstractmethod
    async def register_webhook(self, webhook_url: str) -> bool:
        """
        Register a webhook for real-time updates
        
        Args:
            webhook_url: URL to receive webhook notifications
            
        Returns:
            True if webhook registered successfully
        """
        pass
    
    def normalize_feedback(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize feedback data to common format
        
        Args:
            raw_data: Raw feedback data from source
            
        Returns:
            Normalized feedback dictionary
        """
        return {
            "source": self.get_source_name(),
            "source_id": str(raw_data.get("id", "")),
            "title": raw_data.get("title", ""),
            "content": raw_data.get("content", ""),
            "customer_id": raw_data.get("customer_id", ""),
            "customer_email": raw_data.get("customer_email", ""),
            "customer_name": raw_data.get("customer_name", ""),
            "created_at": self._parse_date(raw_data.get("created_at")),
            "metadata": raw_data.get("metadata", {})
        }
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of this data source
        
        Returns:
            Source name (e.g., "zendesk", "intercom")
        """
        pass
    
    async def handle_rate_limit(self):
        """Handle rate limiting with exponential backoff"""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
            if self.rate_limit_reset:
                wait_time = (self.rate_limit_reset - datetime.utcnow()).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Rate limit reached. Waiting {wait_time:.0f} seconds...")
                    sleep(min(wait_time, 300))  # Max 5 minutes wait
    
    async def retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Any:
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            
        Returns:
            Function result
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    sleep(delay)
        
        # All retries failed
        logger.error(f"All {max_retries} attempts failed: {last_exception}")
        raise last_exception
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse various date formats to datetime"""
        if isinstance(date_str, datetime):
            return date_str
        
        if isinstance(date_str, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                pass
            
            try:
                # Try common formats
                from dateutil import parser
                return parser.parse(date_str)
            except Exception:
                logger.warning(f"Could not parse date: {date_str}")
        
        return None
    
    async def validate_config(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if configuration is valid
        """
        required_fields = self.get_required_config_fields()
        
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                logger.error(f"Missing required configuration field: {field}")
                return False
        
        return True
    
    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """
        Get list of required configuration fields
        
        Returns:
            List of required field names
        """
        pass
    
    async def test_connection(self) -> bool:
        """
        Test connection to data source
        
        Returns:
            True if connection successful
        """
        try:
            is_valid = await self.validate_config()
            if not is_valid:
                return False
            
            is_authenticated = await self.authenticate()
            if not is_authenticated:
                return False
            
            logger.info(f"{self.get_source_name()} connection test successful")
            return True
        except Exception as e:
            logger.error(f"{self.get_source_name()} connection test failed: {e}")
            return False
