"""
Authentication utilities for Customer Onboarding Agent
Handles password hashing, JWT token generation, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Union, List
from functools import wraps
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.database import get_db, User, UserRole
from app.schemas import UserResponse

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# JWT token security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt"""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email from database"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID from database"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Role-based access control
def require_roles(allowed_roles: List[UserRole]):
    """
    Decorator factory for role-based access control
    Usage: @require_roles([UserRole.ADMIN, UserRole.DEVELOPER])
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_developer(current_user: User = Depends(get_current_active_user)) -> User:
    """Require developer role"""
    if current_user.role != UserRole.DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer access required"
        )
    return current_user


def require_business_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Require business user role"""
    if current_user.role != UserRole.BUSINESS_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business user access required"
        )
    return current_user


def can_access_user_data(target_user_id: int, current_user: User) -> bool:
    """
    Check if current user can access target user's data
    Admins can access all data, users can only access their own data
    """
    if current_user.role == UserRole.ADMIN:
        return True
    return current_user.id == target_user_id


def filter_content_by_role(content: dict, user_role: UserRole) -> dict:
    """
    Filter content based on user role
    Different roles see different content in onboarding flows
    """
    filtered_content = content.copy()
    
    if user_role == UserRole.DEVELOPER:
        # Developers see API-focused content
        filtered_content["focus"] = "api"
        filtered_content["show_technical_details"] = True
        filtered_content["show_code_examples"] = True
        
    elif user_role == UserRole.BUSINESS_USER:
        # Business users see workflow-focused content
        filtered_content["focus"] = "workflow"
        filtered_content["show_technical_details"] = False
        filtered_content["show_business_value"] = True
        
    elif user_role == UserRole.ADMIN:
        # Admins see administrative content
        filtered_content["focus"] = "administration"
        filtered_content["show_system_config"] = True
        filtered_content["show_user_management"] = True
    
    return filtered_content


async def check_resource_access(
    resource_user_id: int,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Check if current user can access a resource belonging to another user
    Used as a dependency for endpoints that access user-specific resources
    """
    if not can_access_user_data(resource_user_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own resources."
        )
    return current_user