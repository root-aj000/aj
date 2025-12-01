"""
Search API Routes

Endpoints for semantic code search.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..config import get_settings
from ...embeddings.embedding_service import EmbeddingService
from ...graphs.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# Lazy initialization
_embedding_service: Optional[EmbeddingService] = None
_chroma_client = None
_neo4j_client: Optional[Neo4jClient] = None


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


def get_neo4j_client() -> Optional[Neo4jClient]:
    """Get or create Neo4j client instance."""
    global _neo4j_client
    if _neo4j_client is None:
        try:
            settings = get_settings()
            _neo4j_client = Neo4jClient(
                uri=settings.neo4j_url,
                username=settings.neo4j_username,
                password=settings.neo4j_password
            )
        except Exception as e:
            logger.warning(f"Could not initialize Neo4j: {e}")
            return None
    return _neo4j_client


class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    language: Optional[str] = None
    top_k: int = 20
    min_score: float = 0.0


class SearchResult(BaseModel):
    """Search result model."""
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    score: float
    language: str


@router.post("/semantic")
async def semantic_search(request: SearchRequest):
    """
    Perform semantic code search.
    
    Args:
        request: Search request
    
    Returns:
        Search results
    """
    try:
        chroma_client = get_chroma_client()
        embedding_service = get_embedding_service()
        
        if not chroma_client or not embedding_service:
            return {
                'query': request.query,
                'results': [],
                'total': 0,
                'error': 'Search services not available'
            }
        
        logger.info(f"Semantic search: '{request.query}' (top_k={request.top_k})")
        
        # Get collection
        collection = chroma_client.get_collection("code_chunks")
        
        # Generate query embedding
        query_embedding = embedding_service.encode(request.query)
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=request.top_k
        )
        
        # Format results
        formatted_results = []
        if results and results['documents'] and len(results['documents']) > 0:
            for idx, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity score (lower distance = higher similarity)
                score = 1.0 / (1.0 + distance)
                
                if score >= request.min_score:
                    formatted_results.append({
                        'chunk_id': results['ids'][0][idx],
                        'file_path': metadata.get('file_path', 'unknown'),
                        'start_line': metadata.get('start_line', 0),
                        'end_line': metadata.get('end_line', 0),
                        'content': doc,
                        'score': score,
                        'language': 'python'  # TODO: detect language from file extension
                    })
        
        return {
            'query': request.query,
            'results': formatted_results,
            'total': len(formatted_results)
        }
    
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return {
            'query': request.query,
            'results': [],
            'error': str(e)
        }


@router.get("/function/{function_name}")
async def search_function(function_name: str, file_path: Optional[str] = None):
    """
    Search for a specific function.
    
    Args:
        function_name: Function name to search for
        file_path: Optional file path filter
    
    Returns:
        Function information
    """
    try:
        neo4j_client = get_neo4j_client()
        
        if not neo4j_client:
            return {
                'function_name': function_name,
                'file_path': file_path,
                'found': False,
                'error': 'Neo4j not available'
            }
        
        # Query Neo4j for function
        with neo4j_client.driver.session() as session:
            query = """
            MATCH (fn:Function {name: $name})
            """
            
            params = {'name': function_name}
            
            if file_path:
                query += " WHERE fn.file = $file"
                params['file'] = file_path
            
            query += """
            RETURN fn.name as name, fn.file as file, 
                   fn.start_line as start_line, fn.end_line as end_line,
                   fn.code as code
            LIMIT 1
            """
            
            result = session.run(query, params)
            record = result.single()
            
            if record:
                return {
                    'function_name': record['name'],
                    'file_path': record['file'],
                    'start_line': record['start_line'],
                    'end_line': record['end_line'],
                    'code': record['code'],
                    'found': True
                }
            else:
                return {
                    'function_name': function_name,
                    'file_path': file_path,
                    'found': False
                }
    
    except Exception as e:
        logger.error(f"Function search failed: {e}", exc_info=True)
        return {
            'function_name': function_name,
            'file_path': file_path,
            'found': False,
            'error': str(e)
        }


@router.get("/file/{file_path:path}")
async def search_file(file_path: str):
    """
    Get all chunks for a file.
    
    Args:
        file_path: File path
    
    Returns:
        File chunks
    """
    try:
        chroma_client = get_chroma_client()
        
        if not chroma_client:
            return {
                'file_path': file_path,
                'chunks': [],
                'total': 0,
                'error': 'ChromaDB not available'
            }
        
        # Get collection
        collection = chroma_client.get_collection("code_chunks")
        
        # Query all chunks for this file
        results = collection.get(
            where={"file_path": file_path}
        )
        
        # Format results
        chunks = []
        if results and results['documents']:
            for idx, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                chunks.append({
                    'chunk_id': results['ids'][idx],
                    'content': doc,
                    'start_line': metadata.get('start_line', 0),
                    'end_line': metadata.get('end_line', 0),
                })
        
        # Sort by start line
        chunks.sort(key=lambda x: x['start_line'])
        
        return {
            'file_path': file_path,
            'chunks': chunks,
            'total': len(chunks)
        }
    
    except Exception as e:
        logger.error(f"File search failed: {e}", exc_info=True)
        return {
            'file_path': file_path,
            'chunks': [],
            'total': 0,
            'error': str(e)
        }
