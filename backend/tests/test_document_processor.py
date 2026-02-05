"""
Tests for document processor functionality
"""

import pytest
import io
from fastapi import UploadFile
from app.services.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test document processing functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = DocumentProcessor()
    
    @pytest.mark.asyncio
    async def test_validate_text_file_success(self):
        """Test successful validation of text file"""
        # Create mock text file
        content = b"This is a test document content."
        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(content),
            size=len(content),
            headers={"content-type": "text/plain"}
        )
        
        is_valid, error = await self.processor.validate_file(file)
        
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_validate_file_too_large(self):
        """Test validation failure for oversized file"""
        # Create mock file that exceeds size limit
        large_content = b"x" * (DocumentProcessor.MAX_FILE_SIZE + 1)
        file = UploadFile(
            filename="large.txt",
            file=io.BytesIO(large_content),
            size=len(large_content),
            headers={"content-type": "text/plain"}
        )
        
        is_valid, error = await self.processor.validate_file(file)
        
        assert is_valid is False
        assert "exceeds maximum allowed size" in error
    
    @pytest.mark.asyncio
    async def test_validate_unsupported_format(self):
        """Test validation failure for unsupported file format"""
        content = b"fake image content"
        file = UploadFile(
            filename="image.jpg",
            file=io.BytesIO(content),
            size=len(content),
            headers={"content-type": "image/jpeg"}
        )
        
        is_valid, error = await self.processor.validate_file(file)
        
        assert is_valid is False
        assert "Unsupported file type" in error
    
    @pytest.mark.asyncio
    async def test_validate_missing_filename(self):
        """Test validation failure for missing filename"""
        content = b"test content"
        file = UploadFile(
            filename=None,
            file=io.BytesIO(content),
            size=len(content),
            headers={"content-type": "text/plain"}
        )
        
        is_valid, error = await self.processor.validate_file(file)
        
        assert is_valid is False
        assert "Filename is required" in error
    
    @pytest.mark.asyncio
    async def test_extract_text_content(self):
        """Test text content extraction"""
        content = b"This is test content for extraction."
        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(content),
            headers={"content-type": "text/plain"}
        )
        
        extracted = await self.processor.extract_content(file)
        
        assert extracted == "This is test content for extraction."
    
    @pytest.mark.asyncio
    async def test_extract_markdown_content(self):
        """Test markdown content extraction"""
        content = b"# Test Markdown\n\nThis is **bold** text."
        file = UploadFile(
            filename="test.md",
            file=io.BytesIO(content),
            headers={"content-type": "text/markdown"}
        )
        
        extracted = await self.processor.extract_content(file)
        
        assert "# Test Markdown" in extracted
        assert "**bold**" in extracted
    
    def test_calculate_content_hash(self):
        """Test content hash calculation"""
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "This is different content"
        
        hash1 = self.processor.calculate_content_hash(content1)
        hash2 = self.processor.calculate_content_hash(content2)
        hash3 = self.processor.calculate_content_hash(content3)
        
        # Same content should produce same hash
        assert hash1 == hash2
        # Different content should produce different hash
        assert hash1 != hash3
        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64
    
    @pytest.mark.asyncio
    async def test_get_file_info(self):
        """Test file information extraction"""
        content = b"Test file content"
        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(content),
            headers={"content-type": "text/plain"}
        )
        
        info = await self.processor.get_file_info(file)
        
        assert info['filename'] == "test.txt"
        assert info['content_type'] == "text/plain"
        assert info['size'] == len(content)
        assert info['extension'] == ".txt"
    
    @pytest.mark.asyncio
    async def test_validate_pdf_file(self):
        """Test PDF file validation"""
        content = b"fake pdf content"
        file = UploadFile(
            filename="document.pdf",
            file=io.BytesIO(content),
            size=len(content),
            headers={"content-type": "application/pdf"}
        )
        
        is_valid, error = await self.processor.validate_file(file)
        
        assert is_valid is True
        assert error is None