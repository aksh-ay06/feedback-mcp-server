# Quick Reference

## 🚀 Common Commands

### Setup
```bash
./setup.sh                    # Initial setup
source venv/bin/activate      # Activate environment
```

### Running
```bash
# Development
python -m src.server

# Docker
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose logs -f        # View logs
```

### Testing
```bash
pytest tests/                 # Run all tests
pytest tests/ -v              # Verbose output
pytest tests/ --cov=src       # With coverage
```

### Code Quality
```bash
black src/ tests/             # Format code
isort src/ tests/             # Sort imports
flake8 src/ tests/            # Lint
mypy src/                     # Type check
```

---

## 📡 MCP Resources

| Resource | Description |
|----------|-------------|
| `feedback://recent` | Last 7 days of feedback |
| `feedback://critical` | Urgent issues |
| `feedback://trends` | Aggregated trends |

---

## 🔧 MCP Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `search_feedback` | Find feedback | query, sentiment, tier |
| `analyze_sentiment` | Sentiment analysis | feedback_ids, include_trends |
| `identify_themes` | Extract themes | date_range, num_themes |
| `prioritize_issues` | Rank by impact | feedback_ids, factors |
| `generate_summary` | Executive summary | date_range, format |

---

## 🔌 API Endpoints

```
GET  /health                   # Health check
POST /webhooks/zendesk         # Zendesk webhook
POST /webhooks/intercom        # Intercom webhook
```

---

## 🗄️ Database

### Connect
```bash
psql postgresql://user:password@localhost:5432/feedback_mcp
```

### Common Queries
```sql
-- Count feedback by sentiment
SELECT sentiment, COUNT(*) FROM feedback GROUP BY sentiment;

-- Top themes
SELECT name, frequency FROM themes ORDER BY frequency DESC LIMIT 10;

-- Critical feedback
SELECT * FROM feedback WHERE severity IN ('critical', 'high');
```

---

## 🐳 Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database |
| Elasticsearch | 9200 | Search |
| Redis | 6379 | Cache |
| MCP Server | 8000 | API |

---

## 📝 Environment Variables

### Required
```bash
DATABASE_URL=postgresql://...
ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6379
```

### Zendesk
```bash
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email
ZENDESK_API_TOKEN=your-token
```

### Intercom
```bash
INTERCOM_ACCESS_TOKEN=your-token
```

---

## 🐛 Troubleshooting

### Database connection failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres
docker-compose logs postgres

# Verify credentials
echo $DATABASE_URL
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Tests failing
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run with verbose output
pytest tests/ -v -s
```

---

## 📚 File Locations

| What | Where |
|------|-------|
| Main server | `src/server.py` |
| Resources | `src/mcp/resources.py` |
| Tools | `src/mcp/tools.py` |
| Models | `src/storage/models.py` |
| Tests | `tests/test_tools.py` |
| Config | `.env` |
| Docs | `docs/` |

---

## 🎯 Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**
   - Edit code
   - Run tests: `pytest tests/`
   - Format: `black src/`

3. **Commit**
   ```bash
   git add .
   git commit -m "Add feature"
   ```

4. **Deploy**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

---

## 🔍 Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m src.server

# Or in .env
LOG_LEVEL=DEBUG
```

---

## 📦 Dependencies Update

```bash
# Update all
pip install --upgrade -r requirements.txt

# Update specific
pip install --upgrade transformers

# Freeze current
pip freeze > requirements.txt
```

---

## 🎨 Code Style

- **Format**: Black (88 chars)
- **Imports**: isort
- **Docstrings**: Google style
- **Type hints**: Required for functions

---

## 📞 Getting Help

1. Check `IMPLEMENTATION_SUMMARY.md`
2. Read `docs/api.md`
3. Review `docs/examples.md`
4. Check logs: `docker-compose logs`
