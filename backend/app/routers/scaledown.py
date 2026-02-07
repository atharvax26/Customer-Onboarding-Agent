"""
ScaleDown Engine router for document processing
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.database import get_db, User
from app.schemas import DocumentResponse, DocumentUploadResponse, ErrorResponse, ProcessedDocumentResponse
from app.services.scaledown_service import ScaleDownService
from app.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()
scaledown_service = ScaleDownService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF or text)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and validate document for processing
    
    Accepts PDF and text files up to 10MB.
    Validates file format, extracts content, and stores in database.
    """
    try:
        document = await scaledown_service.upload_and_validate_document(file, db, current_user.id)
        
        return DocumentUploadResponse(
            message=f"Document '{document.filename}' uploaded successfully",
            document_id=document.id,
            processing_status="uploaded"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during document upload: {str(e)}"
        )


@router.post("/upload-and-process", response_model=ProcessedDocumentResponse)
async def upload_and_process_document(
    file: UploadFile = File(..., description="Document file (PDF or text)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload, validate, and process document in one operation
    
    Accepts PDF and text files up to 10MB.
    Processes document through Claude API to generate summary and tasks.
    """
    try:
        logger.info(f"User {current_user.id} uploading document: {file.filename}")
        result = await scaledown_service.upload_and_process_document(file, db, current_user.id)
        logger.info(f"Document {result.id} processed successfully for user {current_user.id}")
        return result
    
    except HTTPException as he:
        logger.error(f"HTTP error during upload/process: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during document processing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during document processing: {str(e)}"
        )


@router.post("/documents/{document_id}/process", response_model=ProcessedDocumentResponse)
async def process_existing_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process existing document through Claude API
    
    Generates summary and actionable tasks from document content.
    Returns cached result if document was already processed.
    """
    try:
        result = await scaledown_service.process_document_with_scaledown_ai(document_id, db, current_user.id)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during document processing: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of documents to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all uploaded documents for the current user with pagination
    
    Returns documents ordered by upload date (newest first).
    """
    try:
        documents = await scaledown_service.list_documents(db, current_user.id, skip=skip, limit=limit)
        return documents
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific document by ID (only if owned by current user)
    
    Returns document details including processing status and content.
    """
    try:
        document = await scaledown_service.get_document(document_id, db, current_user.id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete document by ID (only if owned by current user)
    
    Removes document and all associated data from the system.
    """
    try:
        deleted = await scaledown_service.delete_document(document_id, db, current_user.id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        return {"message": f"Document {document_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/documents/{document_id}/stats")
async def get_document_stats(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get document statistics and metadata (only if owned by current user)
    
    Returns processing status, file size, content length, and other metrics.
    """
    try:
        document = await scaledown_service.get_document(document_id, db, current_user.id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID {document_id} not found"
            )
        
        stats = scaledown_service.get_document_stats(document)
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document stats: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Check ScaleDown Engine health status
    
    Returns system health and Claude API connectivity status.
    """
    try:
        scaledown_ai_health = await scaledown_service.get_scaledown_ai_health()
        
        return {
            "status": "healthy" if scaledown_ai_health.get("status") == "healthy" else "degraded",
            "service": "ScaleDown Engine",
            "scaledown_ai_api": scaledown_ai_health,
            "timestamp": scaledown_ai_health.get("timestamp"),
            "gemini_available": scaledown_service.gemini_client is not None
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "ScaleDown Engine",
            "error": str(e),
            "scaledown_ai_api": {"status": "unknown"},
            "gemini_available": False
        }