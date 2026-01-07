"""
MCP Resources for Customer Feedback

Implements the resource handlers for the MCP protocol:
- feedback://recent - Recent feedback (last 7 days)
- feedback://critical - Critical/urgent feedback
- feedback://trends - Aggregated trends and themes
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ..storage.models import Feedback, Theme

logger = logging.getLogger(__name__)


class FeedbackResources:
    """Handles MCP resource endpoints for feedback data"""
    
    def __init__(self, db, settings):
        self.db = db
        self.settings = settings
    
    async def get_recent_feedback(self, days: int = 7) -> Dict[str, Any]:
        """
        Get recent feedback from the last N days
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            Dictionary containing recent feedback items with metadata
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self.db.get_session() as session:
                feedback_items = session.query(Feedback).filter(
                    Feedback.created_at >= cutoff_date
                ).order_by(
                    desc(Feedback.created_at)
                ).limit(100).all()
                
                # Calculate statistics
                total_count = session.query(func.count(Feedback.id)).filter(
                    Feedback.created_at >= cutoff_date
                ).scalar()
                
                sentiment_breakdown = session.query(
                    Feedback.sentiment,
                    func.count(Feedback.id)
                ).filter(
                    Feedback.created_at >= cutoff_date
                ).group_by(
                    Feedback.sentiment
                ).all()
                
                return {
                    "uri": "feedback://recent",
                    "mimeType": "application/json",
                    "text": self._format_feedback_list(feedback_items),
                    "metadata": {
                        "total_count": total_count,
                        "days": days,
                        "date_range": {
                            "start": cutoff_date.isoformat(),
                            "end": datetime.utcnow().isoformat()
                        },
                        "sentiment_breakdown": {
                            sentiment: count 
                            for sentiment, count in sentiment_breakdown
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Error fetching recent feedback: {e}")
            raise
    
    async def get_critical_feedback(self) -> Dict[str, Any]:
        """
        Get critical/urgent feedback requiring immediate attention
        
        Returns:
            Dictionary containing critical feedback items
        """
        try:
            with self.db.get_session() as session:
                # Fetch feedback marked as high priority or negative sentiment
                critical_feedback = session.query(Feedback).filter(
                    and_(
                        Feedback.severity.in_(['high', 'critical']),
                        Feedback.status != 'resolved'
                    )
                ).order_by(
                    desc(Feedback.impact_score),
                    desc(Feedback.created_at)
                ).limit(50).all()
                
                # Get urgency statistics
                total_critical = session.query(func.count(Feedback.id)).filter(
                    and_(
                        Feedback.severity.in_(['high', 'critical']),
                        Feedback.status != 'resolved'
                    )
                ).scalar()
                
                return {
                    "uri": "feedback://critical",
                    "mimeType": "application/json",
                    "text": self._format_feedback_list(critical_feedback),
                    "metadata": {
                        "total_count": total_critical,
                        "severity_levels": {
                            "critical": len([f for f in critical_feedback if f.severity == 'critical']),
                            "high": len([f for f in critical_feedback if f.severity == 'high'])
                        },
                        "requires_immediate_action": total_critical
                    }
                }
        except Exception as e:
            logger.error(f"Error fetching critical feedback: {e}")
            raise
    
    async def get_feedback_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregated trends and themes from feedback
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dictionary containing trends and theme analysis
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self.db.get_session() as session:
                # Get top themes
                themes = session.query(
                    Theme.name,
                    Theme.frequency,
                    Theme.sentiment_score
                ).filter(
                    Theme.last_seen >= cutoff_date
                ).order_by(
                    desc(Theme.frequency)
                ).limit(20).all()
                
                # Get sentiment trends over time
                sentiment_by_week = session.query(
                    func.date_trunc('week', Feedback.created_at).label('week'),
                    Feedback.sentiment,
                    func.count(Feedback.id).label('count'),
                    func.avg(Feedback.sentiment_score).label('avg_score')
                ).filter(
                    Feedback.created_at >= cutoff_date
                ).group_by(
                    'week',
                    Feedback.sentiment
                ).order_by('week').all()
                
                # Get feedback volume by source
                by_source = session.query(
                    Feedback.source,
                    func.count(Feedback.id).label('count')
                ).filter(
                    Feedback.created_at >= cutoff_date
                ).group_by(
                    Feedback.source
                ).all()
                
                return {
                    "uri": "feedback://trends",
                    "mimeType": "application/json",
                    "text": self._format_trends(themes, sentiment_by_week),
                    "metadata": {
                        "date_range": {
                            "start": cutoff_date.isoformat(),
                            "end": datetime.utcnow().isoformat()
                        },
                        "top_themes": [
                            {
                                "name": theme.name,
                                "frequency": theme.frequency,
                                "sentiment": theme.sentiment_score
                            }
                            for theme in themes
                        ],
                        "sentiment_trends": [
                            {
                                "week": str(week),
                                "sentiment": sentiment,
                                "count": count,
                                "avg_score": float(avg_score) if avg_score else 0
                            }
                            for week, sentiment, count, avg_score in sentiment_by_week
                        ],
                        "by_source": {
                            source: count for source, count in by_source
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Error fetching feedback trends: {e}")
            raise
    
    def _format_feedback_list(self, feedback_items: List[Feedback]) -> str:
        """Format feedback items as readable text"""
        if not feedback_items:
            return "No feedback items found."
        
        lines = [f"Found {len(feedback_items)} feedback items:\n"]
        for item in feedback_items:
            lines.append(
                f"- [{item.source}] {item.title or 'Untitled'}\n"
                f"  Sentiment: {item.sentiment} ({item.sentiment_score:.2f})\n"
                f"  Customer: {item.customer_id} (Tier: {item.customer_tier})\n"
                f"  Date: {item.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"  Preview: {item.content[:100]}...\n"
            )
        
        return "\n".join(lines)
    
    def _format_trends(self, themes: List, sentiment_trends: List) -> str:
        """Format trends data as readable text"""
        lines = ["# Feedback Trends\n\n## Top Themes:\n"]
        
        for i, theme in enumerate(themes[:10], 1):
            lines.append(
                f"{i}. {theme.name} - "
                f"Frequency: {theme.frequency}, "
                f"Sentiment: {theme.sentiment_score:.2f}\n"
            )
        
        lines.append("\n## Sentiment Overview:\n")
        if sentiment_trends:
            lines.append("Recent sentiment patterns show evolving customer perception.\n")
        
        return "\n".join(lines)
