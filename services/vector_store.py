import numpy as np
import faiss
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from services.gemini_service import GeminiService
from sqlalchemy.orm import Session
from models.database_models import DocumentChunk
from config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.dimension = 768  # Gemini embedding dimension
        self.index_path = Path("vector_index")
        self.index_path.mkdir(exist_ok=True)
        
        # Initialize Gemini service
        self.gemini_service = GeminiService()
        
        # Initialize FAISS index
        self.index = None
        self.chunk_ids = []
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create new one"""
        index_file = self.index_path / "faiss_index.bin"
        metadata_file = self.index_path / "chunk_metadata.pkl"
        
        try:
            if index_file.exists() and metadata_file.exists():
                # Load existing index
                self.index = faiss.read_index(str(index_file))
                with open(metadata_file, 'rb') as f:
                    self.chunk_ids = pickle.load(f)
                logger.info(f"Loaded existing FAISS index with {len(self.chunk_ids)} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.chunk_ids = []
                logger.info("Created new FAISS index")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            # Create new index as fallback
            self.index = faiss.IndexFlatIP(self.dimension)
            self.chunk_ids = []
    
    def _save_index(self):
        """Save FAISS index and metadata"""
        try:
            index_file = self.index_path / "faiss_index.bin"
            metadata_file = self.index_path / "chunk_metadata.pkl"
            
            faiss.write_index(self.index, str(index_file))
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.chunk_ids, f)
            
            logger.info("FAISS index saved successfully")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Gemini API"""
        return await self.gemini_service.get_embedding(text)
    
    async def add_document_chunks(self, chunks: List[DocumentChunk], db: Session):
        """Add document chunks to vector store"""
        try:
            vectors = []
            chunk_ids = []
            
            for chunk in chunks:
                # Get embedding for chunk content
                embedding = await self.get_embedding(chunk.content)
                
                # Normalize embedding for cosine similarity
                embedding_array = np.array(embedding, dtype=np.float32)
                embedding_array = embedding_array / np.linalg.norm(embedding_array)
                
                vectors.append(embedding_array)
                chunk_ids.append(chunk.id)
                
                # Store embedding in database
                chunk.embedding_vector = embedding
                db.add(chunk)
            
            if vectors:
                # Add to FAISS index
                vectors_array = np.array(vectors)
                self.index.add(vectors_array)
                self.chunk_ids.extend(chunk_ids)
                
                # Save index
                self._save_index()
                
                # Commit database changes
                db.commit()
                
                logger.info(f"Added {len(vectors)} chunks to vector store")
        
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {str(e)}")
            db.rollback()
            raise
    
    async def search_similar_chunks(
        self, 
        query: str, 
        k: int = 5, 
        similarity_threshold: float = 0.7,
        document_ids: Optional[List[str]] = None,
        db: Session = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar chunks using vector similarity"""
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            query_vector = np.array(query_embedding, dtype=np.float32)
            query_vector = query_vector / np.linalg.norm(query_vector)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_vector.reshape(1, -1), k * 2)  # Get more results to filter
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                if score < similarity_threshold:  # Below threshold
                    continue
                
                chunk_id = self.chunk_ids[idx]
                
                # Get chunk from database
                chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
                if not chunk:
                    continue
                
                # Filter by document IDs if specified
                if document_ids and chunk.document_id not in document_ids:
                    continue
                
                results.append((chunk, float(score)))
                
                if len(results) >= k:
                    break
            
            logger.info(f"Found {len(results)} similar chunks for query")
            return results
        
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    async def remove_document_chunks(self, document_id: str, db: Session):
        """Remove document chunks from vector store"""
        try:
            # Get chunk IDs for the document
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
            chunk_ids_to_remove = [chunk.id for chunk in chunks]
            
            if not chunk_ids_to_remove:
                return
            
            # Find indices in FAISS index
            indices_to_remove = []
            for i, chunk_id in enumerate(self.chunk_ids):
                if chunk_id in chunk_ids_to_remove:
                    indices_to_remove.append(i)
            
            # Remove from FAISS index (rebuild index without removed vectors)
            if indices_to_remove:
                # Get all vectors except the ones to remove
                all_vectors = []
                remaining_chunk_ids = []
                
                for i in range(len(self.chunk_ids)):
                    if i not in indices_to_remove:
                        vector = self.index.reconstruct(i)
                        all_vectors.append(vector)
                        remaining_chunk_ids.append(self.chunk_ids[i])
                
                # Rebuild index
                self.index = faiss.IndexFlatIP(self.dimension)
                if all_vectors:
                    vectors_array = np.array(all_vectors)
                    self.index.add(vectors_array)
                
                self.chunk_ids = remaining_chunk_ids
                self._save_index()
                
                logger.info(f"Removed {len(indices_to_remove)} chunks from vector store")
        
        except Exception as e:
            logger.error(f"Error removing chunks from vector store: {str(e)}")
            raise
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": "FAISS IndexFlatIP",
            "chunk_count": len(self.chunk_ids)
        } 