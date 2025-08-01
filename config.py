import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "LLM Query-Retrieval System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # For Vercel - use in-memory storage
    USE_MEMORY_STORAGE: bool = True
    
    # Database settings - use PostgreSQL for production
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    
    # Gemini API settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    EMBEDDING_MODEL: str = "text-embedding-004"
    
    # Vector store settings
    VECTOR_DIMENSION: int = 768
    USE_PINECONE: bool = False
    
    # Document processing settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # Reduced to 10MB for serverless
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".txt"]
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
