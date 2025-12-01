"""
Indexing API Routes

Endpoints for code indexing operations.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import uuid
import os
from pathlib import Path

from ..config import get_settings
from ...indexing.walker import FileWalker
from ...indexing.ast_parser import ASTParser
from ...indexing.chunker import CodeChunker
from ...embeddings.embedding_service import EmbeddingService
from ...graphs.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter()


class IndexRequest(BaseModel):
    """Request model for indexing."""
    repo_path: Optional[str] = None  # If None, use settings default
    force_reindex: bool = False


class IndexStatus(BaseModel):
    """Status model for indexing."""
    session_id: str
    status: str
    progress: float
    message: str


# Global state for tracking indexing sessions
indexing_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/start")
async def start_indexing(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Start indexing a repository.
    
    Args:
        request: Indexing request
        background_tasks: FastAPI background tasks
    
    Returns:
        Session information
    """
    settings = get_settings()
    
    # Determine repo path
    repo_path = request.repo_path or settings.target_repo_path
    
    if not repo_path:
        raise HTTPException(
            status_code=400,
            detail="Repository path not provided and TARGET_REPO_PATH not set in environment"
        )
    
    # Validate path exists
    if not os.path.exists(repo_path):
        raise HTTPException(
            status_code=400,
            detail=f"Repository path does not exist: {repo_path}"
        )
    
    session_id = str(uuid.uuid4())
    
    # Initialize session
    indexing_sessions[session_id] = {
        'status': 'started',
        'progress': 0.0,
        'repo_path': repo_path,
        'message': 'Initializing...'
    }
    
    # Start indexing in background
    background_tasks.add_task(
        run_indexing,
        session_id,
        repo_path,
        request.force_reindex
    )
    
    logger.info(f"Started indexing session {session_id} for {repo_path}")
    
    return {
        'session_id': session_id,
        'status': 'started',
        'message': 'Indexing started',
        'repo_path': repo_path
    }


@router.get("/status/{session_id}")
async def get_indexing_status(session_id: str):
    """Get indexing status for a session."""
    if session_id not in indexing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = indexing_sessions[session_id]
    
    return {
        'session_id': session_id,
        'status': session.get('status', 'unknown'),
        'progress': session.get('progress', 0.0),
        'message': session.get('message', ''),
        'files_processed': session.get('files_processed', 0),
        'total_files': session.get('total_files', 0)
    }


@router.get("/stats")
async def get_index_stats():
    """Get indexing statistics."""
    try:
        settings = get_settings()
        
        # Initialize components
        neo4j_client = None
        stats = {
            'total_files': 0,
            'total_functions': 0,
            'total_chunks': 0,
            'vector_count': 0,
            'graph_nodes': 0,
            'graph_relationships': 0
        }
        
        # Try to get Neo4j stats
        try:
            neo4j_client = Neo4jClient(
                uri=settings.neo4j_url,
                username=settings.neo4j_username,
                password=settings.neo4j_password
            )
            
            # Query node counts
            with neo4j_client.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                stats['graph_nodes'] = result.single()['count']
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                stats['graph_relationships'] = result.single()['count']
                
                result = session.run("MATCH (f:Function) RETURN count(f) as count")
                stats['total_functions'] = result.single()['count']
                
                result = session.run("MATCH (file:File) RETURN count(file) as count")
                stats['total_files'] = result.single()['count']
        
        except Exception as e:
            logger.warning(f"Could not get Neo4j stats: {e}")
        
        finally:
            if neo4j_client:
                neo4j_client.close()
        
        # Try to get vector DB stats
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            chroma_client = chromadb.PersistentClient(
                path=str(settings.vector_db_path),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            collections = chroma_client.list_collections()
            for collection in collections:
                stats['vector_count'] += collection.count()
        
        except Exception as e:
            logger.warning(f"Could not get vector DB stats: {e}")
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            'total_files': 0,
            'total_functions': 0,
            'total_chunks': 0,
            'vector_count': 0,
            'graph_nodes': 0,
            'graph_relationships': 0,
            'error': str(e)
        }


