"""
FAISS Vector Store

Manages vector storage and similarity search using FAISS.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
from pathlib import Path
import json
import pickle

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("Warning: faiss not installed")

logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS-based vector store for code chunks.
    """
    
    def __init__(self, dimension: int, index_path: Optional[str] = None):
        """
        Initialize vector store.
        
        Args:
            dimension: Embedding dimension
            index_path: Path to save/load index
        """
        if not HAS_FAISS:
            raise RuntimeError("faiss not installed")
        
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        
        # Create FAISS index (using IndexFlatIP for inner product/cosine similarity)
        self.index = faiss.IndexFlatIP(dimension)
        
        # Metadata storage (chunk_id -> metadata)
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self.id_counter = 0
        
        logger.info(f"Initialized FAISS index with dimension {dimension}")
        
        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load()
    
    def add(
        self,
        embeddings: np.ndarray,
        metadata_list: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Add embeddings to the index.
        
        Args:
            embeddings: Numpy array of embeddings (n x dimension)
            metadata_list: List of metadata dicts for each embedding
        
        Returns:
            List of assigned IDs
        """
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: {embeddings.shape[1]} != {self.dimension}")
        
        if len(metadata_list) != len(embeddings):
            raise ValueError("Number of embeddings and metadata must match")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        ids = []
        for metadata in metadata_list:
            self.metadata[self.id_counter] = metadata
            ids.append(self.id_counter)
            self.id_counter += 1
        
        logger.info(f"Added {len(embeddings)} embeddings to index")
        
        return ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding (1D array)
            k: Number of results to return
            return_scores: Whether to include similarity scores
        
        Returns:
            List of results with metadata and optional scores
        """
        # Reshape to 2D if needed
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, k)
        
        # Build results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # No more results
                break
            
            result = self.metadata.get(int(idx), {}).copy()
            
            if return_scores:
                result['score'] = float(scores[0][i])
            
            result['id'] = int(idx)
            results.append(result)
        
        return results
    
    def search_batch(
        self,
        query_embeddings: np.ndarray,
        k: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch search for multiple queries.
        
        Args:
            query_embeddings: Query embeddings (n x dimension)
            k: Number of results per query
        
        Returns:
            List of result lists
        """
        # Normalize queries
        faiss.normalize_L2(query_embeddings)
        
        # Search
        scores, indices = self.index.search(query_embeddings, k)
        
        # Build results for each query
        all_results = []
        
        for q_idx in range(len(query_embeddings)):
            results = []
            
            for i, idx in enumerate(indices[q_idx]):
                if idx == -1:
                    break
                
                result = self.metadata.get(int(idx), {}).copy()
                result['score'] = float(scores[q_idx][i])
                result['id'] = int(idx)
                results.append(result)
            
            all_results.append(results)
        
        return all_results
    
    def save(self, path: Optional[str] = None):
        """
        Save index and metadata to disk.
        
        Args:
            path: Optional path override
        """
        save_path = Path(path) if path else self.index_path
        
        if not save_path:
            raise ValueError("No save path specified")
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = str(save_path / "index.faiss")
        faiss.write_index(self.index, index_file)
        
        # Save metadata
        metadata_file = str(save_path / "metadata.pkl")
        with open(metadata_file, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'id_counter': self.id_counter,
                'dimension': self.dimension
            }, f)
        
        logger.info(f"Saved index to {save_path}")
    
    def load(self, path: Optional[str] = None):
        """
        Load index and metadata from disk.
        
        Args:
            path: Optional path override
        """
        load_path = Path(path) if path else self.index_path
        
        if not load_path:
            raise ValueError("No load path specified")
        
        # Load FAISS index
        index_file = str(load_path / "index.faiss")
        if Path(index_file).exists():
            self.index = faiss.read_index(index_file)
        else:
            logger.warning(f"Index file not found: {index_file}")
            return
        
        # Load metadata
        metadata_file = str(load_path / "metadata.pkl")
        if Path(metadata_file).exists():
            with open(metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.id_counter = data['id_counter']
                self.dimension = data['dimension']
        else:
            logger.warning(f"Metadata file not found: {metadata_file}")
        
        logger.info(f"Loaded index from {load_path}")
        logger.info(f"  Total vectors: {self.index.ntotal}")
        logger.info(f"  Metadata entries: {len(self.metadata)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'metadata_count': len(self.metadata),
            'index_type': type(self.index).__name__
        }
    
    def clear(self):
        """Clear the index and metadata."""
        self.index.reset()
        self.metadata.clear()
        self.id_counter = 0
        logger.info("Index cleared")


def main():
    """CLI entry point for testing."""
    import sys
    
    # Create test data
    dimension = 1024
    num_vectors = 100
    
    print(f"\n🔧 Creating FAISS index (dimension={dimension})...")
    
    store = VectorStore(dimension=dimension, index_path="./data/vector_db")
    
    # Generate random embeddings
    embeddings = np.random.randn(num_vectors, dimension).astype('float32')
    
    # Create metadata
    metadata = [
        {
            'chunk_id': f"chunk_{i}",
            'file': f"file_{i % 10}.py",
            'start_line': i * 10,
            'end_line': (i + 1) * 10
        }
        for i in range(num_vectors)
    ]
    
    # Add to index
    print(f"📥 Adding {num_vectors} vectors...")
    ids = store.add(embeddings, metadata)
    
    # Search
    query = np.random.randn(1, dimension).astype('float32')
    print(f"\n🔍 Searching (k=5)...")
    results = store.search(query, k=5)
    
    print(f"\n✅ Found {len(results)} results:")
    for r in results:
        print(f"  {r['chunk_id']} (score: {r['score']:.4f})")
    
    # Stats
    stats = store.get_stats()
    print(f"\n📊 Index Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
