# API Documentation

## MCP Resources

### feedback://recent

Returns feedback from the last 7 days.

**Response Format:**
```json
{
  "uri": "feedback://recent",
  "mimeType": "application/json",
  "text": "Formatted feedback list...",
  "metadata": {
    "total_count": 150,
    "days": 7,
    "date_range": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-01-07T00:00:00Z"
    },
    "sentiment_breakdown": {
      "positive": 80,
      "negative": 50,
      "neutral": 20
    }
  }
}
```

### feedback://critical

Returns critical/urgent feedback requiring immediate attention.

**Response Format:**
```json
{
  "uri": "feedback://critical",
  "mimeType": "application/json",
  "text": "Formatted critical feedback...",
  "metadata": {
    "total_count": 15,
    "severity_levels": {
      "critical": 5,
      "high": 10
    },
    "requires_immediate_action": 15
  }
}
```

### feedback://trends

Returns aggregated trends and themes from feedback.

**Response Format:**
```json
{
  "uri": "feedback://trends",
  "mimeType": "application/json",
  "text": "Formatted trends...",
  "metadata": {
    "date_range": {...},
    "top_themes": [...],
    "sentiment_trends": [...],
    "by_source": {...}
  }
}
```

## MCP Tools

### search_feedback

Search customer feedback with various filters.

**Input Schema:**
```json
{
  "query": "string (optional)",
  "date_range": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-07T00:00:00Z"
  },
  "sentiment": "positive|negative|neutral (optional)",
  "customer_tier": "enterprise|business|professional|free (optional)",
  "category": "string (optional)",
  "limit": 50
}
```

**Example:**
```json
{
  "query": "login issue",
  "sentiment": "negative",
  "customer_tier": "enterprise",
  "limit": 20
}
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "title": "Cannot login to account",
      "content": "...",
      "source": "zendesk",
      "sentiment": "negative",
      "sentiment_score": -0.7,
      "customer_id": "cust-123",
      "customer_tier": "enterprise",
      "category": "bug_report",
      "created_at": "2026-01-06T10:30:00Z",
      "impact_score": 85
    }
  ],
  "filters_applied": {...}
}
```

### analyze_sentiment

Analyze sentiment of specified feedback items.

**Input Schema:**
```json
{
  "feedback_ids": ["uuid1", "uuid2"],
  "include_trends": true
}
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": "uuid1",
      "title": "...",
      "sentiment": "positive",
      "score": 0.85,
      "confidence": 0.85
    }
  ],
  "summary": {
    "average_sentiment_score": 0.5,
    "sentiment_distribution": {
      "positive": 1,
      "negative": 0,
      "neutral": 1
    },
    "overall_sentiment": "positive"
  },
  "trends": {...}
}
```

### identify_themes

Extract and cluster themes from feedback.

**Input Schema:**
```json
{
  "date_range": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-07T00:00:00Z"
  },
  "num_themes": 10,
  "min_frequency": 3
}
```

**Response:**
```json
{
  "success": true,
  "count": 8,
  "themes": [
    {
      "name": "Login Issues",
      "keywords": ["login", "authentication", "password"],
      "frequency": 25,
      "confidence": 0.75
    }
  ],
  "metadata": {...}
}
```

### prioritize_issues

Rank feedback by business impact.

**Input Schema:**
```json
{
  "feedback_ids": ["uuid1", "uuid2"],
  "factors": ["customer_tier", "sentiment", "frequency", "recency"]
}
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": "uuid1",
      "title": "...",
      "impact_score": 85,
      "customer_tier": "enterprise",
      "sentiment": "negative",
      "created_at": "2026-01-06T10:30:00Z",
      "priority_level": "critical"
    }
  ],
  "factors_used": [...]
}
```

### generate_summary

Generate executive summary of feedback.

**Input Schema:**
```json
{
  "date_range": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-07T00:00:00Z"
  },
  "format": "brief|detailed"
}
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "overview": {
      "total_feedback": 150,
      "sentiment_breakdown": {...},
      "critical_issues": 15,
      "response_rate": "53.3%"
    },
    "key_insights": [
      "Received 150 feedback items in the period",
      "50 negative feedback items require attention"
    ],
    "detailed_metrics": {...}
  }
}
```

## Error Responses

All tools return error responses in this format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

## Rate Limits

- Search: 100 requests/minute
- Sentiment Analysis: 50 requests/minute
- Theme Extraction: 20 requests/minute
- Other tools: 60 requests/minute
