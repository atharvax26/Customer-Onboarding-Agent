"""
Pydantic schemas for Customer Onboarding Agent
Request/Response validation models
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    DEVELOPER = "Developer"
    BUSINESS_USER = "Business_User"
    ADMIN = "Admin"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# Base schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# User schemas
class UserBase(BaseSchema):
    email: EmailStr
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class UserLoginResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Document schemas
class DocumentBase(BaseSchema):
    filename: str
    file_size: Optional[int] = None


class DocumentCreate(DocumentBase):
    original_content: str
    content_hash: str


class DocumentUpdate(BaseSchema):
    processed_summary: Optional[Dict[str, Any]] = None
    step_tasks: Optional[List[str]] = None


class DocumentResponse(DocumentBase):
    id: int
    processed_summary: Optional[Dict[str, Any]] = None
    step_tasks: Optional[List[str]] = None
    uploaded_at: datetime
    content_hash: str


class ProcessedDocumentResponse(BaseSchema):
    id: int
    filename: str
    summary: str
    tasks: List[str]
    processing_time: float


# OnboardingSession schemas
class OnboardingSessionBase(BaseSchema):
    current_step: int = 1
    total_steps: int
    session_metadata: Optional[Dict[str, Any]] = None


class OnboardingSessionCreate(OnboardingSessionBase):
    user_id: int
    document_id: int


class OnboardingSessionUpdate(BaseSchema):
    status: Optional[SessionStatus] = None
    current_step: Optional[int] = None
    completed_at: Optional[datetime] = None
    session_metadata: Optional[Dict[str, Any]] = None


class OnboardingSessionResponse(OnboardingSessionBase):
    id: int
    user_id: int
    document_id: int
    status: SessionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None


# StepCompletion schemas
class StepCompletionBase(BaseSchema):
    step_number: int
    time_spent_seconds: Optional[int] = None
    step_data: Optional[Dict[str, Any]] = None


class StepCompletionCreate(StepCompletionBase):
    session_id: int


class StepCompletionUpdate(BaseSchema):
    completed_at: Optional[datetime] = None
    time_spent_seconds: Optional[int] = None
    step_data: Optional[Dict[str, Any]] = None


class StepCompletionResponse(StepCompletionBase):
    id: int
    session_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None


# EngagementLog schemas
class EngagementLogBase(BaseSchema):
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    engagement_score: Optional[float] = Field(None, ge=0, le=100, description="Engagement score between 0-100")


class EngagementLogCreate(EngagementLogBase):
    user_id: int
    session_id: Optional[int] = None


class EngagementLogResponse(EngagementLogBase):
    id: int
    user_id: int
    session_id: Optional[int] = None
    timestamp: datetime


# InterventionLog schemas
class InterventionLogBase(BaseSchema):
    intervention_type: str
    message_content: Optional[str] = None
    was_helpful: Optional[bool] = None


class InterventionLogCreate(InterventionLogBase):
    user_id: int
    session_id: Optional[int] = None


class InterventionLogResponse(InterventionLogBase):
    id: int
    user_id: int
    session_id: Optional[int] = None
    triggered_at: datetime


# Onboarding flow schemas
class OnboardingStepResponse(BaseSchema):
    step_number: int
    total_steps: int
    title: str
    content: str
    tasks: List[str]
    estimated_time: int


class OnboardingProgressResponse(BaseSchema):
    session_id: int
    current_step: int
    total_steps: int
    completion_percentage: float
    steps_completed: List[StepCompletionResponse]


# Analytics schemas
class ScorePoint(BaseSchema):
    timestamp: datetime
    score: float = Field(..., ge=0, le=100, description="Engagement score between 0-100")


class EngagementScoreResponse(BaseSchema):
    current_score: float = Field(..., ge=0, le=100, description="Engagement score between 0-100")
    score_history: List[ScorePoint]
    last_updated: datetime


class ActivationMetrics(BaseSchema):
    total_users: int
    activated_users: int
    activation_rate: float
    role_breakdown: Dict[str, Dict[str, int]]


class DropoffData(BaseSchema):
    step_number: int
    step_title: str
    started_count: int
    completed_count: int
    completion_rate: float
    average_time_spent: Optional[float] = None


class DropoffAnalysisResponse(BaseSchema):
    overall_completion_rate: float
    steps: List[DropoffData]


class TrendDataPoint(BaseSchema):
    date: datetime
    value: float
    count: int


class TrendData(BaseSchema):
    metric_name: str
    data_points: List[TrendDataPoint]
    trend_direction: str  # "up", "down", "stable"


class AnalyticsFilters(BaseSchema):
    role: Optional[UserRole] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None


class DashboardData(BaseSchema):
    activation_metrics: ActivationMetrics
    recent_dropoff_analysis: DropoffAnalysisResponse
    engagement_trends: List[TrendData]
    total_sessions: int
    active_sessions: int
    recent_interventions: int


# File upload schemas
class DocumentUploadResponse(BaseSchema):
    message: str
    document_id: int
    processing_status: str


# Error schemas
class ErrorResponse(BaseSchema):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Interaction tracking schemas
class InteractionEvent(BaseSchema):
    event_type: str = Field(..., description="Type of interaction (click, scroll, focus, etc.)")
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    page_url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    additional_data: Optional[Dict[str, Any]] = None


class InteractionTrackingResponse(BaseSchema):
    success: bool
    message: str


# Help message schemas
class HelpMessage(BaseSchema):
    message_id: str
    content: str
    message_type: str
    context: Dict[str, Any]
    dismissible: bool = True


class HelpMessageResponse(BaseSchema):
    help_message: HelpMessage
    triggered_at: datetime