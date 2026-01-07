# Usage Examples

## Example 1: Weekly Product Review

**Scenario:** Product manager wants a weekly summary of customer feedback

**MCP Tool Call:**
```json
{
  "tool": "generate_summary",
  "arguments": {
    "date_range": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-01-07T00:00:00Z"
    },
    "format": "detailed"
  }
}
```

**Expected Response:**
Summary showing:
- 150 total feedback items
- 53% positive sentiment
- Top 3 themes: Login Issues, Feature Requests, Performance
- 15 critical issues requiring attention

**Usage in AI Assistant:**
> "Show me a summary of last week's customer feedback"
>
> AI Assistant calls `generate_summary` and presents:
> "Last week we received 150 feedback items with an overall positive sentiment (53%). The main themes were Login Issues (25 mentions), Feature Requests (20 mentions), and Performance concerns (18 mentions). There are 15 critical issues that need immediate attention."

---

## Example 2: Finding Urgent Issues

**Scenario:** Support lead needs to identify urgent customer issues

**MCP Tool Calls:**

1. Search for critical feedback:
```json
{
  "tool": "search_feedback",
  "arguments": {
    "sentiment": "negative",
    "customer_tier": "enterprise",
    "limit": 50
  }
}
```

2. Prioritize the results:
```json
{
  "tool": "prioritize_issues",
  "arguments": {
    "feedback_ids": ["uuid1", "uuid2", "uuid3", ...],
    "factors": ["customer_tier", "sentiment", "recency"]
  }
}
```

**Usage in AI Assistant:**
> "What are the most urgent customer issues right now?"
>
> AI Assistant:
> 1. Searches for negative feedback from enterprise customers
> 2. Prioritizes by impact
> 3. Presents: "Here are the top 5 urgent issues:
>    1. [Critical] Login failures for Enterprise Corp (Impact: 95)
>    2. [High] Data export broken for Acme Inc (Impact: 87)
>    ..."

---

## Example 3: Tracking Feature Requests

**Scenario:** Product team wants to understand what features customers are requesting

**MCP Tool Calls:**

1. Search for feature requests:
```json
{
  "tool": "search_feedback",
  "arguments": {
    "category": "feature_request",
    "date_range": {
      "start": "2025-12-01T00:00:00Z",
      "end": "2026-01-07T00:00:00Z"
    },
    "limit": 100
  }
}
```

2. Identify themes in feature requests:
```json
{
  "tool": "identify_themes",
  "arguments": {
    "date_range": {
      "start": "2025-12-01T00:00:00Z",
      "end": "2026-01-07T00:00:00Z"
    },
    "num_themes": 15,
    "min_frequency": 3
  }
}
```

**Usage in AI Assistant:**
> "What features are customers requesting most?"
>
> AI Assistant:
> 1. Retrieves feature request feedback
> 2. Extracts themes
> 3. Presents: "Top requested features based on 85 feature requests:
>    1. Dark Mode (mentioned 23 times)
>    2. Mobile App (mentioned 18 times)
>    3. API Webhooks (mentioned 15 times)
>    ..."

---

## Example 4: Sentiment Trend Analysis

**Scenario:** Executive team wants to understand if customer sentiment is improving

**MCP Resource Access:**
```
feedback://trends
```

**Then MCP Tool Call:**
```json
{
  "tool": "analyze_sentiment",
  "arguments": {
    "feedback_ids": ["all-from-last-30-days"],
    "include_trends": true
  }
}
```

**Usage in AI Assistant:**
> "Is customer sentiment improving or declining?"
>
> AI Assistant:
> 1. Accesses trends resource
> 2. Analyzes sentiment with trends enabled
> 3. Presents: "Customer sentiment analysis for the last 30 days:
>    - Overall sentiment: Slightly Positive (score: 0.15)
>    - Trend: Improving (+0.08 from previous period)
>    - Week 1: 0.05, Week 2: 0.12, Week 3: 0.18, Week 4: 0.21
>    Customer sentiment has been steadily improving over the month."

---

## Example 5: Customer Tier Analysis

**Scenario:** Sales team wants to understand feedback from enterprise customers

**MCP Tool Calls:**

1. Search enterprise feedback:
```json
{
  "tool": "search_feedback",
  "arguments": {
    "customer_tier": "enterprise",
    "date_range": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-01-07T00:00:00Z"
    }
  }
}
```

2. Analyze sentiment:
```json
{
  "tool": "analyze_sentiment",
  "arguments": {
    "feedback_ids": ["enterprise-feedback-ids"],
    "include_trends": false
  }
}
```

3. Identify themes:
```json
{
  "tool": "identify_themes",
  "arguments": {
    "date_range": {
      "start": "2026-01-01T00:00:00Z",
      "end": "2026-01-07T00:00:00Z"
    },
    "num_themes": 10
  }
}
```

**Usage in AI Assistant:**
> "How are our enterprise customers feeling about the product?"
>
> AI Assistant:
> 1. Retrieves enterprise customer feedback
> 2. Analyzes sentiment and themes
> 3. Presents: "Enterprise Customer Feedback (Last 7 Days):
>    - 45 feedback items received
>    - Overall sentiment: Positive (62% positive, 28% neutral, 10% negative)
>    - Top concerns: Integration Complexity, Documentation, Performance
>    - Top praise: Customer Support, Feature Set, Reliability
>    - 3 critical issues requiring attention"

---

## Integration with AI Workflows

### Claude Desktop Integration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "feedback-analysis": {
      "command": "python",
      "args": ["-m", "src.server"],
      "env": {
        "DATABASE_URL": "postgresql://...",
        "ELASTICSEARCH_URL": "http://localhost:9200"
      }
    }
  }
}
```

### Example Conversation Flow

**User:** "What are customers saying about our mobile app?"

**Claude:** Let me check the feedback data...
- Calls `search_feedback` with query="mobile app"
- Calls `analyze_sentiment` on results
- Calls `identify_themes` for mobile app feedback

**Claude responds:** "Based on 32 feedback items about the mobile app:
- Overall sentiment is mixed (50% positive, 31% negative, 19% neutral)
- Main complaints: App crashes (12 mentions), slow performance (8 mentions)
- Main praise: Clean UI (15 mentions), easy to use (10 mentions)
- Recommendation: Focus on stability and performance improvements"
