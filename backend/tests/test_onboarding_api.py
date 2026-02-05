"""
Integration tests for onboarding API endpoints
Tests the REST API endpoints for onboarding functionality
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import User, Document, UserRole
from app.auth import create_access_token


@pytest.mark.asyncio
async def test_start_onboarding_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test the start onboarding endpoint"""
    # Create test user
    user = User(
        email="test_start@example.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test document
    document = Document(
        filename="test_doc.txt",
        original_content="Test content for onboarding",
        content_hash="test_hash_start",
        file_size=100
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test start onboarding
    response = await client.post(
        f"/api/onboarding/start?document_id={document.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["document_id"] == document.id
    assert data["current_step"] == 1
    assert data["total_steps"] == 5  # Developer role
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_current_step_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test the get current step endpoint"""
    # Create test user
    user = User(
        email="test_step@example.com",
        password_hash="hashed_password",
        role=UserRole.BUSINESS_USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test document
    document = Document(
        filename="step_doc.txt",
        original_content="Step content for testing",
        content_hash="test_hash_step",
        file_size=150
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Start onboarding session first
    start_response = await client.post(
        f"/api/onboarding/start?document_id={document.id}",
        headers=headers
    )
    assert start_response.status_code == 200
    session_data = start_response.json()
    session_id = session_data["id"]
    
    # Test get current step
    response = await client.get(
        f"/api/onboarding/current-step/{session_id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["step_number"] == 1
    assert data["total_steps"] == 3  # Business_User role
    assert "Business Process Overview" in data["title"]
    assert len(data["tasks"]) > 0
    assert data["estimated_time"] > 0


@pytest.mark.asyncio
async def test_advance_step_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test the advance step endpoint"""
    # Create test user
    user = User(
        email="test_advance@example.com",
        password_hash="hashed_password",
        role=UserRole.BUSINESS_USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test document
    document = Document(
        filename="advance_doc.txt",
        original_content="Advance content for testing",
        content_hash="test_hash_advance",
        file_size=120
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Start onboarding session first
    start_response = await client.post(
        f"/api/onboarding/start?document_id={document.id}",
        headers=headers
    )
    assert start_response.status_code == 200
    session_data = start_response.json()
    session_id = session_data["id"]
    
    # Test advance step
    response = await client.post(
        f"/api/onboarding/advance-step/{session_id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "advanced"
    assert data["current_step"] == 2
    assert data["total_steps"] == 3


@pytest.mark.asyncio
async def test_get_session_progress_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test the get session progress endpoint"""
    # Create test user
    user = User(
        email="test_progress@example.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test document
    document = Document(
        filename="progress_doc.txt",
        original_content="Progress content for testing",
        content_hash="test_hash_progress",
        file_size=180
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Start onboarding session first
    start_response = await client.post(
        f"/api/onboarding/start?document_id={document.id}",
        headers=headers
    )
    assert start_response.status_code == 200
    session_data = start_response.json()
    session_id = session_data["id"]
    
    # Test get progress
    response = await client.get(
        f"/api/onboarding/progress/{session_id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["current_step"] == 1
    assert data["total_steps"] == 4  # Admin role
    assert data["completion_percentage"] == 0.0  # No steps completed yet
    assert len(data["steps_completed"]) == 0


@pytest.mark.asyncio
async def test_get_user_sessions_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Test the get user sessions endpoint"""
    # Create test user
    user = User(
        email="test_sessions@example.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test document
    document = Document(
        filename="sessions_doc.txt",
        original_content="Sessions content for testing",
        content_hash="test_hash_sessions",
        file_size=200
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Start multiple onboarding sessions
    for i in range(2):
        start_response = await client.post(
            f"/api/onboarding/start?document_id={document.id}",
            headers=headers
        )
        assert start_response.status_code == 200
    
    # Test get user sessions
    response = await client.get(
        "/api/onboarding/sessions",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for session in data:
        assert session["user_id"] == user.id
        assert session["document_id"] == document.id


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test that endpoints require authentication"""
    # Test without authorization header
    response = await client.post("/api/onboarding/start?document_id=1")
    assert response.status_code == 401
    
    response = await client.get("/api/onboarding/current-step/1")
    assert response.status_code == 401
    
    response = await client.post("/api/onboarding/advance-step/1")
    assert response.status_code == 401
    
    response = await client.get("/api/onboarding/progress/1")
    assert response.status_code == 401
    
    response = await client.get("/api/onboarding/sessions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_document_id(client: AsyncClient, db_session: AsyncSession):
    """Test starting onboarding with invalid document ID"""
    # Create test user
    user = User(
        email="test_invalid@example.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test with invalid document ID
    response = await client.post(
        "/api/onboarding/start?document_id=999",
        headers=headers
    )
    
    assert response.status_code == 400
    assert "Document with ID 999 not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_session_id(client: AsyncClient, db_session: AsyncSession):
    """Test accessing invalid session ID"""
    # Create test user
    user = User(
        email="test_invalid_session@example.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test with invalid session ID
    response = await client.get(
        "/api/onboarding/current-step/999",
        headers=headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()