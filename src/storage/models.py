"""
Database Models for Customer Feedback

SQLAlchemy ORM models for storing and querying feedback data
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Feedback(Base):
    """Main feedback model"""
    
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Source information
    source = Column(String(50), nullable=False, index=True)  # zendesk, intercom, surveymonkey
    source_id = Column(String(255), nullable=False)  # ID from source system
    
    # Content
    title = Column(String(500))
    content = Column(Text, nullable=False)
    category = Column(String(100), index=True)
    
    # Customer information
    customer_id = Column(String(255), nullable=False, index=True)
    customer_email = Column(String(255))
    customer_name = Column(String(255))
    customer_tier = Column(String(50), index=True)  # enterprise, business, professional, free
    
    # Analysis results
    sentiment = Column(String(20), index=True)  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1.0 to 1.0
    impact_score = Column(Float, default=0.0, index=True)  # 0-100
    severity = Column(String(20))  # critical, high, medium, low
    
    # Status
    status = Column(String(50), default="open", index=True)  # open, in_progress, resolved, closed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    themes = relationship("FeedbackTheme", back_populates="feedback")
    
    # Indexes
    __table_args__ = (
        Index('idx_feedback_search', 'customer_tier', 'sentiment', 'created_at'),
        Index('idx_feedback_critical', 'severity', 'status', 'impact_score'),
    )
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, source={self.source}, sentiment={self.sentiment})>"


class Theme(Base):
    """Extracted themes from feedback"""
    
    __tablename__ = "themes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Statistics
    frequency = Column(Integer, default=0)
    sentiment_score = Column(Float, default=0.0)
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    feedback_associations = relationship("FeedbackTheme", back_populates="theme")
    
    def __repr__(self):
        return f"<Theme(id={self.id}, name={self.name}, frequency={self.frequency})>"


class FeedbackTheme(Base):
    """Many-to-many relationship between feedback and themes"""
    
    __tablename__ = "feedback_themes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("feedback.id"), nullable=False, index=True)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("themes.id"), nullable=False, index=True)
    
    # Relevance score for this theme to this feedback
    relevance_score = Column(Float, default=1.0)
    
    # Relationships
    feedback = relationship("Feedback", back_populates="themes")
    theme = relationship("Theme", back_populates="feedback_associations")
    
    __table_args__ = (
        Index('idx_feedback_theme', 'feedback_id', 'theme_id'),
    )
    
    def __repr__(self):
        return f"<FeedbackTheme(feedback_id={self.feedback_id}, theme_id={self.theme_id})>"


class DataSource(Base):
    """Configuration for data sources"""
    
    __tablename__ = "data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # zendesk, intercom, surveymonkey
    
    # Connection details (encrypted in production)
    api_endpoint = Column(String(500))
    credentials = Column(Text)  # JSON encrypted credentials
    
    # Sync status
    last_sync = Column(DateTime)
    sync_status = Column(String(50), default="active")  # active, paused, error
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DataSource(id={self.id}, name={self.name}, type={self.type})>"
