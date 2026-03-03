"""
DATABASE SCHEMA & LOGGING LAYER
=================================
SQLAlchemy models and database management for logging
predictions, chat interactions, and playbook executions.

Supports:
- SQLite (development)
- PostgreSQL (production)
- Connection pooling
- Async database operations

Author: Role 3 Backend Developer
Date: 2026-02-26
"""

from sqlalchemy import (
    create_engine, Column, String, Float, DateTime,
    Integer, Boolean, JSON, ForeignKey, Enum as SQLEnum,
    Index, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from datetime import datetime
from typing import Optional, List
import enum
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# ============================================================================
# ENUMS
# ============================================================================

class RiskSegmentEnum(str, enum.Enum):
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"


class PlaybookStatusEnum(str, enum.Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SentimentEnum(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"


# ============================================================================
# DATABASE MODELS
# ============================================================================

class PredictionLogModel(Base):
    """
    Log table for churn predictions.
    
    Tracks:
    - User prediction
    - Model version
    - Feature inputs
    - Timestamp
    """
    __tablename__ = "prediction_logs"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(100), index=True, nullable=False)
    prediction_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # Prediction data
    churn_probability = Column(Float, nullable=False)
    risk_segment = Column(SQLEnum(RiskSegmentEnum), nullable=False)
    prediction_label = Column(Integer, nullable=False)  # 0 or 1
    confidence_score = Column(Float, nullable=False)
    
    # Model info
    model_version = Column(String(50), nullable=False)
    features_hash = Column(String(256), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    api_endpoint = Column(String(255), nullable=True)
    request_ip = Column(String(45), nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_prediction_user_date', 'user_id', 'created_at'),
        Index('ix_prediction_risk_segment', 'risk_segment'),
    )
    
    def __repr__(self):
        return f"<PredictionLog {self.prediction_id} - {self.user_id}>"


class ExplanationLogModel(Base):
    """
    Log table for explanation requests and responses.
    
    Tracks:
    - Explanation requests
    - Feature attributions
    - SHAP values
    - Response generation time
    """
    __tablename__ = "explanation_logs"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(100), index=True, nullable=False)
    prediction_id = Column(String(36), ForeignKey('prediction_logs.prediction_id'), nullable=False)
    
    # Explanation data
    explanation_depth = Column(String(50), nullable=False)
    explanation_method = Column(String(100), nullable=False)  # SHAP, LIME, etc.
    
    # Response data (stored as JSON)
    summary = Column(String(1000), nullable=True)
    key_drivers = Column(JSON, nullable=True)
    feature_attributions = Column(JSON, nullable=True)
    actionable_insights = Column(JSON, nullable=True)
    
    # Quality metrics
    explanation_stability_score = Column(Float, nullable=True)
    generation_time_ms = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_explanation_user_date', 'user_id', 'created_at'),
        Index('ix_explanation_prediction', 'prediction_id'),
    )
    
    def __repr__(self):
        return f"<ExplanationLog {self.id} - {self.user_id}>"


class PlaybookExecutionLogModel(Base):
    """
    Log table for playbook executions.
    
    Tracks:
    - Playbook recommendations
    - Executions
    - Actions queued/completed
    - User response
    """
    __tablename__ = "playbook_execution_logs"
    
    id = Column(String(36), primary_key=True)
    execution_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    prediction_id = Column(String(36), ForeignKey('prediction_logs.prediction_id'), nullable=False)
    
    # Playbook info
    playbook_id = Column(String(100), nullable=False)
    playbook_name = Column(String(255), nullable=True)
    
    # Execution tracking
    status = Column(SQLEnum(PlaybookStatusEnum), default=PlaybookStatusEnum.PENDING, nullable=False)
    initial_churn_probability = Column(Float, nullable=True)
    
    # Actions
    actions_queued = Column(JSON, nullable=True)  # List of action IDs
    actions_completed = Column(JSON, nullable=True)
    actions_failed = Column(JSON, nullable=True)
    
    # Business metrics
    estimated_impact = Column(JSON, nullable=True)  # Revenue, conversion lift, etc.
    actual_impact = Column(JSON, nullable=True)  # Updated after execution
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_playbook_user_date', 'user_id', 'created_at'),
        Index('ix_playbook_status', 'status'),
    )
    
    def __repr__(self):
        return f"<PlaybookExecutionLog {self.execution_id} - {self.playbook_id}>"


