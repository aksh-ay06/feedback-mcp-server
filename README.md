# Customer Feedback Analysis MCP Server

An MCP (Model Context Protocol) server that aggregates and analyzes customer feedback from multiple sources (Zendesk, Intercom, SurveyMonkey) to provide AI assistants with actionable insights.

## Features

- **Multi-Source Data Integration**: Connects to Zendesk, Intercom, and SurveyMonkey
- **Real-Time Processing**: Webhook support for instant feedback analysis
- **Intelligent Analysis**: Sentiment analysis, theme extraction, and impact prioritization
- **MCP Protocol**: Exposes resources and tools via Model Context Protocol
- **Scalable Architecture**: PostgreSQL, Elasticsearch, Redis for high performance

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Elasticsearch 8+
- Redis 7+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd feedback-mcp-server
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your actual configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
python -m src.server
```

## MCP Resources

- `feedback://recent` - Recent feedback (last 7 days)
- `feedback://critical` - Critical/urgent feedback
- `feedback://trends` - Aggregated trends and themes

## MCP Tools

1. **search_feedback** - Search feedback with filters
2. **analyze_sentiment** - Sentiment analysis with trends
3. **identify_themes** - Theme extraction and clustering
4. **prioritize_issues** - Business impact ranking
5. **generate_summary** - Executive summaries

## Architecture

```
┌─────────────────┐
│  AI Assistant   │
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────┐
│   MCP Server    │
├─────────────────┤
│  Resources      │
│  Tools          │
└────────┬────────┘
         │
┌────────▼────────────────────────┐
│  Data Processing Pipeline       │
│  - Sentiment Analysis           │
│  - Theme Extraction             │
│  - Impact Prioritization        │
└────────┬────────────────────────┘
         │
┌────────▼──────────────────────────────┐
│  Data Sources                         │
│  - Zendesk    - Intercom             │
│  - SurveyMonkey                       │
└───────────────────────────────────────┘
```

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Quality

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

## Docker Deployment

```bash
docker-compose up -d
```

## Documentation

See the [docs](./docs) folder for detailed documentation:
- [API Documentation](./docs/api.md)
- [Integration Guide](./docs/integrations.md)
- [Usage Examples](./docs/examples.md)

## License

MIT License
