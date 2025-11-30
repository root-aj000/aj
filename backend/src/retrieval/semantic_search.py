"""
Semantic Search

Performs vector similarity search using FAISS.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import logging

from ..embeddings.vector_store import VectorStore
from ..embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SemanticSearch:
    """
    Semantic code search using vector embeddings.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService
    ):
        """
        Initialize semantic search.
        
        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
    
    def search(
        self,
        query: str,
        top_k: int = 50,
        filter_language: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar code.
        
        Args:
            query: Search query (natural language or code)
            top_k: Number of results to return
            filter_language: Optional language filter
            min_score: Minimum similarity score
        
        Returns:
            List of search results with metadata and scores
        """
        logger.info(f"Semantic search: '{query[:50]}...' (top_k={top_k})")
        
        # Generate query embedding
        query_embedding = self.embedding_service.encode(query, normalize=True)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding,
            k=top_k,
            return_scores=True
        )
        
        # Filter by language if specified
        if filter_language:
            results = [r for r in results if r.get('language') == filter_language]
        
        # Filter by minimum score
        if min_score > 0:
            results = [r for r in results if r.get('score', 0) >= min_score]
        
        logger.info(f"Found {len(results)} results")
        
        return results
    
    def search_similar_chunks(
        self,
        chunk_id: str,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find chunks similar to a given chunk.
        
        Args:
            chunk_id: Chunk ID to find similar chunks for
            top_k: Number of results
        
        Returns:
            List of similar chunks
        """
        # Find the chunk in metadata
        chunk_metadata = None
        for idx, meta in self.vector_store.metadata.items():
            if meta.get('chunk_id') == chunk_id:
                chunk_metadata = meta
                break
        
        if not chunk_metadata:
            logger.warning(f"Chunk not found: {chunk_id}")
            return []
        
        # Get the embedding (we need to re-embed or store embeddings)
        # For now, search by the chunk's file context
        file_path = chunk_metadata.get('file_path', '')
        
        query = f"Code from {file_path}"
        
        return self.search(query, top_k=top_k)
    
    def search_by_function(
        self,
        function_name: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for code related to a function.
        
        Args:
            function_name: Function name
            top_k: Number of results
        
        Returns:
            List of related code chunks
        """
        query = f"Function: {function_name}"
        return self.search(query, top_k=top_k)
    
    def multi_query_search(
        self,
        queries: List[str],
        top_k_per_query: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform multiple searches in parallel.
        
        Args:
            queries: List of search queries
            top_k_per_query: Results per query
        
        Returns:
            Dictionary mapping queries to results
        """
        results = {}
        
        for query in queries:
            results[query] = self.search(query, top_k=top_k_per_query)
        
        return results
    
    def get_context_chunks(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        expand_lines: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get chunks overlapping with a specific code region.
        
        Args:
            file_path: File path
            start_line: Start line
            end_line: End line
            expand_lines: Lines to expand before/after
        
        Returns:
            List of overlapping chunks
        """
        # Search for chunks from the same file
        results = []
        
        for idx, meta in self.vector_store.metadata.items():
            if meta.get('file_path') != file_path:
                continue
            
            chunk_start = meta.get('start_line', 0)
            chunk_end = meta.get('end_line', 0)
            
            # Check for overlap (with expansion)
            if (chunk_start <= end_line + expand_lines and 
                chunk_end >= start_line - expand_lines):
                results.append(meta)
        
        # Sort by start line
        results.sort(key=lambda x: x.get('start_line', 0))
        
        return results


def main():
    """CLI entry point."""
    import sys
    from ..app.config import get_settings
    
    if len(sys.argv) < 2:
        print("Usage: python semantic_search.py '<search query>'")
        sys.exit(1)
    
    query = sys.argv[1]
    
    settings = get_settings()
    
    # Initialize services
    embedding_service = EmbeddingService(
        model_path=settings.embedding_model_path,
        use_gpu=True
    )
    
    vector_store = VectorStore(
        dimension=embedding_service.embedding_dim,
        index_path=settings.vector_db_path
    )
    
    # Load existing index
    vector_store.load()
    
    # Perform search
    search = SemanticSearch(vector_store, embedding_service)
    results = search.search(query, top_k=10)
    
    print(f"\n🔍 Search Results for: '{query}'")
    print(f"Found {len(results)} results\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('file_path', 'unknown')}")
        print(f"   Lines {result.get('start_line')}-{result.get('end_line')}")
        print(f"   Score: {result.get('score', 0):.4f}")
        print(f"   Language: {result.get('language', 'unknown')}")
        print()


if __name__ == "__main__":
    main()
