"""
MCP Tools for Customer Feedback Analysis

Implements the tool handlers for the MCP protocol:
- search_feedback: Natural language and structured search
- analyze_sentiment: Sentiment analysis with trends
- identify_themes: Theme extraction and clustering
- prioritize_issues: Business impact ranking
- generate_summary: Executive summaries
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_

from ..processing.sentiment import SentimentAnalyzer
from ..processing.themes import ThemeExtractor
from ..storage.models import Feedback

logger = logging.getLogger(__name__)


class FeedbackTools:
    """Implements MCP tools for feedback analysis"""
    
    def __init__(self, db, settings):
        self.db = db
        self.settings = settings
        self.sentiment_analyzer = SentimentAnalyzer()
        self.theme_extractor = ThemeExtractor()
    
    async def search_feedback(
        self,
        query: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None,
        sentiment: Optional[str] = None,
        customer_tier: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search customer feedback with various filters
        
        Args:
            query: Natural language search query
            date_range: Date range filter with 'start' and 'end'
            sentiment: Filter by sentiment (positive/negative/neutral)
            customer_tier: Filter by customer tier
            category: Filter by feedback category
            limit: Maximum number of results
            
        Returns:
            Search results with matching feedback items
        """
        try:
            with self.db.get_session() as session:
                # Build query
                filters = []
                
                if date_range:
                    start = datetime.fromisoformat(date_range.get('start'))
                    end = datetime.fromisoformat(date_range.get('end'))
                    filters.append(Feedback.created_at.between(start, end))
                
                if sentiment:
                    filters.append(Feedback.sentiment == sentiment)
                
                if customer_tier:
                    filters.append(Feedback.customer_tier == customer_tier)
                
                if category:
                    filters.append(Feedback.category == category)
                
                if query:
                    # Simple text search (in production, use Elasticsearch)
                    filters.append(
                        or_(
                            Feedback.title.ilike(f'%{query}%'),
                            Feedback.content.ilike(f'%{query}%')
                        )
                    )
                
                # Execute query
                results = session.query(Feedback)
                if filters:
                    results = results.filter(and_(*filters))
                
                results = results.order_by(
                    desc(Feedback.created_at)
                ).limit(limit).all()
                
                return {
                    "success": True,
                    "count": len(results),
                    "results": [
                        {
                            "id": str(item.id),
                            "title": item.title,
                            "content": item.content,
                            "source": item.source,
                            "sentiment": item.sentiment,
                            "sentiment_score": item.sentiment_score,
                            "customer_id": item.customer_id,
                            "customer_tier": item.customer_tier,
                            "category": item.category,
                            "created_at": item.created_at.isoformat(),
                            "impact_score": item.impact_score
                        }
                        for item in results
                    ],
                    "filters_applied": {
                        "query": query,
                        "date_range": date_range,
                        "sentiment": sentiment,
                        "customer_tier": customer_tier,
                        "category": category
                    }
                }
        except Exception as e:
            logger.error(f"Error searching feedback: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_sentiment(
        self,
        feedback_ids: List[str],
        include_trends: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of specified feedback items
        
        Args:
            feedback_ids: List of feedback IDs to analyze
            include_trends: Whether to include trend analysis
            
        Returns:
            Sentiment analysis results with optional trends
        """
        try:
            with self.db.get_session() as session:
                # Fetch feedback items
                feedback_items = session.query(Feedback).filter(
                    Feedback.id.in_(feedback_ids)
                ).all()
                
                if not feedback_items:
                    return {
                        "success": False,
                        "error": "No feedback items found"
                    }
                
                # Analyze sentiment for each item
                results = []
                sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
                total_score = 0.0
                
                for item in feedback_items:
                    # Use stored sentiment or analyze if missing
                    if item.sentiment and item.sentiment_score is not None:
                        sentiment = item.sentiment
                        score = item.sentiment_score
                    else:
                        sentiment, score = await self.sentiment_analyzer.analyze(item.content)
                    
                    results.append({
                        "id": str(item.id),
                        "title": item.title,
                        "sentiment": sentiment,
                        "score": score,
                        "confidence": abs(score)
                    })
                    
                    sentiment_counts[sentiment] += 1
                    total_score += score
                
                avg_sentiment = total_score / len(feedback_items)
                
                response = {
                    "success": True,
                    "count": len(results),
                    "results": results,
                    "summary": {
                        "average_sentiment_score": avg_sentiment,
                        "sentiment_distribution": sentiment_counts,
                        "overall_sentiment": (
                            "positive" if avg_sentiment > 0.1 else
                            "negative" if avg_sentiment < -0.1 else
                            "neutral"
                        )
                    }
                }
                
                # Add trend analysis if requested
                if include_trends:
                    response["trends"] = await self._calculate_sentiment_trends(
                        session, feedback_items
                    )
                
                return response
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def identify_themes(
        self,
        date_range: Optional[Dict[str, str]] = None,
        num_themes: int = 10,
        min_frequency: int = 3
    ) -> Dict[str, Any]:
        """
        Extract and cluster themes from feedback
        
        Args:
            date_range: Date range to analyze
            num_themes: Number of themes to extract
            min_frequency: Minimum frequency for a theme
            
        Returns:
            Identified themes with metadata
        """
        try:
            with self.db.get_session() as session:
                # Build query
                query = session.query(Feedback)
                
                if date_range:
                    start = datetime.fromisoformat(date_range.get('start'))
                    end = datetime.fromisoformat(date_range.get('end'))
                    query = query.filter(Feedback.created_at.between(start, end))
                
                feedback_items = query.all()
                
                if not feedback_items:
                    return {
                        "success": False,
                        "error": "No feedback items found in date range"
                    }
                
                # Extract themes
                themes = await self.theme_extractor.extract_themes(
                    [item.content for item in feedback_items],
                    num_themes=num_themes,
                    min_frequency=min_frequency
                )
                
                return {
                    "success": True,
                    "count": len(themes),
                    "themes": themes,
                    "metadata": {
                        "analyzed_items": len(feedback_items),
                        "date_range": date_range,
                        "num_themes_requested": num_themes,
                        "min_frequency": min_frequency
                    }
                }
        except Exception as e:
            logger.error(f"Error identifying themes: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def prioritize_issues(
        self,
        feedback_ids: List[str],
        factors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Rank feedback by business impact
        
        Args:
            feedback_ids: List of feedback IDs to prioritize
            factors: Factors to consider (customer_tier, sentiment, frequency, etc.)
            
        Returns:
            Prioritized feedback with impact scores
        """
        try:
            if factors is None:
                factors = ["customer_tier", "sentiment", "frequency", "recency"]
            
            with self.db.get_session() as session:
                feedback_items = session.query(Feedback).filter(
                    Feedback.id.in_(feedback_ids)
                ).all()
                
                if not feedback_items:
                    return {
                        "success": False,
                        "error": "No feedback items found"
                    }
                
                # Calculate impact scores
                prioritized = []
                for item in feedback_items:
                    score = self._calculate_impact_score(item, factors)
                    
                    prioritized.append({
                        "id": str(item.id),
                        "title": item.title,
                        "impact_score": score,
                        "customer_tier": item.customer_tier,
                        "sentiment": item.sentiment,
                        "created_at": item.created_at.isoformat(),
                        "priority_level": (
                            "critical" if score >= 80 else
                            "high" if score >= 60 else
                            "medium" if score >= 40 else
                            "low"
                        )
                    })
                
                # Sort by impact score
                prioritized.sort(key=lambda x: x["impact_score"], reverse=True)
                
                return {
                    "success": True,
                    "count": len(prioritized),
                    "results": prioritized,
                    "factors_used": factors
                }
        except Exception as e:
            logger.error(f"Error prioritizing issues: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_summary(
        self,
        date_range: Optional[Dict[str, str]] = None,
        format: str = "brief"
    ) -> Dict[str, Any]:
        """
        Generate executive summary of feedback
        
        Args:
            date_range: Date range to summarize
            format: Summary format (brief or detailed)
            
        Returns:
            Executive summary with key insights
        """
        try:
            with self.db.get_session() as session:
                # Build query
                query = session.query(Feedback)
                
                if date_range:
                    start = datetime.fromisoformat(date_range.get('start'))
                    end = datetime.fromisoformat(date_range.get('end'))
                    query = query.filter(Feedback.created_at.between(start, end))
                else:
                    # Default to last 30 days
                    start = datetime.utcnow() - timedelta(days=30)
                    query = query.filter(Feedback.created_at >= start)
                
                feedback_items = query.all()
                
                if not feedback_items:
                    return {
                        "success": False,
                        "error": "No feedback to summarize"
                    }
                
                # Generate summary
                summary = await self._generate_executive_summary(
                    feedback_items,
                    format
                )
                
                return {
                    "success": True,
                    "summary": summary
                }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_sentiment_trends(self, session, feedback_items):
        """Calculate sentiment trends over time"""
        # Group by week and calculate average sentiment
        weekly_sentiment = {}
        for item in feedback_items:
            week = item.created_at.strftime('%Y-W%W')
            if week not in weekly_sentiment:
                weekly_sentiment[week] = []
            weekly_sentiment[week].append(item.sentiment_score or 0)
        
        return {
            week: {
                "average": sum(scores) / len(scores),
                "count": len(scores)
            }
            for week, scores in weekly_sentiment.items()
        }
    
    def _calculate_impact_score(self, feedback: Feedback, factors: List[str]) -> float:
        """Calculate business impact score for feedback"""
        score = 0.0
        
        # Customer tier weight (enterprise = 40, business = 25, free = 10)
        if "customer_tier" in factors:
            tier_weights = {"enterprise": 40, "business": 25, "professional": 20, "free": 10}
            score += tier_weights.get(feedback.customer_tier, 10)
        
        # Sentiment weight (negative issues are higher priority)
        if "sentiment" in factors:
            if feedback.sentiment == "negative":
                score += 30
            elif feedback.sentiment == "neutral":
                score += 15
        
        # Recency weight (newer is higher priority)
        if "recency" in factors:
            days_old = (datetime.utcnow() - feedback.created_at).days
            recency_score = max(0, 20 - days_old)
            score += recency_score
        
        # Severity weight
        if hasattr(feedback, 'severity'):
            severity_weights = {"critical": 30, "high": 20, "medium": 10, "low": 5}
            score += severity_weights.get(feedback.severity, 5)
        
        return min(100, score)
    
    async def _generate_executive_summary(
        self,
        feedback_items: List[Feedback],
        format: str
    ) -> Dict[str, Any]:
        """Generate executive summary from feedback"""
        total = len(feedback_items)
        
        # Calculate sentiment breakdown
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        for item in feedback_items:
            sentiments[item.sentiment or "neutral"] += 1
        
        # Get top issues
        negative_items = [f for f in feedback_items if f.sentiment == "negative"]
        critical_count = len([f for f in feedback_items if hasattr(f, 'severity') and f.severity in ['critical', 'high']])
        
        summary = {
            "overview": {
                "total_feedback": total,
                "sentiment_breakdown": sentiments,
                "critical_issues": critical_count,
                "response_rate": f"{(sentiments['positive'] / total * 100):.1f}%" if total > 0 else "0%"
            },
            "key_insights": [
                f"Received {total} feedback items in the period",
                f"{sentiments['negative']} negative feedback items require attention",
                f"{critical_count} critical issues need immediate action"
            ]
        }
        
        if format == "detailed":
            # Add more detailed analysis
            summary["detailed_metrics"] = {
                "by_source": self._group_by_field(feedback_items, "source"),
                "by_category": self._group_by_field(feedback_items, "category"),
                "by_tier": self._group_by_field(feedback_items, "customer_tier")
            }
        
        return summary
    
    def _group_by_field(self, items: List[Feedback], field: str) -> Dict[str, int]:
        """Group feedback items by a field"""
        groups = {}
        for item in items:
            value = getattr(item, field, "unknown")
            groups[value] = groups.get(value, 0) + 1
        return groups
