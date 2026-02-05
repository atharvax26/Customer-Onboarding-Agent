"""
Document processing service for ScaleDown Engine
Handles file upload, validation, and content extraction
"""

import hashlib
import mimetypes
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
import pypdf
import io
from pathlib import Path


class DocumentProcessor:
    """Handles document upload validation and content extraction"""
    
    # Supported file types and their MIME types
    SUPPORTED_FORMATS = {
        'text/plain': ['.txt'],
        'application/pdf': ['.pdf'],
        'text/markdown': ['.md'],
        'text/x-markdown': ['.md']
    }
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_FILE_SIZE = 1  # 1 byte
    
    def __init__(self):
        pass
    
    async def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file format and size
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if hasattr(file, 'size') and file.size is not None:
            if file.size > self.MAX_FILE_SIZE:
                return False, f"File size {file.size} bytes exceeds maximum allowed size of {self.MAX_FILE_SIZE} bytes"
            if file.size < self.MIN_FILE_SIZE:
                return False, f"File size {file.size} bytes is below minimum required size of {self.MIN_FILE_SIZE} bytes"
        
        # Check filename
        if not file.filename:
            return False, "Filename is required"
        
        # Get file extension
        file_path = Path(file.filename)
        file_extension = file_path.suffix.lower()
        
        # Check MIME type
        mime_type = file.content_type
        if not mime_type:
            # Try to guess MIME type from filename
            mime_type, _ = mimetypes.guess_type(file.filename)
        
        # Validate against supported formats
        if mime_type not in self.SUPPORTED_FORMATS:
            supported_extensions = []
            for extensions in self.SUPPORTED_FORMATS.values():
                supported_extensions.extend(extensions)
            return False, f"Unsupported file type '{mime_type}'. Supported formats: {', '.join(supported_extensions)}"
        
        # Check if file extension matches MIME type
        expected_extensions = self.SUPPORTED_FORMATS[mime_type]
        if file_extension not in expected_extensions:
            return False, f"File extension '{file_extension}' does not match content type '{mime_type}'"
        
        return True, None
    
    async def extract_content(self, file: UploadFile) -> str:
        """
        Extract text content from uploaded file
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Extracted text content
            
        Raises:
            HTTPException: If content extraction fails
        """
        try:
            # Read file content
            content = await file.read()
            
            # Reset file pointer for potential re-reading
            await file.seek(0)
            
            # Extract content based on file type
            if file.content_type == 'application/pdf':
                return await self._extract_pdf_content(content)
            elif file.content_type in ['text/plain', 'text/markdown', 'text/x-markdown']:
                return await self._extract_text_content(content)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported content type for extraction: {file.content_type}"
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract content from file: {str(e)}"
            )
    
    async def _extract_pdf_content(self, content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            text_content = []
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            extracted_text = '\n'.join(text_content).strip()
            
            if not extracted_text:
                raise HTTPException(
                    status_code=400,
                    detail="PDF file appears to be empty or contains no extractable text"
                )
            
            return extracted_text
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from PDF: {str(e)}"
            )
    
    async def _extract_text_content(self, content: bytes) -> str:
        """Extract text from plain text files"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text_content = content.decode(encoding).strip()
                    if text_content:
                        return text_content
                except UnicodeDecodeError:
                    continue
            
            raise HTTPException(
                status_code=400,
                detail="Unable to decode text file with supported encodings"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text content: {str(e)}"
            )
    
    def calculate_content_hash(self, content: str) -> str:
        """
        Calculate SHA-256 hash of content for deduplication
        
        Args:
            content: Text content to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def get_file_info(self, file: UploadFile) -> dict:
        """
        Get comprehensive file information
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Dictionary with file metadata
        """
        # Read content to get actual size
        content = await file.read()
        await file.seek(0)  # Reset for potential re-reading
        
        return {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': len(content),
            'extension': Path(file.filename).suffix.lower() if file.filename else None
        }