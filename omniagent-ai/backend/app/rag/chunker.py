from typing import List
import re
import structlog

log = structlog.get_logger("chunker")


def chunk_text(text: str, size: int = 800, overlap: int = 120) -> List[str]:
    """Basic character-based chunking"""
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    out, i = [], 0
    while i < len(text):
        out.append(text[i : i + size])
        i += size - overlap
    return out


def semantic_chunk_text(text: str, max_chunk_size: int = 1000) -> List[str]:
    """Smarter semantic chunking using paragraphs and sentences"""
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    
    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # Split paragraph into sentences if too long
        sentences = re.split(r'(?<=[.!?])\s+', para)
        
        for sentence in sentences:
            potential = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = potential
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    log.info("chunks.created", count=len(chunks), total_size=len(text))
    return chunks


def chunk_pdf_text(text: str, metadata: dict = None) -> List[dict]:
    """Chunk text with metadata (for PDFs)"""
    chunks = semantic_chunk_text(text)
    
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            "content": chunk,
            "chunk_index": i,
            "metadata": {
                **(metadata or {}),
                "chunk_number": i,
                "total_chunks": len(chunks)
            }
        })
    
    return result
