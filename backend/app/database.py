"""
Database configuration and models for Customer Onboarding Agent
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from datetime import datetime
from enum import Enum
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./customer_onboarding.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# Enums
class UserRole(str, Enum):
    DEVELOPER = "Developer"
    BUSINESS_USER = "Business_User"
    ADMIN = "Admin"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    onboarding_sessions = relationship("OnboardingSession", back_populates="user")
    engagement_logs = relationship("EngagementLog", back_populates="user")
    intervention_logs = relationship("InterventionLog", back_populates="user")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_content = Column(Text, nullable=False)
    processed_summary = Column(JSON)
    step_tasks = Column(JSON)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    content_hash = Column(String, index=True)  # Removed unique constraint to allow same doc for different users
    
    # Relationships
    user = relationship("User", back_populates="documents")
    onboarding_sessions = relationship("OnboardingSession", back_populates="document")


class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    session_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="onboarding_sessions")
    document = relationship("Document", back_populates="onboarding_sessions")
    step_completions = relationship("StepCompletion", back_populates="session")


class StepCompletion(Base):
    __tablename__ = "step_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("onboarding_sessions.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    time_spent_seconds = Column(Integer)
    step_data = Column(JSON)
    
    # Relationships
    session = relationship("OnboardingSession", back_populates="step_completions")


class EngagementLog(Base):
    __tablename__ = "engagement_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("onboarding_sessions.id"))
    event_type = Column(String, nullable=False)
    event_data = Column(JSON)
    engagement_score = Column(Float)  # 0-100
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="engagement_logs")


class InterventionLog(Base):
    __tablename__ = "intervention_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("onboarding_sessions.id"))
    intervention_type = Column(String, nullable=False)
    message_content = Column(Text)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    was_helpful = Column(Boolean)
    
    # Relationships
    user = relationship("User", back_populates="intervention_logs")


# Database session dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)