class ChatSessionLogModel(Base):
    """
    Log table for chatbot sessions.
    
    Tracks:
    - Chat sessions
    - Messages (user & assistant)
    - Intents
    - Outcomes
    """
    __tablename__ = "chat_session_logs"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    
    # Session metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Conversation tracking
    turn_count = Column(Integer, default=0)
    intent_sequence = Column(JSON, nullable=True)  # List of intents in order
    sentiment_progression = Column(JSON, nullable=True)  # Sentiment history
    
    # Messages (full transcript)
    messages = Column(JSON, nullable=True)
    
    # Outcomes
    offers_presented = Column(JSON, nullable=True)
    offers_accepted = Column(JSON, nullable=True)
    playbook_recommended = Column(String(100), nullable=True)
    playbook_accepted = Column(Boolean, default=False)
    
    # Quality metrics
    user_satisfaction = Column(Float, nullable=True)  # 0-5 rating if provided
    
    # Indexes
    __table_args__ = (
        Index('ix_chat_user_date', 'user_id', 'created_at'),
        Index('ix_chat_playbook', 'playbook_recommended'),
    )
    
    def __repr__(self):
        return f"<ChatSessionLog {self.session_id} - {self.user_id}>"


class ChatMessageLogModel(Base):
    """
    Detailed chat message log.
    Separate table from ChatSessionLog for query efficiency.
    """
    __tablename__ = "chat_message_logs"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey('chat_session_logs.session_id'), nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(String(5000), nullable=False)
    
    # Metadata
    turn_number = Column(Integer, nullable=False)
    intent = Column(String(100), nullable=True)
    sentiment = Column(SQLEnum(SentimentEnum), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_message_session', 'session_id'),
        Index('ix_message_user', 'user_id'),
    )
    
    def __repr__(self):
        return f"<ChatMessageLog {self.id}>"


class APICallLogModel(Base):
    """
    General API call logging for monitoring and analytics.
    """
    __tablename__ = "api_call_logs"
    
    id = Column(String(36), primary_key=True)
    
    # Request info
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    request_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Response info
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    
    # User info
    user_id = Column(String(100), nullable=True)
    
    # Error tracking
    error_message = Column(String(1000), nullable=True)
    error_type = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_api_endpoint_date', 'endpoint', 'created_at'),
        Index('ix_api_status', 'status_code'),
    )
    
    def __repr__(self):
        return f"<APICallLog {self.id} - {self.endpoint}>"


# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