async def run_indexing(session_id: str, repo_path: str, force_reindex: bool):
    """
    Run indexing pipeline.
    
    This is a background task that orchestrates the entire indexing process.
    """
    settings = get_settings()
    walker = None
    ast_parser = None
    chunker = None
    embedding_gen = None
    neo4j_client = None
    
    try:
        # Update status
        indexing_sessions[session_id]['status'] = 'running'
        indexing_sessions[session_id]['message'] = 'Walking directory tree...'
        indexing_sessions[session_id]['progress'] = 0.05
        
        logger.info(f"[{session_id}] Starting file walk of {repo_path}")
        
        # Step 1: File walking
        walker = FileWalker(repo_path)
        files = walker.walk()
        
        total_files = len(files)
        indexing_sessions[session_id]['total_files'] = total_files
        indexing_sessions[session_id]['files_processed'] = 0
        
        logger.info(f"[{session_id}] Found {total_files} files")
        
        indexing_sessions[session_id]['message'] = f'Found {total_files} files. Parsing...'
        indexing_sessions[session_id]['progress'] = 0.1
        
        # Step 2: Initialize components
        ast_parser = ASTParser()
        chunker = CodeChunker()
        
        # Initialize embedding service
        embedding_service = EmbeddingService(
            model_path=settings.embedding_model_path,
            use_gpu=True
        )
        
        neo4j_client = Neo4jClient(
            uri=settings.neo4j_url,
            username=settings.neo4j_username,
            password=settings.neo4j_password
        )
        
        # Import vector DB
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        chroma_client = chromadb.PersistentClient(
            path=str(settings.vector_db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            collection = chroma_client.get_collection("code_chunks")
            if force_reindex:
                chroma_client.delete_collection("code_chunks")
                collection = chroma_client.create_collection("code_chunks")
        except:
            collection = chroma_client.create_collection("code_chunks")
        
        logger.info(f"[{session_id}] Initialized all components")
        
        # Step 3: Process files
        for idx, file_metadata in enumerate(files):
            try:
                # Extract actual file path from FileMetadata object
                file_path = file_metadata.path if hasattr(file_metadata, 'path') else str(file_metadata)
                
                indexing_sessions[session_id]['message'] = f'Processing {Path(file_path).name}...'
                indexing_sessions[session_id]['progress'] = 0.1 + (0.8 * idx / total_files)
                indexing_sessions[session_id]['files_processed'] = idx + 1
                
                # Parse AST
                ast_result = ast_parser.parse_file(file_path)
                
                if not ast_result or 'functions' not in ast_result:
                    continue
                
                # Create file node in graph
                with neo4j_client.driver.session() as session:
                    session.run(
                        """
                        MERGE (f:File {path: $path})
                        SET f.name = $name,
                            f.extension = $extension
                        """,
                        path=file_path,
                        name=Path(file_path).name,
                        extension=Path(file_path).suffix
                    )
                
                # Process functions
                for func in ast_result.get('functions', []):
                    # Create function node
                    with neo4j_client.driver.session() as session:
                        session.run(
                            """
                            MATCH (f:File {path: $file_path})
                            MERGE (fn:Function {name: $name, file: $file_path})
                            SET fn.start_line = $start_line,
                                fn.end_line = $end_line,
                                fn.code = $code
                            MERGE (f)-[:CONTAINS]->(fn)
                            """,
                            file_path=file_path,
                            name=func.get('name', ''),
                            start_line=func.get('lineno', 0),
                            end_line=func.get('end_lineno', 0),
                            code=func.get('code', '')
                        )
                
                # Chunk the file
                chunks = chunker.chunk_file(file_path, ast_result)
                
                # Generate embeddings and store
                for chunk_idx, chunk in enumerate(chunks):
                    try:
                        # Generate embedding
                        embedding = embedding_service.encode(chunk.get('content', ''))
                        
                        # Store in vector DB
                        collection.add(
                            ids=[f"{file_path}_{chunk_idx}"],
                            embeddings=[embedding],
                            metadatas=[{
                                "file_path": file_path,
                                "chunk_index": chunk_idx,
                                "start_line": chunk.get('start_line', 0),
                                "end_line": chunk.get('end_line', 0)
                            }],
                            documents=[chunk.get('content', '')]
                        )
                    
                    except Exception as e:
                        logger.warning(f"Failed to process chunk {chunk_idx} of {file_path}: {e}")
            
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                continue
        
        # Complete
        indexing_sessions[session_id]['status'] = 'completed'
        indexing_sessions[session_id]['progress'] = 1.0
        indexing_sessions[session_id]['message'] = f'Indexing complete! Processed {total_files} files.'
        
        logger.info(f"[{session_id}] Indexing completed successfully")
    
    except Exception as e:
        logger.error(f"[{session_id}] Indexing failed: {e}", exc_info=True)
        indexing_sessions[session_id]['status'] = 'failed'
        indexing_sessions[session_id]['message'] = f"Error: {str(e)}"
    
    finally:
        # Clean up
        if neo4j_client:
            neo4j_client.close()
