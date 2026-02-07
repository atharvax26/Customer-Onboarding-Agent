"""
Integration tests for ScaleDown service
"""

import pytest
import io
from fastapi import UploadFile
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.scaledown_service import ScaleDownService


class TestScaleDownIntegration:
    """Test ScaleDown service integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ScaleDownService()
    
    @pytest.mark.asyncio
    async def test_upload_and_validate_document_success(self):
        """Test successful document upload and validation"""
        # Create mock text file
        content = b"This is a comprehensive test document with enough content to validate properly."
        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(content),
            size=len(content),
            headers={"content-type": "text/plain"}
        )
        
        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock the _get_document_by_hash method to return None (no existing document)
        with patch.object(self.service, '_get_document_by_hash', return_value=None):
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            # Mock the add method to set the document attributes
            def mock_add(doc):
                doc.id = 1
                doc.filename = "test.txt"
                doc.original_content = content.decode('utf-8')
                doc.file_size = len(content)
                doc.content_hash = "test-hash"
            
            mock_db.add = mock_add
            
            # Mock refresh to set the ID
            def mock_refresh(doc):
                doc.id = 1
            
            mock_db.refresh.side_effect = mock_refresh
            
            # Test the upload
            result = await self.service.upload_and_validate_document(file, mock_db)
            
            # Verify the result
            assert result is not None
            assert result.filename == "test.txt"
    
    @pytest.mark.asyncio
    async def test_document_validation_failure(self):
        """Test document validation failure"""
        # Create invalid file (too large)
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # Exceed 10MB limit
        file = UploadFile(
            filename="large.txt",
            file=io.BytesIO(large_content),
            size=len(large_content),
            headers={"content-type": "text/plain"}
        )
        
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Test validation failure
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await self.service.upload_and_validate_document(file, mock_db)
        
        assert exc_info.value.status_code == 400
        assert "exceeds maximum allowed size" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_claude_client_unavailable(self):
        """Test behavior when Claude client is unavailable"""
        # Create service without Claude client
        service = ScaleDownService()
        service.claude_client = None
        
        # Mock database session and document result
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock the get_document method to return a valid document
        mock_document_response = MagicMock()
        mock_document_response.id = 1
        mock_document_response.filename = "test.txt"
        mock_document_response.original_content = "Test content"
        mock_document_response.file_size = 100
        mock_document_response.uploaded_at = "2024-01-01T00:00:00"
        mock_document_response.processed_summary = None
        mock_document_response.step_tasks = None
        mock_document_response.content_hash = "test-hash"
        
        with patch.object(service, 'get_document', return_value=mock_document_response):
            # Test processing failure
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await service.process_document_with_scaledown_ai(1, mock_db)
            
            assert exc_info.value.status_code == 503
            assert "ScaleDown.ai API client not available" in str(exc_info.value.detail)
    
    def test_get_document_stats(self):
        """Test document statistics generation"""
        # Mock document response
        mock_doc = AsyncMock()
        mock_doc.id = 1
        mock_doc.filename = "test.txt"
        mock_doc.file_size = 1000
        mock_doc.uploaded_at = "2024-01-01T00:00:00"
        mock_doc.processed_summary = {"text": "Test summary"}
        mock_doc.step_tasks = ["Task 1", "Task 2"]
        mock_doc.original_content = "Test content"
        
        stats = self.service.get_document_stats(mock_doc)
        
        assert stats['id'] == 1
        assert stats['filename'] == "test.txt"
        assert stats['file_size'] == 1000
        assert stats['has_summary'] is True
        assert stats['has_tasks'] is True
        assert stats['task_count'] == 2
        assert stats['processing_status'] == 'processed'
    
    @pytest.mark.asyncio
    async def test_get_scaledown_ai_health_unavailable(self):
        """Test ScaleDown.ai health check when client unavailable"""
        service = ScaleDownService()
        service.scaledown_ai_client = None
        
        result = await service.get_scaledown_ai_health()
        
        assert result['status'] == 'unavailable'
        assert 'ScaleDown.ai API client not configured' in result['error']