import hashlib
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def generate_hash(content: str) -> str:
    """Generate MD5 hash for content"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-\'""]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text (simple implementation)"""
    if not text:
        return []
    
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
        'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'shall'
    }
    
    # Filter out stop words and count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 3:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in keywords[:max_keywords]]

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate if file type is allowed"""
    if not filename:
        return False
    
    file_extension = f".{filename.split('.')[-1].lower()}"
    return file_extension in allowed_types

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    if not filename:
        return "unnamed_file"
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename

def create_error_response(error: str, message: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": error,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id
    }

def log_performance(func_name: str, execution_time: float, **kwargs):
    """Log performance metrics"""
    logger.info(
        f"Performance: {func_name} executed in {execution_time:.3f}s",
        extra={
            "function": func_name,
            "execution_time": execution_time,
            **kwargs
        }
    )

def chunk_text_by_sentences(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Chunk text by sentences with overlap"""
    if not text:
        return []
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Check if adding this sentence would exceed chunk size
        if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                
                # Create overlap for next chunk
                words = current_chunk.split()
                if len(words) > overlap // 10:  # Approximate word overlap
                    overlap_text = " ".join(words[-(overlap // 10):])
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def extract_metadata_from_text(text: str) -> Dict[str, Any]:
    """Extract metadata from text content"""
    metadata = {}
    
    if not text:
        return metadata
    
    # Basic statistics
    metadata["character_count"] = len(text)
    metadata["word_count"] = len(text.split())
    metadata["sentence_count"] = len(re.split(r'[.!?]+', text))
    metadata["paragraph_count"] = len([p for p in text.split('\n\n') if p.strip()])
    
    # Extract potential dates
    date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
    dates = re.findall(date_pattern, text)
    if dates:
        metadata["dates_found"] = dates[:5]  # Limit to first 5 dates
    
    # Extract potential email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        metadata["emails_found"] = emails[:3]  # Limit to first 3 emails
    
    # Extract potential phone numbers
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b'
    phones = re.findall(phone_pattern, text)
    if phones:
        metadata["phones_found"] = phones[:3]  # Limit to first 3 phones
    
    # Extract keywords
    keywords = extract_keywords(text, max_keywords=5)
    if keywords:
        metadata["keywords"] = keywords
    
    return metadata

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely dump object to JSON string with fallback"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default 