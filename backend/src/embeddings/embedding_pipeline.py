"""
Embedding Pipeline

Orchestrates embedding generation for all code chunks.
"""

from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .embedding_service import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """
    Pipeline for embedding code chunks and storing in vector database.
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore
    ):
        """
        Initialize embedding pipeline.
        
        Args:
            embedding_service: Embedding service instance
            vector_store: Vector store instance
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def process_manifest(
        self,
        manifest: Dict[str, Any],
        batch_size: int = 32
    ) -> Dict[str, int]:
        """
        Process manifest and embed all chunks.
        
        Args:
            manifest: Indexing manifest
            batch_size: Batch size for embedding generation
        
        Returns:
            Statistics dictionary
        """
        logger.info("Starting embedding pipeline...")
        
        total_chunks = 0
        total_files = 0
        
        files = manifest.get('files', [])
        
        for file_data in files:
            chunks = file_data.get('chunks', [])
            
            if not chunks:
                continue
            
            total_files += 1
            
            # Extract chunk texts
            texts = [chunk['content'] for chunk in chunks]
            
            # Generate embeddings in batches
            logger.info(f"Processing {len(texts)} chunks from {file_data['relative_path']}")
            
            embeddings = self.embedding_service.encode_batch(
                texts,
                batch_size=batch_size,
                normalize=True
            )
            
            # Prepare metadata
            metadata_list = []
            for chunk in chunks:
                metadata = {
                    'chunk_id': chunk['chunk_id'],
                    'file_path': chunk['file_path'],
                    'start_line': chunk['start_line'],
                    'end_line': chunk['end_line'],
                    'language': chunk['language'],
                    'token_count': chunk['token_count']
                }
                metadata_list.append(metadata)
            
            # Add to vector store
            self.vector_store.add(embeddings, metadata_list)
            
            total_chunks += len(chunks)
        
        logger.info(f"Embedding pipeline complete")
        logger.info(f"  Files processed: {total_files}")
        logger.info(f"  Chunks embedded: {total_chunks}")
        
        return {
            'files_processed': total_files,
            'chunks_embedded': total_chunks
        }
    
    def embed_functions(
        self,
        manifest: Dict[str, Any],
        batch_size: int = 32
    ) -> int:
        """
        Generate and store function-level embeddings.
        
        Args:
            manifest: Indexing manifest
            batch_size: Batch size
        
        Returns:
            Number of functions embedded
        """
        logger.info("Embedding functions...")
        
        function_count = 0
        
        for file_data in manifest.get('files', []):
            functions = file_data.get('functions', [])
            
            if not functions:
                continue
            
            # For function embeddings, we'll use function signatures + docstrings
            # In production, we'd extract actual function content
            texts = [f"Function: {func['name']}" for func in functions]
            
            embeddings = self.embedding_service.encode_batch(texts, batch_size=batch_size)
            
            # Prepare metadata
            metadata_list = []
            for func in functions:
                metadata = {
                    'type': 'function',
                    'name': func['name'],
                    'file_path': file_data['path'],
                    'start_line': func['start_line'],
                    'end_line': func['end_line'],
                    'language': func.get('language', 'unknown')
                }
                metadata_list.append(metadata)
            
            self.vector_store.add(embeddings, metadata_list)
            function_count += len(functions)
        
        logger.info(f"Embedded {function_count} functions")
        
        return function_count
    
    def save(self):
        """Save vector store to disk."""
        self.vector_store.save()
        logger.info("Vector store saved")


def main():
    """CLI entry point."""
    import sys
    import json
    from ..app.config import get_settings
    
    if len(sys.argv) < 2:
        print("Usage: python embedding_pipeline.py <manifest.json>")
        sys.exit(1)
    
    manifest_path = sys.argv[1]
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
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
    
    # Run pipeline
    pipeline = EmbeddingPipeline(embedding_service, vector_store)
    
    stats = pipeline.process_manifest(manifest, batch_size=32)
    
    # Also embed functions
    func_count = pipeline.embed_functions(manifest, batch_size=32)
    
    # Save
    pipeline.save()
    
    print(f"\n✅ Embedding pipeline complete")
    print(f"   Files: {stats['files_processed']}")
    print(f"   Chunks: {stats['chunks_embedded']}")
    print(f"   Functions: {func_count}")
    print(f"\n💾 Saved to: {settings.vector_db_path}")


if __name__ == "__main__":
    main()
