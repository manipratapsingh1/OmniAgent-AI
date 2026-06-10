"""
Test chat endpoint with mock Ollama responses.
Use this if Ollama is not available for testing.
"""
import asyncio
from app.schemas.chat import ChatRequest, ChatResponse, Citation

async def test_fast_rag_mock():
    """Simulate a fast RAG response without needing Ollama"""
    print("\n🧪 Testing Fast RAG Endpoint (Mock)\n")
    
    # Mock response
    response = ChatResponse(
        conversation_id=1,
        message_id=1,
        content="Based on the OmniAgent documentation, OmniAgent AI is a multi-agent framework designed to handle complex reasoning tasks. It uses a chain of specialized agents (router, planner, research, tool, verifier, critic, summarizer) to process queries. The system supports RAG (Retrieval Augmented Generation) for document-based Q&A, with vectorized storage in Chroma and embedding generation through Ollama.",
        sources=[
            Citation(
                document_id=1,
                chunk_index=0,
                snippet="OmniAgent is a multi-agent AI framework..."
            ),
            Citation(
                document_id=2,
                chunk_index=1,
                snippet="Supports document retrieval and semantic search..."
            ),
        ],
        trace=[]
    )
    
    print("✓ Response received (mock)")
    print(f"  Content length: {len(response.content)} chars")
    print(f"  Sources found: {len(response.sources)}")
    print(f"\nAnswer preview:\n  {response.content[:150]}...\n")
    
    return response

if __name__ == "__main__":
    result = asyncio.run(test_fast_rag_mock())
    print("✓ Mock test passed!")
