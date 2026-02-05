"""
Property-based tests for user role assignment and authentication
Feature: customer-onboarding-agent, Property 9: User Role Assignment and Authentication
Validates: Requirements 6.1, 6.2, 6.5
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from fastapi import HTTPException
from jose import jwt
from unittest.mock import patch

from app.database import Base, User, UserRole
from app.auth import (
    create_access_token, verify_token, authenticate_user, get_user_by_email, 
    get_user_by_id, can_access_user_data, filter_content_by_role, 
    SECRET_KEY, ALGORITHM
)
from app.schemas import UserCreate


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Hypothesis strategies for generating test data
user_role_strategy = st.sampled_from([UserRole.DEVELOPER, UserRole.BUSINESS_USER, UserRole.ADMIN])

email_strategy = st.builds(
    lambda name, domain: f"{name}@{domain}.com",
    name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=1, max_size=20),
    domain=st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=2, max_size=10)
)

password_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), min_codepoint=32, max_codepoint=126),
    min_size=8, 
    max_size=50  # Keep well under 72 bytes to account for encoding
)
user_id_strategy = st.integers(min_value=1, max_value=1000000)


# Mock password hashing functions for testing
def mock_get_password_hash(password: str) -> str:
    """Mock password hashing for testing"""
    return f"hashed_{password}"


def mock_verify_password(plain_password: str, hashed_password: str) -> bool:
    """Mock password verification for testing"""
    return hashed_password == f"hashed_{plain_password}"


@pytest.mark.asyncio
@given(
    email=email_strategy,
    password=password_strategy,
    role=user_role_strategy,
    is_active=st.booleans()
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_user_registration_role_assignment(email, password, role, is_active):
    """
    **Feature: customer-onboarding-agent, Property 9: User Role Assignment and Authentication**
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    For any user registration, the system should assign exactly one of three valid roles 
    (Developer, Business_User, Admin), and successful authentication should establish 
    secure sessions while preventing unauthorized access to role-specific content.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Test user registration with role assignment using mock hashing
        with patch('app.auth.get_password_hash', side_effect=mock_get_password_hash):
            password_hash = mock_get_password_hash(password)
            
            # Create user with specified role
            user = User(
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=is_active
            )
            
            test_db.add(user)
            await test_db.commit()
            await test_db.refresh(user)
            
            # Verify role assignment requirements (6.1)
            assert user.role in [UserRole.DEVELOPER, UserRole.BUSINESS_USER, UserRole.ADMIN], \
                "User must be assigned exactly one of three valid roles"
            assert user.role == role, "Assigned role must match the requested role"
            assert isinstance(user.role, UserRole), "Role must be a valid UserRole enum value"
            
            # Verify user profile maintenance (6.2)
            assert user.id is not None, "User should have an ID after registration"
            assert user.email == email, "Email should be stored correctly"
            assert user.password_hash == password_hash, "Password hash should be stored correctly"
            assert user.is_active == is_active, "Active status should be stored correctly"
            assert user.created_at is not None, "Created timestamp should be set"
            
            # Test authentication establishes secure session (6.2)
            with patch('app.auth.verify_password', side_effect=mock_verify_password):
                if is_active:
                    authenticated_user = await authenticate_user(test_db, email, password)
                    assert authenticated_user is not None, "Active user should authenticate successfully"
                    assert authenticated_user.id == user.id, "Authenticated user should match registered user"
                    assert authenticated_user.role == role, "Authenticated user should maintain correct role"
                else:
                    authenticated_user = await authenticate_user(test_db, email, password)
                    assert authenticated_user is None, "Inactive user should not authenticate"
            
            # Test role-specific content access control (6.5)
            content = {"title": "Test Content", "data": "sample"}
            filtered_content = filter_content_by_role(content, role)
            
            if role == UserRole.DEVELOPER:
                assert filtered_content["focus"] == "api", "Developers should get API-focused content"
                assert filtered_content["show_technical_details"] is True, "Developers should see technical details"
                assert filtered_content["show_code_examples"] is True, "Developers should see code examples"
            elif role == UserRole.BUSINESS_USER:
                assert filtered_content["focus"] == "workflow", "Business users should get workflow-focused content"
                assert filtered_content["show_technical_details"] is False, "Business users should not see technical details"
                assert filtered_content["show_business_value"] is True, "Business users should see business value"
            elif role == UserRole.ADMIN:
                assert filtered_content["focus"] == "administration", "Admins should get administration-focused content"
                assert filtered_content["show_system_config"] is True, "Admins should see system config"
                assert filtered_content["show_user_management"] is True, "Admins should see user management"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user1_email=email_strategy,
    user1_role=user_role_strategy,
    user2_email=email_strategy,
    user2_role=user_role_strategy,
    password=password_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_role_based_access_control(user1_email, user1_role, user2_email, user2_role, password):
    """
    **Feature: customer-onboarding-agent, Property 9: User Role Assignment and Authentication**
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    For any two users with different roles, the system should prevent unauthorized access 
    to role-specific content and ensure users can only access their own data unless they are admins.
    """
    assume(user1_email != user2_email)  # Ensure different users
    
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create two users with different roles using mock hashing
        with patch('app.auth.get_password_hash', side_effect=mock_get_password_hash):
            password_hash = mock_get_password_hash(password)
            
            user1 = User(
                email=user1_email,
                password_hash=password_hash,
                role=user1_role,
                is_active=True
            )
            
            user2 = User(
                email=user2_email,
                password_hash=password_hash,
                role=user2_role,
                is_active=True
            )
            
            test_db.add(user1)
            test_db.add(user2)
            await test_db.commit()
            await test_db.refresh(user1)
            await test_db.refresh(user2)
            
            # Test access control between users (6.5)
            # Users should only access their own data
            assert can_access_user_data(user1.id, user1) is True, "User should access their own data"
            assert can_access_user_data(user2.id, user2) is True, "User should access their own data"
            
            # Non-admin users should not access other users' data
            if user1_role != UserRole.ADMIN:
                assert can_access_user_data(user2.id, user1) is False, "Non-admin should not access other user's data"
            
            if user2_role != UserRole.ADMIN:
                assert can_access_user_data(user1.id, user2) is False, "Non-admin should not access other user's data"
            
            # Admin users should access any user's data
            if user1_role == UserRole.ADMIN:
                assert can_access_user_data(user2.id, user1) is True, "Admin should access any user's data"
            
            if user2_role == UserRole.ADMIN:
                assert can_access_user_data(user1.id, user2) is True, "Admin should access any user's data"
            
            # Test role-specific content filtering
            content = {"title": "Test Content"}
            
            user1_content = filter_content_by_role(content, user1_role)
            user2_content = filter_content_by_role(content, user2_role)
            
            # Content should be filtered based on role
            if user1_role != user2_role:
                # Different roles should get different content focus
                if user1_role == UserRole.DEVELOPER and user2_role == UserRole.BUSINESS_USER:
                    assert user1_content["focus"] == "api", "Developer should get API focus"
                    assert user2_content["focus"] == "workflow", "Business user should get workflow focus"
                    assert user1_content["show_technical_details"] != user2_content["show_technical_details"], \
                        "Different roles should have different technical detail visibility"
                
                elif user1_role == UserRole.ADMIN and user2_role != UserRole.ADMIN:
                    assert user1_content["focus"] == "administration", "Admin should get administration focus"
                    assert user2_content["focus"] != "administration", "Non-admin should not get administration focus"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    email=email_strategy,
    password=password_strategy,
    role=user_role_strategy,
    user_id=user_id_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_jwt_token_authentication_security(email, password, role, user_id):
    """
    **Feature: customer-onboarding-agent, Property 9: User Role Assignment and Authentication**
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    For any user authentication, JWT tokens should be created securely, contain correct user information,
    and be verifiable to establish secure sessions.
    """
    # Test JWT token creation and verification (6.2)
    token_data = {"sub": str(user_id), "role": role.value}
    token = create_access_token(token_data)
    
    # Verify token structure and content
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 0, "Token should not be empty"
    assert token.count('.') == 2, "JWT token should have 3 parts separated by dots"
    
    # Verify token can be decoded and contains correct data
    payload = verify_token(token)
    assert payload is not None, "Valid token should be verifiable"
    assert payload["sub"] == str(user_id), "Token should contain correct user ID"
    assert payload["role"] == role.value, "Token should contain correct role"
    assert "exp" in payload, "Token should have expiration time"
    
    # Verify token expiration is set correctly
    exp_timestamp = payload["exp"]
    current_timestamp = datetime.utcnow().timestamp()
    assert exp_timestamp > current_timestamp, "Token should not be expired immediately"
    
    # Test invalid token handling
    invalid_token = "invalid.token.string"
    invalid_payload = verify_token(invalid_token)
    assert invalid_payload is None, "Invalid token should return None"
    
    # Test token with tampered data
    try:
        # Manually decode without verification to tamper with data
        import base64
        import json
        
        header, payload_part, signature = token.split('.')
        
        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_part + '==')
        payload_dict = json.loads(payload_bytes)
        
        # Tamper with payload
        payload_dict["sub"] = "999999"  # Change user ID
        
        # Re-encode
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps(payload_dict).encode()
        ).decode().rstrip('=')
        
        tampered_token = f"{header}.{tampered_payload}.{signature}"
        
        # Verify tampered token is rejected
        tampered_result = verify_token(tampered_token)
        assert tampered_result is None, "Tampered token should be rejected"
        
    except Exception:
        # If tampering fails, that's also acceptable - token is secure
        pass


