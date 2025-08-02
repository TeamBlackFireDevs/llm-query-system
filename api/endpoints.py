from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import time
from datetime import datetime

from database import get_db
from models.pydantic_models import (
    QueryRequest,
    QueryResponse,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentSummaryResponse,
    HealthResponse,
    ErrorResponse,
    PydanticDocument
)
from models.database_models import Document, DocumentChunk
from services.document_processor import DocumentProcessor
from services.query_engine import QueryEngine
from services.vector_store import VectorStore
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
document_processor = DocumentProcessor()
query_engine = QueryEngine()
vector_store = VectorStore()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    start_time = time.time()
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Check file type
        file_extension = file.filename.split('.')[-1].lower()
        if f".{file_extension}" not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed types: {settings.ALLOWED_FILE_TYPES}"
            )
        
        # Process document
        document = await document_processor.process_document(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            db=db
        )
        
        # Add chunks to vector store
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).all()
        if chunks:
            await vector_store.add_document_chunks(chunks, db)
        
        processing_time = time.time() - start_time
        
        return DocumentUploadResponse(
            message=f"Document processed successfully with {len(chunks)} chunks",
            document_id=document.id,
            filename=document.filename,
            chunks_created=len(chunks),
            file_size=document.file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    query_request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Query documents using natural language"""
    try:
        # Validate query
        if not query_request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        # Process query
        response = await query_engine.process_query(query_request, db)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all uploaded documents"""
    try:
        # Get documents with pagination
        documents = db.query(Document).offset(skip).limit(limit).all()
        total_count = db.query(Document).count()
        
        # Convert to response format
        document_infos = []
        for doc in documents:
            doc_info = PydanticDocument(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                file_path=doc.file_path,
                upload_timestamp=doc.upload_timestamp
            )
            document_infos.append(doc_info)
        
        return DocumentListResponse(
            documents=document_infos,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get specific document information"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get document summary
        summary = await query_engine.get_document_summary(document_id, db)
        
        doc_info = PydanticDocument(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            file_path=document.file_path,
            upload_timestamp=document.upload_timestamp
        )
        
        return {
            "document": doc_info,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document: {str(e)}"
        )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Delete a document and its chunks"""
    try:
        # Check if document exists
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Remove from vector store
        await vector_store.remove_document_chunks(document_id, db)
        
        # Delete document and chunks
        success = await document_processor.delete_document(document_id, db)
        
        if success:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_status = "healthy"
        
        # Check vector store
        vector_stats = vector_store.get_index_stats()
        vector_status = "healthy" if vector_stats["total_vectors"] >= 0 else "unhealthy"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.0.0"
        )

@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        # Document statistics
        total_documents = db.query(Document).count()
        
        # Chunk statistics
        total_chunks = db.query(DocumentChunk).count()
        
        # Vector store statistics
        vector_stats = vector_store.get_index_stats()
        
        return {
            "documents": {
                "total": total_documents
            },
            "chunks": {
                "total": total_chunks
            },
            "vector_store": vector_stats,
            "system": {
                "version": "1.0.0",
                "max_file_size": settings.MAX_FILE_SIZE,
                "allowed_file_types": settings.ALLOWED_FILE_TYPES
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system stats: {str(e)}"
        ) 