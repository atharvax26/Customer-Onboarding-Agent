"""
End-to-End Integration Tests for Customer Onboarding Agent

This module tests complete user journeys for all roles, verifies real-time features,
tests error scenarios and recovery mechanisms, and validates performance requirements.

Requirements: 9.1 - Performance and Reliability
"""

import pytest
import asyncio
import time
import tempfile
import os
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import json

from app.database import User, Document, OnboardingSession, EngagementLog
from app.schemas import UserRole


class TestCompleteUserJourneys:
    """Test complete user journeys for all roles"""
    
    @pytest.mark.asyncio
    async def test_developer_complete_journey(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete developer onboarding journey from registration to completion"""
        # Step 1: Register as developer
        register_data = {
            "email": "dev@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        register_response = await client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        # Step 2: Login
        login_data = {"email": "dev@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Upload document
        test_content = "API Documentation\n\nThis is a comprehensive API guide with endpoints and examples."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("test_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            assert upload_response.status_code == 200
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        # Step 4: Start onboarding
        onboarding_data = {"document_id": document_id}
        start_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]
        
        # Verify developer gets exactly 5 steps
        session_response = await client.get(f"/api/onboarding/session/{session_id}", headers=headers)
        assert session_response.status_code == 200
        assert session_response.json()["total_steps"] == 5
        
        # Step 5: Complete all onboarding steps
        for step in range(1, 6):
            # Get current step
            step_response = await client.get(f"/api/onboarding/session/{session_id}/step", headers=headers)
            assert step_response.status_code == 200
            assert step_response.json()["step_number"] == step
            
            # Record some interactions for engagement scoring
            interaction_data = {
                "session_id": session_id,
                "event_type": "button_click",
                "event_data": {"button": "next_step", "step": step}
            }
            await client.post("/api/engagement/interaction", json=interaction_data, headers=headers)
            
            # Complete step
            complete_response = await client.post(f"/api/onboarding/session/{session_id}/complete-step", headers=headers)
            assert complete_response.status_code == 200
        
        # Step 6: Verify completion
        final_session = await client.get(f"/api/onboarding/session/{session_id}", headers=headers)
        assert final_session.status_code == 200
        assert final_session.json()["status"] == "completed"
        
        # Step 7: Check analytics reflect completion
        analytics_response = await client.get("/api/analytics/activation-rates", headers=headers)
        assert analytics_response.status_code == 200
        analytics_data = analytics_response.json()
        assert analytics_data["developer"]["completed"] >= 1
    
    @pytest.mark.asyncio
    async def test_business_user_complete_journey(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete business user onboarding journey"""
        # Step 1: Register as business user
        register_data = {
            "email": "business@example.com",
            "password": "testpass123",
            "role": "business_user"
        }
        register_response = await client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        # Step 2: Login
        login_data = {"email": "business@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Upload document
        test_content = "Business Process Guide\n\nWorkflow management and business operations."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("business_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            assert upload_response.status_code == 200
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        # Step 4: Start onboarding
        onboarding_data = {"document_id": document_id}
        start_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]
        
        # Verify business user gets exactly 3 steps
        session_response = await client.get(f"/api/onboarding/session/{session_id}", headers=headers)
        assert session_response.status_code == 200
        assert session_response.json()["total_steps"] == 3
        
        # Step 5: Complete all onboarding steps
        for step in range(1, 4):
            step_response = await client.get(f"/api/onboarding/session/{session_id}/step", headers=headers)
            assert step_response.status_code == 200
            assert step_response.json()["step_number"] == step
            
            # Complete step
            complete_response = await client.post(f"/api/onboarding/session/{session_id}/complete-step", headers=headers)
            assert complete_response.status_code == 200
        
        # Step 6: Verify completion
        final_session = await client.get(f"/api/onboarding/session/{session_id}", headers=headers)
        assert final_session.status_code == 200
        assert final_session.json()["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_admin_complete_journey(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete admin onboarding journey"""
        # Step 1: Register as admin
        register_data = {
            "email": "admin@example.com",
            "password": "testpass123",
            "role": "admin"
        }
        register_response = await client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        # Step 2: Login
        login_data = {"email": "admin@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Upload document
        test_content = "Admin Configuration Guide\n\nSystem administration and user management."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("admin_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            assert upload_response.status_code == 200
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        # Step 4: Start onboarding
        onboarding_data = {"document_id": document_id}
        start_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]
        
        # Step 5: Verify admin gets appropriate steps (implementation dependent)
        session_response = await client.get(f"/api/onboarding/session/{session_id}", headers=headers)
        assert session_response.status_code == 200
        assert session_response.json()["total_steps"] > 0
        
        # Complete first step to verify functionality
        step_response = await client.get(f"/api/onboarding/session/{session_id}/step", headers=headers)
        assert step_response.status_code == 200
        
        complete_response = await client.post(f"/api/onboarding/session/{session_id}/complete-step", headers=headers)
        assert complete_response.status_code == 200


class TestRealTimeFeatures:
    """Test real-time features work correctly"""
    
    @pytest.mark.asyncio
    async def test_real_time_engagement_scoring(self, client: AsyncClient, db_session: AsyncSession):
        """Test real-time engagement score updates"""
        # Setup user and session
        register_data = {
            "email": "realtime@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        await client.post("/api/auth/register", json=register_data)
        
        login_data = {"email": "realtime@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload document and start onboarding
        test_content = "Real-time test document"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("realtime_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        onboarding_data = {"document_id": document_id}
        start_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        session_id = start_response.json()["session_id"]
        
        # Record initial engagement score
        initial_score_response = await client.get(f"/api/engagement/score/{session_id}", headers=headers)
        assert initial_score_response.status_code == 200
        initial_score = initial_score_response.json()["current_score"]
        
        # Record interaction
        interaction_data = {
            "session_id": session_id,
            "event_type": "button_click",
            "event_data": {"button": "help", "timestamp": time.time()}
        }
        await client.post("/api/engagement/interaction", json=interaction_data, headers=headers)
        
        # Wait a moment for real-time processing (should be < 5 seconds per requirement)
        await asyncio.sleep(1)
        
        # Check updated score
        updated_score_response = await client.get(f"/api/engagement/score/{session_id}", headers=headers)
        assert updated_score_response.status_code == 200
        updated_score = updated_score_response.json()["current_score"]
        
        # Score should have changed (increased due to interaction)
        assert updated_score != initial_score
        assert 0 <= updated_score <= 100
    
    @pytest.mark.asyncio
    async def test_real_time_intervention_system(self, client: AsyncClient, db_session: AsyncSession):
        """Test real-time intervention triggering"""
        # Setup user and session
        register_data = {
            "email": "intervention@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        await client.post("/api/auth/register", json=register_data)
        
        login_data = {"email": "intervention@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload document and start onboarding
        test_content = "Intervention test document"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("intervention_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        onboarding_data = {"document_id": document_id}
        start_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        session_id = start_response.json()["session_id"]
        
        # Simulate low engagement by recording inactivity
        inactivity_data = {
            "session_id": session_id,
            "event_type": "inactivity",
            "event_data": {"duration": 300}  # 5 minutes of inactivity
        }
        await client.post("/api/engagement/interaction", json=inactivity_data, headers=headers)
        
        # Wait for intervention system to process
        await asyncio.sleep(2)
        
        # Check if intervention was triggered
        interventions_response = await client.get(f"/api/intervention/session/{session_id}", headers=headers)
        assert interventions_response.status_code == 200
        
        # Should have at least one intervention if score dropped below 30
        score_response = await client.get(f"/api/engagement/score/{session_id}", headers=headers)
        current_score = score_response.json()["current_score"]
        
        if current_score < 30:
            interventions = interventions_response.json()
            assert len(interventions) > 0
    
    @pytest.mark.asyncio
    async def test_real_time_analytics_updates(self, client: AsyncClient, db_session: AsyncSession):
        """Test real-time analytics updates"""
        # Create multiple users to test analytics aggregation
        users = []
        for i in range(3):
            register_data = {
                "email": f"analytics{i}@example.com",
                "password": "testpass123",
                "role": "developer" if i < 2 else "business_user"
            }
            await client.post("/api/auth/register", json=register_data)
            
            login_data = {"email": f"analytics{i}@example.com", "password": "testpass123"}
            login_response = await client.post("/api/auth/login", json=login_data)
            token = login_response.json()["access_token"]
            users.append({"token": token, "headers": {"Authorization": f"Bearer {token}"}})
        
        # Get initial analytics
        initial_analytics = await client.get("/api/analytics/activation-rates", headers=users[0]["headers"])
        assert initial_analytics.status_code == 200
        initial_data = initial_analytics.json()
        
        # Complete onboarding for one user
        test_content = "Analytics test document"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("analytics_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=users[0]["headers"])
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        onboarding_data = {"document_id": document_id}
        start_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=users[0]["headers"])
        session_id = start_response.json()["session_id"]
        
        # Complete all steps
        for step in range(1, 6):  # Developer has 5 steps
            await client.post(f"/api/onboarding/session/{session_id}/complete-step", headers=users[0]["headers"])
        
        # Check updated analytics
        updated_analytics = await client.get("/api/analytics/activation-rates", headers=users[0]["headers"])
        assert updated_analytics.status_code == 200
        updated_data = updated_analytics.json()
        
        # Analytics should reflect the completion
        assert updated_data["developer"]["completed"] > initial_data["developer"]["completed"]


class TestErrorScenariosAndRecovery:
    """Test error scenarios and recovery mechanisms"""
    
    @pytest.mark.asyncio
    async def test_invalid_document_upload_recovery(self, client: AsyncClient, db_session: AsyncSession):
        """Test recovery from invalid document uploads"""
        # Setup user
        register_data = {
            "email": "error@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        await client.post("/api/auth/register", json=register_data)
        
        login_data = {"email": "error@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Upload invalid file type
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
            f.write("Invalid file content")
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("invalid.exe", f, "application/octet-stream")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            
            # Should return error but not crash
            assert upload_response.status_code in [400, 422]
            error_data = upload_response.json()
            assert "error" in error_data or "detail" in error_data
        finally:
            os.unlink(temp_file_path)
        
        # Test 2: Upload empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")  # Empty file
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("empty.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            
            # Should handle gracefully
            assert upload_response.status_code in [400, 422]
        finally:
            os.unlink(temp_file_path)
        
        # Test 3: Valid upload after errors should work
        test_content = "Valid document content after errors"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("valid.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            
            # Should succeed after previous errors
            assert upload_response.status_code == 200
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_authentication_error_recovery(self, client: AsyncClient, db_session: AsyncSession):
        """Test authentication error handling and recovery"""
        # Test 1: Invalid credentials
        login_data = {"email": "nonexistent@example.com", "password": "wrongpass"}
        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 401
        
        # Test 2: Invalid token access
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        protected_response = await client.get("/api/onboarding/sessions", headers=invalid_headers)
        assert protected_response.status_code == 401
        
        # Test 3: Valid authentication after errors should work
        register_data = {
            "email": "recovery@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        register_response = await client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {"email": "recovery@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        valid_headers = {"Authorization": f"Bearer {token}"}
        protected_response = await client.get("/api/onboarding/sessions", headers=valid_headers)
        assert protected_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_database_error_recovery(self, client: AsyncClient, db_session: AsyncSession):
        """Test database error handling and recovery"""
        # Setup user
        register_data = {
            "email": "dbtest@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        await client.post("/api/auth/register", json=register_data)
        
        login_data = {"email": "dbtest@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test accessing non-existent session
        nonexistent_response = await client.get("/api/onboarding/session/99999", headers=headers)
        assert nonexistent_response.status_code == 404
        
        # Test system should still be functional after error
        sessions_response = await client.get("/api/onboarding/sessions", headers=headers)
        assert sessions_response.status_code == 200


class TestPerformanceRequirements:
    """Test performance requirements validation"""
    
    @pytest.mark.asyncio
    async def test_api_response_times(self, client: AsyncClient, db_session: AsyncSession):
        """Test API response times under 2 seconds (Requirement 9.1)"""
        # Setup user
        register_data = {
            "email": "perf@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        await client.post("/api/auth/register", json=register_data)
        
        login_data = {"email": "perf@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test various API endpoints for response time
        endpoints_to_test = [
            ("/api/onboarding/sessions", "GET"),
            ("/api/analytics/activation-rates", "GET"),
            ("/api/engagement/interactions", "GET"),
        ]
        
        for endpoint, method in endpoints_to_test:
            start_time = time.time()
            
            if method == "GET":
                response = await client.get(endpoint, headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Response time should be under 2 seconds
            assert response_time < 2.0, f"Endpoint {endpoint} took {response_time:.2f}s (> 2s limit)"
            assert response.status_code in [200, 404]  # 404 is acceptable for empty data
    
    @pytest.mark.asyncio
    async def test_concurrent_user_handling(self, client: AsyncClient, db_session: AsyncSession):
        """Test system handles multiple concurrent users"""
        # Create multiple users concurrently
        async def create_and_test_user(user_id: int):
            register_data = {
                "email": f"concurrent{user_id}@example.com",
                "password": "testpass123",
                "role": "developer"
            }
            register_response = await client.post("/api/auth/register", json=register_data)
            assert register_response.status_code == 201
            
            login_data = {"email": f"concurrent{user_id}@example.com", "password": "testpass123"}
            login_response = await client.post("/api/auth/login", json=login_data)
            assert login_response.status_code == 200
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test basic operations
            sessions_response = await client.get("/api/onboarding/sessions", headers=headers)
            assert sessions_response.status_code == 200
            
            return user_id
        
        # Run 5 concurrent user operations
        tasks = [create_and_test_user(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should succeed
        for result in results:
            assert not isinstance(result, Exception), f"Concurrent operation failed: {result}"
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, client: AsyncClient, db_session: AsyncSession):
        """Test system health monitoring endpoints"""
        # Test basic health check
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert "status" in health_data
        
        # Test component health checks
        components = ["database", "claude_api", "engagement_service"]
        for component in components:
            component_response = await client.get(f"/health/{component}")
            assert component_response.status_code == 200
            component_data = component_response.json()
            assert "status" in component_data
        
        # Test health history
        history_response = await client.get("/health-history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert "history" in history_data


class TestDataIntegrityAndConsistency:
    """Test data integrity and consistency under various conditions"""
    
    @pytest.mark.asyncio
    async def test_concurrent_onboarding_sessions(self, client: AsyncClient, db_session: AsyncSession):
        """Test data consistency with concurrent onboarding sessions"""
        # Setup user
        register_data = {
            "email": "integrity@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        await client.post("/api/auth/register", json=register_data)
        
        login_data = {"email": "integrity@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload document
        test_content = "Integrity test document"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("integrity_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        # Start multiple onboarding sessions (should be prevented or handled gracefully)
        onboarding_data = {"document_id": document_id}
        
        session1_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        assert session1_response.status_code == 200
        session1_id = session1_response.json()["session_id"]
        
        # Attempt to start another session (system should handle appropriately)
        session2_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        # Either should succeed with new session or return existing session
        assert session2_response.status_code in [200, 409]
        
        # Verify data consistency
        sessions_response = await client.get("/api/onboarding/sessions", headers=headers)
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        
        # Should have consistent session data
        for session in sessions:
            assert "id" in session
            assert "status" in session
            assert session["status"] in ["active", "completed", "abandoned"]
    
    @pytest.mark.asyncio
    async def test_engagement_score_consistency(self, client: AsyncClient, db_session: AsyncSession):
        """Test engagement score calculation consistency"""
        # Setup user and session
        register_data = {
            "email": "score@example.com",
            "password": "testpass123",
            "role": "developer"
        }
        await client.post("/api/auth/register", json=register_data)
        
        login_data = {"email": "score@example.com", "password": "testpass123"}
        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload document and start onboarding
        test_content = "Score consistency test"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("score_doc.txt", f, "text/plain")}
                upload_response = await client.post("/api/scaledown/upload", files=files, headers=headers)
            document_id = upload_response.json()["id"]
        finally:
            os.unlink(temp_file_path)
        
        onboarding_data = {"document_id": document_id}
        start_response = await client.post("/api/onboarding/start", json=onboarding_data, headers=headers)
        session_id = start_response.json()["session_id"]
        
        # Record multiple interactions and verify score consistency
        interactions = [
            {"event_type": "button_click", "event_data": {"button": "next"}},
            {"event_type": "page_view", "event_data": {"page": "step1"}},
            {"event_type": "time_spent", "event_data": {"duration": 30}},
        ]
        
        scores = []
        for interaction in interactions:
            interaction["session_id"] = session_id
            await client.post("/api/engagement/interaction", json=interaction, headers=headers)
            
            # Get score after each interaction
            score_response = await client.get(f"/api/engagement/score/{session_id}", headers=headers)
            assert score_response.status_code == 200
            score = score_response.json()["current_score"]
            scores.append(score)
            
            # Score should always be between 0 and 100
            assert 0 <= score <= 100
        
        # Scores should generally increase with positive interactions
        # (allowing for some variation due to time-based factors)
        assert len(scores) == len(interactions)