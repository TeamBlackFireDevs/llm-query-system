import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from services.gemini_service import GeminiService
from models.database_models import Document, DocumentChunk, QueryLog
from models.pydantic_models import QueryRequest, QueryResponse, DocumentChunk as PydanticDocumentChunk
from services.vector_store import VectorStore
from config import settings
import time

logger = logging.getLogger(__name__)

class QueryEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        self.gemini_service = GeminiService()
    
    async def process_query(self, query_request: QueryRequest, db: Session) -> QueryResponse:
        """Process user query and return relevant results"""
        start_time = time.time()
        
        try:
            # Search for similar chunks
            similar_chunks = await self.vector_store.search_similar_chunks(
                query=query_request.query,
                k=query_request.max_results,
                similarity_threshold=query_request.similarity_threshold,
                document_ids=query_request.document_ids,
                db=db
            )
            
            # Convert to response format
            result_chunks = []
            for chunk, similarity_score in similar_chunks:
                result_chunk = PydanticDocumentChunk(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    embedding=chunk.embedding,
                    similarity_score=similarity_score
                )
                result_chunks.append(result_chunk)
            
            processing_time = time.time() - start_time
            
            # Generate explanation if requested
            explanation = None
            if result_chunks:
                explanation = await self._generate_explanation(
                    query_request.query, 
                    result_chunks[:3]  # Use top 3 results for explanation
                )
            
            # Log query
            query_log = QueryLog(
                query_text=query_request.query,
                query_type="semantic",  # Default query type
                document_ids=query_request.document_ids,
                results_count=len(result_chunks),
                processing_time=processing_time,
                similarity_threshold=query_request.similarity_threshold
            )
            db.add(query_log)
            db.commit()
            
            response = QueryResponse(
                query=query_request.query,
                results=result_chunks,
                total_results=len(result_chunks),
                explanation=explanation
            )
            
            logger.info(f"Processed query '{query_request.query}' with {len(result_chunks)} results in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    async def _generate_explanation(self, query: str, top_chunks: List[PydanticDocumentChunk]) -> str:
        """Generate explanation using Gemini"""
        try:
            context_parts = []
            for i, chunk in enumerate(top_chunks, 1):
                context_parts.append(f"Result {i} (Score: {chunk.similarity_score:.3f}):\n{chunk.content[:500]}...")
            
            context = "\n\n".join(context_parts)
            
            prompt = f"""
Based on the following query and search results, provide a brief explanation of why these results are relevant:

Query: "{query}"

Search Results:
{context}

Please provide a concise explanation (2-3 sentences) of how these results relate to the query and what key information they contain.
"""
            
            return await self.gemini_service.generate_text(prompt, max_tokens=150)
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return "Unable to generate explanation for the search results."
    
    async def get_document_summary(self, document_id: str, db: Session) -> Optional[str]:
        """Generate summary for a specific document"""
        try:
            # Get document chunks
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).limit(5).all()  # First 5 chunks
            
            if not chunks:
                return None
            
            # Combine chunk content
            content = "\n".join([chunk.content for chunk in chunks])
            
            prompt = f"""
Please provide a concise summary of the following document content:

{content[:2000]}...

Summary should be 2-3 sentences highlighting the main topics and key information.
"""
            
            return await self.gemini_service.generate_text(prompt, max_tokens=200)
            
        except Exception as e:
            logger.error(f"Error generating document summary: {str(e)}")
            return None
    
    async def suggest_related_queries(self, query: str, results: List[PydanticDocumentChunk]) -> List[str]:
        """Suggest related queries based on current query and results"""
        try:
            if not results:
                return []
            
            # Use content from top results
            content_sample = "\n".join([chunk.content[:200] for chunk in results[:2]])
            
            prompt = f"""
Based on the original query and the document content found, suggest 3 related questions that a user might want to ask:

Original Query: "{query}"

Document Content Sample:
{content_sample}

Please provide 3 short, specific questions that would help explore this topic further.
Format as a simple list, one question per line.
"""
            
            response = await self.gemini_service.generate_text(prompt, max_tokens=150)
            suggestions = response.strip().split('\n')
            # Clean up suggestions
            suggestions = [s.strip('- ').strip() for s in suggestions if s.strip()]
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Error generating query suggestions: {str(e)}")
            return [] 