class DatabaseManager:
    """
    Manages database connections and sessions.
    Supports both sync and async operations.
    """
    
    def __init__(self, database_url: str = None, echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy connection string
                          Default: sqlite:///chatbot.db
            echo: Enable SQL logging
        """
        if database_url is None:
            # Use SQLite for development
            database_url = "sqlite:///./chatbot.db"
        
        self.database_url = database_url
        self.echo = echo
        
        # Create engine
        if "sqlite" in database_url:
            # SQLite with in-memory or file
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=echo
            )
        else:
            # PostgreSQL or other
            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=20,
                max_overflow=40
            )
        
        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Async engine (optional)
        self.async_engine = None
        self.AsyncSessionLocal = None
    
    def create_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("✓ Database tables created")
    
    def drop_tables(self):
        """Drop all database tables (WARNING: Data loss!)"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("✓ Database tables dropped")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def init_async(self, async_database_url: str = None):
        """Initialize async support"""
        if async_database_url is None:
            # Convert sync URL to async
            if "postgresql" in self.database_url:
                async_database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            else:
                logger.warning("Async not fully supported for SQLite")
                return
        
        self.async_engine = create_async_engine(
            async_database_url,
            echo=self.echo,
            pool_size=20,
            max_overflow=40
        )
        
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_async_session(self) -> AsyncSession:
        """Get a new async database session"""
        if self.AsyncSessionLocal is None:
            raise ValueError("Async not initialized. Call init_async() first.")
        return self.AsyncSessionLocal()


# ============================================================================
# REPOSITORY PATTERN - DATA ACCESS LAYER
# ============================================================================

class PredictionRepository:
    """Data access layer for predictions"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, prediction_log: PredictionLogModel) -> PredictionLogModel:
        """Create prediction log"""
        self.session.add(prediction_log)
        self.session.commit()
        self.session.refresh(prediction_log)
        return prediction_log
    
    def get_by_id(self, prediction_id: str) -> Optional[PredictionLogModel]:
        """Get prediction by ID"""
        return self.session.query(PredictionLogModel).filter(
            PredictionLogModel.prediction_id == prediction_id
        ).first()
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[PredictionLogModel]:
        """Get recent predictions for user"""
        return self.session.query(PredictionLogModel).filter(
            PredictionLogModel.user_id == user_id
        ).order_by(PredictionLogModel.created_at.desc()).limit(limit).all()
    
    def get_high_risk_users(self, threshold: float = 0.67) -> List[PredictionLogModel]:
        """Get high-risk users"""
        return self.session.query(PredictionLogModel).filter(
            PredictionLogModel.churn_probability >= threshold
        ).order_by(PredictionLogModel.churn_probability.desc()).all()


class ChatSessionRepository:
    """Data access layer for chat sessions"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, chat_session: ChatSessionLogModel) -> ChatSessionLogModel:
        """Create chat session log"""
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        return chat_session
    
    def get_by_id(self, session_id: str) -> Optional[ChatSessionLogModel]:
        """Get chat session by ID"""
        return self.session.query(ChatSessionLogModel).filter(
            ChatSessionLogModel.session_id == session_id
        ).first()
    
    def get_by_user(self, user_id: str, limit: int = 50) -> List[ChatSessionLogModel]:
        """Get user's chat sessions"""
        return self.session.query(ChatSessionLogModel).filter(
            ChatSessionLogModel.user_id == user_id
        ).order_by(ChatSessionLogModel.created_at.desc()).limit(limit).all()
    
    def add_message(self, message_log: ChatMessageLogModel) -> ChatMessageLogModel:
        """Add message to session"""
        self.session.add(message_log)
        self.session.commit()
        self.session.refresh(message_log)
        return message_log


class PlaybookRepository:
    """Data access layer for playbooks"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, execution: PlaybookExecutionLogModel) -> PlaybookExecutionLogModel:
        """Create playbook execution log"""
        self.session.add(execution)
        self.session.commit()
        self.session.refresh(execution)
        return execution
    
    def update_status(self, execution_id: str, status: PlaybookStatusEnum):
        """Update execution status"""
        execution = self.session.query(PlaybookExecutionLogModel).filter(
            PlaybookExecutionLogModel.execution_id == execution_id
        ).first()
        if execution:
            execution.status = status
            if status == PlaybookStatusEnum.COMPLETED:
                execution.completed_at = datetime.utcnow()
            self.session.commit()
        return execution


# ============================================================================
# INITIALIZATION
# ============================================================================

# Default database manager instance
db_manager = DatabaseManager()


if __name__ == "__main__":
    # Initialize database
    db_manager.create_tables()
    logger.info("✓ Database initialized successfully")
    
    # Test creating records
    session = db_manager.get_session()
    
    # Test prediction log
    pred_log = PredictionLogModel(
        id="test_id_1",
        user_id="user_001",
        prediction_id="pred_001",
        churn_probability=0.75,
        risk_segment=RiskSegmentEnum.HIGH_RISK,
        prediction_label=1,
        confidence_score=0.85,
        model_version="1.0"
    )
    session.add(pred_log)
    session.commit()
    logger.info("✓ Test prediction logged")
    
    session.close()
