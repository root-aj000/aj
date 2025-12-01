"""
Chat API Routes

Endpoints for chat interactions with streaming support.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio

from ..config import get_settings
from ...reasoning.llm_client import LLMClient
from ...embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize clients lazily
_llm_client: Optional[LLMClient] = None
_embedding_service: Optional[EmbeddingService] = None
_chroma_client = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _llm_client
    if _llm_client is None:
        settings = get_settings()
        _llm_client = LLMClient(
            api_key=settings.gemini_api_key,
            model_name=settings.llm_model_type
        )
    return _llm_client


def get_embedding_service() -> Optional[EmbeddingService]:
    """Get or create embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        try:
            settings = get_settings()
            _embedding_service = EmbeddingService(
                model_path=settings.embedding_model_path,
                use_gpu=True
            )
        except Exception as e:
            logger.warning(f"Could not initialize embedding service: {e}")
            return None
    return _embedding_service


def get_chroma_client():
    """Get or create ChromaDB client instance."""
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            settings = get_settings()
            _chroma_client = chromadb.PersistentClient(
                path=str(settings.vector_db_path),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        except Exception as e:
            logger.warning(f"Could not initialize ChromaDB: {e}")
            return None
    return _chroma_client


class Message(BaseModel):
    """Chat message model."""
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[Message]
    stream: bool = False
    temperature: float = 0.7
    session_id: Optional[str] = None
    use_context: bool = True  # Whether to use codebase context


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    session_id: str
    usage: Dict[str, int]


@router.post("/completion")
async def chat_completion(request: ChatRequest):
    """
    Generate chat completion.
    
    Args:
        request: Chat request
    
    Returns:
        Chat response or streaming response
    """
    if request.stream:
        return StreamingResponse(
            stream_chat_response(request),
            media_type="text/event-stream"
        )
    
    # Non-streaming response
    try:
        llm_client = get_llm_client()
        
        # Build context if requested
        context = ""
        if request.use_context and len(request.messages) > 0:
            last_message = request.messages[-1].content
            
            # Try to retrieve relevant context from ChromaDB
            chroma_client = get_chroma_client()
            embedding_service = get_embedding_service()
            
            if chroma_client and embedding_service:
                try:
                    # Get collection
                    collection = chroma_client.get_collection("code_chunks")
                    
                    # Generate query embedding
                    query_embedding = embedding_service.encode(last_message)
                    
                    # Search for relevant chunks
                    results = collection.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=3
                    )
                    
                    if results and results['documents'] and len(results['documents']) > 0:
                        context = "\n\n**Relevant Code Context:**\n"
                        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                            file_path = metadata.get('file_path', 'unknown')
                            start_line = metadata.get('start_line', 0)
                            end_line = metadata.get('end_line', 0)
                            context += f"\n**File:** `{file_path}` (lines {start_line}-{end_line})\n```\n{doc}\n```\n"
                
                except Exception as e:
                    logger.warning(f"Context retrieval failed: {e}")
        
        # Convert messages to LLM format
        messages_for_llm = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Add context to the last user message if available
        if context and messages_for_llm:
            messages_for_llm[-1]["content"] += context
        
        # Generate response
        response = llm_client.chat(
            messages=messages_for_llm,
            temperature=request.temperature
        )
        
        if not response.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=f"LLM generation failed: {response.get('error', 'Unknown error')}"
            )
        
        return {
            'message': response['text'],
            'session_id': request.session_id or 'default',
            'usage': response.get('usage', {
                'total_tokens': 0,
                'prompt_tokens': 0,
                'completion_tokens': 0
            })
        }
    
    except Exception as e:
        logger.error(f"Chat completion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def stream_chat_response(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events.
    
    Yields:
        SSE formatted chunks
    """
    try:
        llm_client = get_llm_client()
        
        # Build context if requested
        context = ""
        if request.use_context and len(request.messages) > 0:
            last_message = request.messages[-1].content
            
            # Try to retrieve relevant context from ChromaDB
            chroma_client = get_chroma_client()
            embedding_service = get_embedding_service()
            
            if chroma_client and embedding_service:
                try:
                    # Get collection
                    collection = chroma_client.get_collection("code_chunks")
                    
                    # Generate query embedding
                    query_embedding = embedding_service.encode(last_message)
                    
                    # Search for relevant chunks
                    results = collection.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=3
                    )
                    
                    if results and results['documents'] and len(results['documents']) > 0:
                        context = "\n\n**Relevant Code Context:**\n"
                        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                            file_path = metadata.get('file_path', 'unknown')
                            start_line = metadata.get('start_line', 0)
                            end_line = metadata.get('end_line', 0)
                            context += f"\n**File:** `{file_path}` (lines {start_line}-{end_line})\n```\n{doc}\n```\n"
                
                except Exception as e:
                    logger.warning(f"Context retrieval failed: {e}")
        
        # Build prompt
        prompt = ""
        for msg in request.messages:
            prompt += f"{msg.role}: {msg.content}\n\n"
        
        if context:
            prompt += context
        
        # Stream response
        for chunk in llm_client.generate_streaming(
            prompt=prompt,
            temperature=request.temperature
        ):
            # SSE format
            data = json.dumps({'content': chunk})
            yield f"data: {data}\n\n"
            
            await asyncio.sleep(0)  # Yield control
        
        # End of stream
        yield "data: [DONE]\n\n"
    
    except Exception as e:
        logger.error(f"Streaming failed: {e}", exc_info=True)
        error_data = json.dumps({'error': str(e)})
        yield f"data: {error_data}\n\n"


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """
    Get chat history for a session.
    
    Args:
        session_id: Session ID
        limit: Maximum messages to return
    
    Returns:
        Chat history
    """
    # This would query error memory database
    return {
        'session_id': session_id,
        'messages': [],
        'total': 0
    }


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session."""
    # This would delete from database
    return {
        'session_id': session_id,
        'cleared': True
    }
