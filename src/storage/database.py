"""
Database Operations

Handles database connections, sessions, and operations
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .models import Base

logger = logging.getLogger(__name__)


class Database:
    """Database connection and session management"""
    
    def __init__(self, database_url: str, pool_size: int = 20, max_overflow: int = 10):
        """
        Initialize database connection
        
        Args:
            database_url: PostgreSQL connection string
            pool_size: Size of the connection pool
            max_overflow: Maximum overflow connections
        """
        self.database_url = database_url
        
        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("Database initialized successfully")
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup
        
        Usage:
            with db.get_session() as session:
                # Use session
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """
        Check if database connection is healthy
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close(self):
        """Close database connections"""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
            raise
