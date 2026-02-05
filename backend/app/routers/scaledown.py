"""
ScaleDown Engine router for document processing
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas import DocumentResponse, DocumentUploadResponse, ErrorResponse, ProcessedDocumentResponse
from app.services.scaledown_service import ScaleDownService

router = APIRouter()
scaledown_service = ScaleDownService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF or text)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and validate document for processing
    
    Accepts PDF and text files up to 10MB.
    Validates file format, extracts content, and stores in database.
    """
    try:
        document = await scaledown_service.upload_and_validate_document(file, db)
        
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
    db: AsyncSession = Depends(get_db)
):
    """
    Upload, validate, and process document in one operation
    
    Accepts PDF and text files up to 10MB.
    Processes document through Claude API to generate summary and tasks.
    """
    try:
        result = await scaledown_service.upload_and_process_document(file, db)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during document processing: {str(e)}"
        )


@router.post("/documents/{document_id}/process", response_model=ProcessedDocumentResponse)
async def process_existing_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Process existing document through Claude API
    
    Generates summary and actionable tasks from document content.
    Returns cached result if document was already processed.
    """
    try:
        result = await scaledown_service.process_document_with_claude(document_id, db)
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
    db: AsyncSession = Depends(get_db)
):
    """
    List all uploaded documents with pagination
    
    Returns documents ordered by upload date (newest first).
    """
    try:
        documents = await scaledown_service.list_documents(db, skip=skip, limit=limit)
        return documents
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific document by ID
    
    Returns document details including processing status and content.
    """
    try:
        document = await scaledown_service.get_document(document_id, db)
        
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
    db: AsyncSession = Depends(get_db)
):
    """
    Delete document by ID
    
    Removes document and all associated data from the system.
    """
    try:
        deleted = await scaledown_service.delete_document(document_id, db)
        
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get document statistics and metadata
    
    Returns processing status, file size, content length, and other metrics.
    """
    try:
        document = await scaledown_service.get_document(document_id, db)
        
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
        claude_health = await scaledown_service.get_claude_health()
        
        return {
            "status": "healthy",
            "service": "ScaleDown Engine",
            "claude_api": claude_health,
            "timestamp": claude_health.get("timestamp")
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ScaleDown Engine",
            "error": str(e),
            "claude_api": {"status": "unknown"}
        }