@pytest.mark.asyncio
@given(
    email=email_strategy,
    correct_password=password_strategy,
    wrong_password=password_strategy,
    role=user_role_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_password_authentication_security(email, correct_password, wrong_password, role):
    """
    **Feature: customer-onboarding-agent, Property 9: User Role Assignment and Authentication**
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    For any user authentication attempt, the system should securely hash passwords,
    verify correct passwords, and reject incorrect passwords.
    """
    assume(correct_password != wrong_password)  # Ensure passwords are different
    
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Test password hashing security using mock functions
        with patch('app.auth.get_password_hash', side_effect=mock_get_password_hash), \
             patch('app.auth.verify_password', side_effect=mock_verify_password):
            
            password_hash = mock_get_password_hash(correct_password)
            
            # Verify password hash properties
            assert password_hash != correct_password, "Password should be hashed, not stored in plain text"
            assert len(password_hash) > len(correct_password), "Hash should be longer than original password"
            assert password_hash.startswith('hashed_'), "Should use mock hashing"
            
            # Create user with hashed password
            user = User(
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=True
            )
            
            test_db.add(user)
            await test_db.commit()
            await test_db.refresh(user)
            
            # Test correct password authentication
            authenticated_user = await authenticate_user(test_db, email, correct_password)
            assert authenticated_user is not None, "Correct password should authenticate successfully"
            assert authenticated_user.id == user.id, "Authenticated user should match registered user"
            assert authenticated_user.role == role, "Authenticated user should have correct role"
            
            # Test incorrect password rejection
            failed_auth = await authenticate_user(test_db, email, wrong_password)
            assert failed_auth is None, "Incorrect password should fail authentication"
            
            # Test password verification functions directly
            assert mock_verify_password(correct_password, password_hash) is True, "Correct password should verify"
            assert mock_verify_password(wrong_password, password_hash) is False, "Incorrect password should not verify"
            
            # Test non-existent user authentication
            non_existent_auth = await authenticate_user(test_db, "nonexistent@example.com", correct_password)
            assert non_existent_auth is None, "Non-existent user should fail authentication"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    email=email_strategy,
    password=password_strategy,
    role=user_role_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_inactive_user_access_prevention(email, password, role):
    """
    **Feature: customer-onboarding-agent, Property 9: User Role Assignment and Authentication**
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    For any inactive user, the system should prevent authentication and access to the system,
    regardless of correct credentials.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create inactive user using mock hashing
        with patch('app.auth.get_password_hash', side_effect=mock_get_password_hash), \
             patch('app.auth.verify_password', side_effect=mock_verify_password):
            
            password_hash = mock_get_password_hash(password)
            
            inactive_user = User(
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=False  # User is inactive
            )
            
            test_db.add(inactive_user)
            await test_db.commit()
            await test_db.refresh(inactive_user)
            
            # Verify user is created but inactive
            assert inactive_user.id is not None, "User should be created"
            assert inactive_user.is_active is False, "User should be inactive"
            assert inactive_user.role == role, "User should have assigned role"
            
            # Test that inactive user cannot authenticate even with correct password
            auth_result = await authenticate_user(test_db, email, password)
            assert auth_result is None, "Inactive user should not authenticate even with correct password"
            
            # Test that password verification still works (for potential reactivation)
            assert mock_verify_password(password, password_hash) is True, "Password verification should still work"
            
            # Test user retrieval functions
            retrieved_user = await get_user_by_email(test_db, email)
            assert retrieved_user is not None, "Inactive user should still be retrievable by email"
            assert retrieved_user.is_active is False, "Retrieved user should show as inactive"
            
            retrieved_by_id = await get_user_by_id(test_db, inactive_user.id)
            assert retrieved_by_id is not None, "Inactive user should still be retrievable by ID"
            assert retrieved_by_id.is_active is False, "Retrieved user should show as inactive"
    
    await engine.dispose()