"""
Document processing service using Gemini AI
Handles document validation, processing, and storage
"""

from typing import Optional, Dict, Any, List
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from app.database import Document
from app.schemas import DocumentCreate, DocumentResponse, ProcessedDocumentResponse
from app.services.document_processor import DocumentProcessor
from app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ScaleDownService:
    """Service for managing document processing workflow with Gemini AI"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        # Initialize Gemini AI client
        try:
            self.gemini_client = GeminiClient()
            logger.info("Gemini AI client initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.gemini_client = None
    
    async def upload_and_validate_document(
        self, 
        file: UploadFile, 
        db: AsyncSession,
        user_id: int
    ) -> DocumentResponse:
        """Upload, validate, and store document for a specific user"""
        # Validate file
        is_valid, error_message = await self.document_processor.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Extract content
        content = await self.document_processor.extract_content(file)
        
        # Calculate content hash for deduplication
        content_hash = self.document_processor.calculate_content_hash(content)
        
        # Check if document already exists for this user
        existing_doc = await self._get_document_by_hash_and_user(db, content_hash, user_id)
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
        
        # Store in database with user_id
        db_document = Document(**document_data.dict(), user_id=user_id)
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)
        
        logger.info(f"Document uploaded successfully: {db_document.id} for user {user_id}")
        
        return DocumentResponse(
            id=db_document.id,
            filename=db_document.filename,
            uploaded_at=db_document.uploaded_at,
            file_size=db_document.file_size,
            content_hash=db_document.content_hash
        )
    
    async def upload_and_process_document(
        self, 
        file: UploadFile, 
        db: AsyncSession,
        user_id: int
    ) -> ProcessedDocumentResponse:
        """Upload, validate, and process document in one operation"""
        # First upload and validate
        document_response = await self.upload_and_validate_document(file, db, user_id)
        
        # Then process the document
        processed_response = await self.process_document(document_response.id, db, user_id)
        
        return processed_response
    
    async def process_document(
        self, 
        document_id: int, 
        db: AsyncSession,
        user_id: int
    ) -> ProcessedDocumentResponse:
        """Process document content using Gemini AI"""
        # Get document and verify ownership
        document = await self._get_document_raw(document_id, db, user_id)
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
                processing_time=0.0
            )
        
        # Check if Gemini AI client is available
        if not self.gemini_client:
            raise HTTPException(
                status_code=503,
                detail="Gemini AI service not available. Please configure GEMINI_API_KEY."
            )
        
        try:
            logger.info(f"Processing document {document_id} with Gemini AI")
            start_time = datetime.utcnow()
            
            # Generate onboarding guide using Gemini
            guide_data = await self.gemini_client.generate_onboarding_guide(
                document_content=document.original_content,
                user_role="Developer"
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract summary and steps
            summary_text = guide_data.get('summary', 'Document processed successfully')
            steps = guide_data.get('steps', [])
            
            # Format summary with metadata
            summary_data = {
                'text': summary_text,
                'processing_metadata': {
                    'model_used': 'gemini-2.5-flash',
                    'processed_at': datetime.utcnow().isoformat(),
                    'processing_time': processing_time,
                    'steps_generated': len(steps)
                }
            }
            
            logger.info(f"Gemini generated {len(steps)} steps in {processing_time:.2f}s")
            
            # Update document with processed content
            updated_doc = await self.update_processed_content(
                document_id=document_id,
                summary=summary_data,
                tasks=steps,
                db=db,
                user_id=user_id
            )
            
            if not updated_doc:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update document with processed content"
                )
            
            return ProcessedDocumentResponse(
                id=updated_doc.id,
                filename=updated_doc.filename,
                summary=summary_text,
                tasks=steps,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )
    
    async def process_document_with_scaledown_ai(
        self, 
        document_id: int, 
        db: AsyncSession,
        user_id: int
    ) -> ProcessedDocumentResponse:
        """Alias for process_document for backward compatibility"""
        return await self.process_document(document_id, db, user_id)
    
    async def get_document(self, document_id: int, db: AsyncSession, user_id: int) -> Optional[DocumentResponse]:
        """Get document by ID (only if owned by user)"""
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        doc = result.scalar_one_or_none()
        
        if doc:
            return DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                uploaded_at=doc.uploaded_at,
                file_size=doc.file_size,
                content_hash=doc.content_hash,
                processed_summary=doc.processed_summary,
                step_tasks=doc.step_tasks
            )
        return None
    
    async def _get_document_raw(self, document_id: int, db: AsyncSession, user_id: int) -> Optional[Document]:
        """Get raw document object by ID (internal use, with user verification)"""
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_documents(self, db: AsyncSession) -> List[Document]:
        """Get all documents"""
        result = await db.execute(select(Document))
        return result.scalars().all()
    
    async def list_documents(
        self, 
        db: AsyncSession,
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[DocumentResponse]:
        """List documents for a specific user with pagination"""
        result = await db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()
        
        # Convert to response format
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                uploaded_at=doc.uploaded_at,
                file_size=doc.file_size,
                content_hash=doc.content_hash,
                processed_summary=doc.processed_summary,
                step_tasks=doc.step_tasks
            )
            for doc in documents
        ]
    
    async def delete_document(self, document_id: int, db: AsyncSession, user_id: int) -> bool:
        """Delete document and all related data (only if owned by user)"""
        document = await self._get_document_raw(document_id, db, user_id)
        if not document:
            return False
        
        # Import required models
        from app.database import OnboardingSession, StepCompletion
        
        # Get all onboarding sessions that reference this document
        sessions_result = await db.execute(
            select(OnboardingSession).where(OnboardingSession.document_id == document_id)
        )
        sessions = sessions_result.scalars().all()
        session_ids = [session.id for session in sessions]
        
        # Delete all step completions for these sessions
        if session_ids:
            completions_result = await db.execute(
                select(StepCompletion).where(StepCompletion.session_id.in_(session_ids))
            )
            completions = completions_result.scalars().all()
            for completion in completions:
                await db.delete(completion)
            logger.info(f"Deleted {len(completions)} step completions")
        
        # Delete all onboarding sessions
        for session in sessions:
            await db.delete(session)
        logger.info(f"Deleted {len(sessions)} onboarding sessions")
        
        # Finally, delete the document
        await db.delete(document)
        await db.commit()
        logger.info(f"Document {document_id} and all related data deleted successfully")
        return True
    
    async def update_processed_content(
        self,
        document_id: int,
        summary: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        db: AsyncSession,
        user_id: int
    ) -> Optional[Document]:
        """Update document with processed content"""
        document = await self._get_document_raw(document_id, db, user_id)
        
        if document:
            document.processed_summary = summary
            document.step_tasks = tasks
            await db.commit()
            await db.refresh(document)
            logger.info(f"Updated document {document_id} with processed content")
        
        return document
    
    async def _get_document_by_hash_and_user(self, db: AsyncSession, content_hash: str, user_id: int) -> Optional[Document]:
        """Get document by content hash and user for deduplication"""
        result = await db.execute(
            select(Document).where(Document.content_hash == content_hash, Document.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    def get_document_stats(self, document: DocumentResponse) -> Dict[str, Any]:
        """Get document statistics"""
        return {
            'id': document.id,
            'filename': document.filename,
            'file_size': document.file_size,
            'uploaded_at': document.uploaded_at
        }
    
    async def get_scaledown_ai_health(self) -> Dict[str, Any]:
        """Check Gemini AI health status"""
        if not self.gemini_client:
            return {
                'status': 'unavailable',
                'message': 'Gemini AI client not initialized',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            # Simple health check - just verify the client is initialized
            return {
                'status': 'healthy',
                'message': 'Gemini AI client is ready',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global service instance
scaledown_service = ScaleDownService()
