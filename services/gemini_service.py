import google.generativeai as genai
import logging
from typing import List
from config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding using Gemini"""
        try:
            result = genai.embed_content(
                model=settings.EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error getting Gemini embedding: {str(e)}")
            return [0.0] * 768  # Gemini embedding dimension
            
    async def generate_text(self, prompt: str, max_tokens: int = 150) -> str:
        """Generate text using Gemini"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {str(e)}")
            return "Unable to generate response." 