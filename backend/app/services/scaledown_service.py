"""
ScaleDown Engine service for document processing and storage
Coordinates document validation, processing, and database operations
"""

from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from app.database import Document
from app.schemas import DocumentCreate, DocumentResponse, ProcessedDocumentResponse
from app.services.document_processor import DocumentProcessor
from app.services.claude_client import ClaudeAPIClient

logger = logging.getLogger(__name__)


class ScaleDownService:
    """Service for managing document processing workflow"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        # Initialize Claude client with error handling for testing
        try:
            self.claude_client = ClaudeAPIClient()
        except ValueError:
            # Handle missing API key during testing/development
            self.claude_client = None
    
    async def upload_and_validate_document(
        self, 
        file: UploadFile, 
        db: AsyncSession
    ) -> DocumentResponse:
        """
        Upload, validate, and store document
        
        Args:
            file: Uploaded file
            db: Database session
            
        Returns:
            DocumentResponse with stored document info
            
        Raises:
            HTTPException: If validation or storage fails
        """
        # Validate file
        is_valid, error_message = await self.document_processor.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Extract content
        content = await self.document_processor.extract_content(file)
        
        # Calculate content hash for deduplication
        content_hash = self.document_processor.calculate_content_hash(content)
        
        # Check if document already exists
        existing_doc = await self._get_document_by_hash(db, content_hash)
        if existing_doc:
            raise HTTPException(
                status_code=409,
                detail=f"Document with identical content already exists (ID: {existing_doc.id})"
            )
        
        # Get file info
        file_info = await self.document_processor.get_file_info(file)
        
        # Create document record
        document_data = DocumentCreate(
            filename=file_info['filename'],
            original_content=content,
            content_hash=content_hash,
            file_size=file_info['size']
        )
        
        # Store in database
        db_document = Document(
            filename=document_data.filename,
            original_content=document_data.original_content,
            content_hash=document_data.content_hash,
            file_size=document_data.file_size,
            uploaded_at=datetime.utcnow()
        )
        
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)
        
        return DocumentResponse.model_validate(db_document)
    
    async def process_document_with_claude(
        self,
        document_id: int,
        db: AsyncSession
    ) -> ProcessedDocumentResponse:
        """
        Process document content using Claude API
        
        Args:
            document_id: Document ID to process
            db: Database session
            
        Returns:
            ProcessedDocumentResponse with summary and tasks
            
        Raises:
            HTTPException: If document not found or processing fails
        """
        # Get document
        document = await self.get_document(document_id, db)
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        # Check if already processed
        if document.processed_summary and document.step_tasks:
            logger.info(f"Document {document_id} already processed, returning cached result")
            return ProcessedDocumentResponse(
                id=document.id,
                filename=document.filename,
                summary=document.processed_summary.get('text', '') if isinstance(document.processed_summary, dict) else str(document.processed_summary),
                tasks=document.step_tasks,
                processing_time=0.0  # Cached result
            )
        
        # Check if Claude client is available
        if not self.claude_client:
            raise HTTPException(
                status_code=503,
                detail="Claude API client not available. Please check ANTHROPIC_API_KEY configuration."
            )
        
        try:
            # Process with Claude API
            logger.info(f"Processing document {document_id} with Claude API")
            result = await self.claude_client.process_document_single_call(
                content=document.original_content,
                filename=document.filename
            )
            
            # Update document with processed content
            summary_data = {
                'text': result['summary'],
                'processing_metadata': {
                    'model_used': result.get('model_used'),
                    'processed_at': result.get('processed_at'),
                    'processing_time': result.get('processing_time')
                }
            }
            
            updated_doc = await self.update_processed_content(
                document_id=document_id,
                summary=summary_data,
                tasks=result['tasks'],
                db=db
            )
            
            if not updated_doc:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update document with processed content"
                )
            
            logger.info(f"Successfully processed document {document_id}")
            
            return ProcessedDocumentResponse(
                id=updated_doc.id,
                filename=updated_doc.filename,
                summary=result['summary'],
                tasks=result['tasks'],
                processing_time=result.get('processing_time', 0.0)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )
    
    async def upload_and_process_document(
        self,
        file: UploadFile,
        db: AsyncSession
    ) -> ProcessedDocumentResponse:
        """
        Upload, validate, store, and process document in one operation
        
        Args:
            file: Uploaded file
            db: Database session
            
        Returns:
            ProcessedDocumentResponse with summary and tasks
        """
        # Upload and validate
        document = await self.upload_and_validate_document(file, db)
        
        # Process with Claude
        processed = await self.process_document_with_claude(document.id, db)
        
        return processed
    
    async def get_document(self, document_id: int, db: AsyncSession) -> Optional[DocumentResponse]:
        """
        Retrieve document by ID
        
        Args:
            document_id: Document ID
            db: Database session
            
        Returns:
            DocumentResponse or None if not found
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if document:
            return DocumentResponse.model_validate(document)
        return None
    
    async def list_documents(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[DocumentResponse]:
        """
        List all documents with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of DocumentResponse objects
        """
        result = await db.execute(
            select(Document)
            .order_by(Document.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()
        
        return [DocumentResponse.model_validate(doc) for doc in documents]
    
    async def delete_document(self, document_id: int, db: AsyncSession) -> bool:
        """
        Delete document by ID
        
        Args:
            document_id: Document ID
            db: Database session
            
        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if document:
            await db.delete(document)
            await db.commit()
            return True
        return False
    
    async def update_processed_content(
        self,
        document_id: int,
        summary: Dict[str, Any],
        tasks: list[str],
        db: AsyncSession
    ) -> Optional[DocumentResponse]:
        """
        Update document with processed content from Claude API
        
        Args:
            document_id: Document ID
            summary: Processed summary data
            tasks: List of extracted tasks
            db: Database session
            
        Returns:
            Updated DocumentResponse or None if not found
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if document:
            document.processed_summary = summary
            document.step_tasks = tasks
            await db.commit()
            await db.refresh(document)
            return DocumentResponse.model_validate(document)
        return None
    
    async def _get_document_by_hash(self, db: AsyncSession, content_hash: str) -> Optional[Document]:
        """Get document by content hash for deduplication"""
        result = await db.execute(select(Document).where(Document.content_hash == content_hash))
        return result.scalar_one_or_none()
    
    def get_document_stats(self, document: DocumentResponse) -> Dict[str, Any]:
        """
        Get document statistics and metadata
        
        Args:
            document: Document to analyze
            
        Returns:
            Dictionary with document statistics
        """
        content_length = len(document.original_content) if hasattr(document, 'original_content') else 0
        
        stats = {
            'id': document.id,
            'filename': document.filename,
            'file_size': document.file_size,
            'content_length': content_length,
            'uploaded_at': document.uploaded_at,
            'has_summary': document.processed_summary is not None,
            'has_tasks': document.step_tasks is not None and len(document.step_tasks) > 0,
            'processing_status': 'processed' if document.processed_summary else 'pending'
        }
        
        if document.processed_summary:
            if isinstance(document.processed_summary, dict):
                stats['summary_length'] = len(document.processed_summary.get('text', ''))
                if 'processing_metadata' in document.processed_summary:
                    stats['processing_metadata'] = document.processed_summary['processing_metadata']
            else:
                stats['summary_length'] = len(str(document.processed_summary))
        
        if document.step_tasks:
            stats['task_count'] = len(document.step_tasks)
        
        return stats
    
    async def get_claude_health(self) -> Dict[str, Any]:
        """
        Check Claude API health status
        
        Returns:
            Health status information
        """
        if not self.claude_client:
            return {
                "status": "unavailable",
                "error": "Claude API client not configured",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return await self.claude_client.health_check()