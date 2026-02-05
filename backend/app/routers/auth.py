"""
Authentication router for Customer Onboarding Agent
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, User
from app.schemas import (
    UserCreate, UserLogin, UserLoginResponse, UserResponse, 
    ErrorResponse
)
from app.auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_active_user, get_user_by_email, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with role assignment"""
    
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role,
        is_active=user_data.is_active,
        created_at=datetime.utcnow()
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return UserResponse.model_validate(db_user)


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout_user():
    """Logout user and invalidate token"""
    # Note: JWT tokens are stateless, so logout is handled client-side
    # In production, you might want to implement token blacklisting
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user profile"""
    return UserResponse.model_validate(current_user)