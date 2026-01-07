"""
Tests for MCP Tools

Tests the tool implementations for searching, sentiment analysis, etc.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.mcp.tools import FeedbackTools
from src.storage.models import Feedback


@pytest.fixture
def mock_db():
    """Mock database for testing"""
    db = Mock()
    session = Mock()
    
    # Setup context manager
    db.get_session.return_value.__enter__ = Mock(return_value=session)
    db.get_session.return_value.__exit__ = Mock(return_value=None)
    
    return db, session


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return Mock(
        elasticsearch_url="http://localhost:9200",
        redis_url="redis://localhost:6379"
    )


@pytest.fixture
def feedback_tools(mock_db, mock_settings):
    """Create FeedbackTools instance for testing"""
    db, _ = mock_db
    return FeedbackTools(db, mock_settings)


@pytest.fixture
def sample_feedback():
    """Sample feedback items for testing"""
    return [
        Feedback(
            id="1",
            source="zendesk",
            source_id="ticket-1",
            title="Great product",
            content="I love this product, it's amazing!",
            customer_id="cust-1",
            customer_tier="enterprise",
            sentiment="positive",
            sentiment_score=0.9,
            category="feedback",
            created_at=datetime.utcnow()
        ),
        Feedback(
            id="2",
            source="intercom",
            source_id="conv-1",
            title="Bug report",
            content="The app crashes when I click the button",
            customer_id="cust-2",
            customer_tier="business",
            sentiment="negative",
            sentiment_score=-0.8,
            category="bug_report",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
    ]


@pytest.mark.asyncio
async def test_search_feedback_with_query(feedback_tools, mock_db, sample_feedback):
    """Test searching feedback with a text query"""
    db, session = mock_db
    
    # Mock query results
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = sample_feedback
    
    session.query.return_value = query_mock
    
    # Execute search
    result = await feedback_tools.search_feedback(
        query="product",
        limit=10
    )
    
    # Assertions
    assert result["success"] is True
    assert result["count"] == 2
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Great product"


@pytest.mark.asyncio
async def test_search_feedback_with_filters(feedback_tools, mock_db, sample_feedback):
    """Test searching feedback with filters"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = [sample_feedback[0]]
    
    session.query.return_value = query_mock
    
    result = await feedback_tools.search_feedback(
        sentiment="positive",
        customer_tier="enterprise",
        limit=50
    )
    
    assert result["success"] is True
    assert result["count"] == 1
    assert result["filters_applied"]["sentiment"] == "positive"


@pytest.mark.asyncio
async def test_analyze_sentiment(feedback_tools, mock_db, sample_feedback):
    """Test sentiment analysis tool"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_feedback
    
    session.query.return_value = query_mock
    
    result = await feedback_tools.analyze_sentiment(
        feedback_ids=["1", "2"],
        include_trends=False
    )
    
    assert result["success"] is True
    assert result["count"] == 2
    assert "summary" in result
    assert "sentiment_distribution" in result["summary"]


@pytest.mark.asyncio
async def test_analyze_sentiment_with_trends(feedback_tools, mock_db, sample_feedback):
    """Test sentiment analysis with trends"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_feedback
    
    session.query.return_value = query_mock
    
    result = await feedback_tools.analyze_sentiment(
        feedback_ids=["1", "2"],
        include_trends=True
    )
    
    assert result["success"] is True
    assert "trends" in result


@pytest.mark.asyncio
async def test_identify_themes(feedback_tools, mock_db, sample_feedback):
    """Test theme identification"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_feedback
    
    session.query.return_value = query_mock
    
    with patch.object(feedback_tools.theme_extractor, 'extract_themes') as mock_extract:
        mock_extract.return_value = [
            {"name": "Product Quality", "frequency": 5, "keywords": ["great", "amazing"]}
        ]
        
        result = await feedback_tools.identify_themes(
            num_themes=10,
            min_frequency=2
        )
        
        assert result["success"] is True
        assert "themes" in result
        assert len(result["themes"]) > 0


@pytest.mark.asyncio
async def test_prioritize_issues(feedback_tools, mock_db, sample_feedback):
    """Test issue prioritization"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_feedback
    
    session.query.return_value = query_mock
    
    result = await feedback_tools.prioritize_issues(
        feedback_ids=["1", "2"],
        factors=["customer_tier", "sentiment", "recency"]
    )
    
    assert result["success"] is True
    assert result["count"] == 2
    assert "results" in result
    
    # Check that results are sorted by impact score
    scores = [item["impact_score"] for item in result["results"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_generate_summary_brief(feedback_tools, mock_db, sample_feedback):
    """Test brief summary generation"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_feedback
    
    session.query.return_value = query_mock
    
    result = await feedback_tools.generate_summary(format="brief")
    
    assert result["success"] is True
    assert "summary" in result
    assert "overview" in result["summary"]


@pytest.mark.asyncio
async def test_generate_summary_detailed(feedback_tools, mock_db, sample_feedback):
    """Test detailed summary generation"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = sample_feedback
    
    session.query.return_value = query_mock
    
    result = await feedback_tools.generate_summary(format="detailed")
    
    assert result["success"] is True
    assert "summary" in result
    assert "detailed_metrics" in result["summary"]


@pytest.mark.asyncio
async def test_search_feedback_empty_results(feedback_tools, mock_db):
    """Test search with no results"""
    db, session = mock_db
    
    query_mock = Mock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.all.return_value = []
    
    session.query.return_value = query_mock
    
    result = await feedback_tools.search_feedback(query="nonexistent")
    
    assert result["success"] is True
    assert result["count"] == 0
    assert len(result["results"]) == 0


@pytest.mark.asyncio
async def test_error_handling(feedback_tools, mock_db):
    """Test error handling in tools"""
    db, session = mock_db
    
    # Simulate database error
    session.query.side_effect = Exception("Database error")
    
    result = await feedback_tools.search_feedback(query="test")
    
    assert result["success"] is False
    assert "error" in result
