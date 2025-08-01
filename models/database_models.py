from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, Boolean
from sqlalchemy.sql import func
from database import Base
import uuid

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String, default="pending")
    processing_error = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    metadata = Column(JSON, default={})
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False)
    embedding_vector = Column(JSON, nullable=True)  # Store as JSON for SQLite compatibility
    metadata = Column(JSON, default={})
    created_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    query_type = Column(String, nullable=False)
    document_ids = Column(JSON, nullable=True)
    results_count = Column(Integer, default=0)
    processing_time = Column(Float, nullable=False)
    similarity_threshold = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String, nullable=True)  # For future user management
    
    def __repr__(self):
        return f"<QueryLog(id={self.id}, query_text={self.query_text[:50]}...)>"
