# Data Source Integrations Guide

## Overview

This guide explains how to configure and use data source integrations for fetching customer feedback.

## Supported Data Sources

1. **Zendesk Support** - Support tickets and customer inquiries
2. **Intercom** - Customer conversations and messages
3. **SurveyMonkey** - Survey responses (implementation template included)

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Zendesk
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@example.com
ZENDESK_API_TOKEN=your-api-token

# Intercom
INTERCOM_ACCESS_TOKEN=your-intercom-token

# SurveyMonkey
SURVEYMONKEY_ACCESS_TOKEN=your-surveymonkey-token
```

## Zendesk Integration

### Getting API Credentials

1. Log in to Zendesk as an admin
2. Go to Admin Center → Apps and integrations → APIs → Zendesk API
3. Enable token access
4. Click "Add API token"
5. Copy the token (you won't be able to see it again)

### Configuration

```python
from src.integrations.zendesk import ZendeskIntegration

config = {
    'subdomain': 'your-company',
    'email': 'admin@your-company.com',
    'api_token': 'your-token-here'
}

zendesk = ZendeskIntegration(config)
```

### Usage

```python
# Test connection
await zendesk.test_connection()

# Fetch recent tickets
from datetime import datetime, timedelta

start_date = datetime.utcnow() - timedelta(days=7)
tickets = await zendesk.fetch_feedback(start_date=start_date)

# Register webhook
await zendesk.register_webhook('https://your-server.com/webhooks/zendesk')
```

### Data Mapping

| Zendesk Field | Normalized Field |
|---------------|------------------|
| ticket.id | source_id |
| ticket.subject | title |
| ticket.description | content |
| ticket.requester_id | customer_id |
| ticket.priority | Mapped to severity |
| ticket.tags | Used for categorization |

## Intercom Integration

### Getting API Credentials

1. Log in to Intercom
2. Go to Settings → Developers → Developer Hub
3. Create a new app
4. Generate an access token with appropriate scopes:
   - Read conversations
   - Read users
   - Manage webhooks

### Configuration

```python
from src.integrations.intercom import IntercomIntegration

config = {
    'access_token': 'your-access-token'
}

intercom = IntercomIntegration(config)
```

### Usage

```python
# Test connection
await intercom.test_connection()

# Fetch conversations
conversations = await intercom.fetch_feedback(
    start_date=datetime.utcnow() - timedelta(days=30),
    limit=100
)

# Register webhook
await intercom.register_webhook('https://your-server.com/webhooks/intercom')
```

### Data Mapping

| Intercom Field | Normalized Field |
|----------------|------------------|
| conversation.id | source_id |
| conversation.source.subject | title |
| conversation.parts[].body | content (combined) |
| user.id | customer_id |
| custom_attributes.plan | customer_tier |
| tags | category |

## Adding New Integrations

To add a new data source:

1. Create a new file in `src/integrations/` (e.g., `my_source.py`)
2. Extend `BaseIntegration` class
3. Implement required methods:
   - `authenticate()`
   - `fetch_feedback()`
   - `register_webhook()`
   - `get_source_name()`
   - `get_required_config_fields()`

### Example Template

```python
from .base import BaseIntegration
from typing import Dict, List, Any, Optional
from datetime import datetime

class MySourceIntegration(BaseIntegration):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
    
    def get_source_name(self) -> str:
        return "my_source"
    
    def get_required_config_fields(self) -> List[str]:
        return ['api_key']
    
    async def authenticate(self) -> bool:
        # Implement authentication logic
        pass
    
    async def fetch_feedback(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        # Implement data fetching
        pass
    
    async def register_webhook(self, webhook_url: str) -> bool:
        # Implement webhook registration
        pass
```

## Webhooks

### Setting Up Webhook Endpoints

The server automatically creates webhook endpoints at:
- `/webhooks/zendesk` - For Zendesk notifications
- `/webhooks/intercom` - For Intercom notifications

### Webhook Security

1. Verify webhook signatures
2. Use HTTPS in production
3. Implement rate limiting
4. Log all webhook events

### Example Webhook Handler

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhooks/zendesk")
async def zendesk_webhook(request: Request):
    data = await request.json()
    
    # Verify signature
    # Process webhook data
    # Store feedback
    
    return {"status": "received"}
```

## Data Normalization

All integrations normalize feedback to this standard format:

```python
{
    "source": "zendesk|intercom|...",
    "source_id": "original-id",
    "title": "Feedback title",
    "content": "Feedback content/description",
    "customer_id": "customer-identifier",
    "customer_email": "customer@example.com",
    "customer_name": "Customer Name",
    "customer_tier": "enterprise|business|professional|free",
    "category": "bug_report|feature_request|support|...",
    "created_at": datetime_object,
    "metadata": {
        # Source-specific additional data
    }
}
```

## Rate Limiting

### Zendesk
- 400 requests per minute per account
- Automatically handled with exponential backoff

### Intercom
- 500 requests per minute
- Burst allowance of 1000 requests

### Best Practices
1. Implement caching
2. Use webhooks for real-time updates
3. Batch fetch historical data during off-peak hours
4. Monitor rate limit headers

## Troubleshooting

### Connection Issues

```python
# Test individual integration
integration = ZendeskIntegration(config)
is_connected = await integration.test_connection()
print(f"Connection status: {is_connected}")
```

### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Errors

1. **Authentication Failed**
   - Check API credentials
   - Verify token hasn't expired
   - Ensure proper permissions

2. **Rate Limit Exceeded**
   - Implement backoff strategy
   - Use webhook for real-time updates
   - Reduce fetch frequency

3. **Data Not Found**
   - Check date range filters
   - Verify data exists in source system
   - Check API permissions

## Performance Optimization

1. **Use Pagination**
   ```python
   # Fetch in batches
   for page in range(0, total_pages):
       batch = await fetch_feedback(offset=page*100, limit=100)
   ```

2. **Parallel Fetching**
   ```python
   import asyncio
   
   results = await asyncio.gather(
       zendesk.fetch_feedback(),
       intercom.fetch_feedback()
   )
   ```

3. **Incremental Sync**
   ```python
   # Only fetch new data since last sync
   last_sync = get_last_sync_time()
   new_data = await fetch_feedback(start_date=last_sync)
   ```
