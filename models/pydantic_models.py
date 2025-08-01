from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    EMAIL = "email"

class QueryType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"

class DocumentUploadRequest(BaseModel):
    filename: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = {}

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
    processing_time: float

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    document_ids: Optional[List[str]] = None
    query_type: QueryType = QueryType.SEMANTIC
    max_results: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_metadata: bool = True

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float

class QueryResponse(BaseModel):
    query: str
    results: List[DocumentChunk]
    total_results: int
    processing_time: float
    query_type: str
    explanation: Optional[str] = None

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    document_type: DocumentType
    file_size: int
    upload_timestamp: datetime
    processing_status: str
    chunk_count: int
    metadata: Dict[str, Any]

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_count: int

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    database_status: str
    vector_store_status: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime
    request_id: Optional[str] = None
