from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Change 'metadata' to 'file_metadata' to avoid conflict
    file_metadata = Column(Text, nullable=True)  # Changed from 'metadata'
    
    # Relationship
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # Store as JSON string
    
    # Relationship
    document = relationship("Document", back_populates="chunks")

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
