from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    file_metadata: Optional[str] = None  # Changed from 'metadata'

class DocumentCreate(DocumentBase):
    file_path: str

class PydanticDocument(DocumentBase):
    id: int
    file_path: str
    upload_timestamp: datetime
    
    class Config:
        from_attributes = True

class DocumentChunkBase(BaseModel):
    chunk_index: int
    content: str

class DocumentChunkCreate(DocumentChunkBase):
    document_id: int
    embedding: Optional[str] = None

class PydanticDocumentChunk(DocumentChunkBase):
    id: int
    document_id: int
    embedding: Optional[str] = None
    similarity_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    query: str
    max_results: int = 5
    similarity_threshold: float = 0.7
    document_ids: Optional[List[int]] = None

class QueryResponse(BaseModel):
    query: str
    results: List[PydanticDocumentChunk]
    total_results: int
    explanation: Optional[str] = None
    suggested_queries: Optional[List[str]] = None
