"""
Embedding Service

Generates embeddings using BGE-M3 model (local).
"""

from typing import List, Union, Optional
import numpy as np
import logging
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import torch
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("Warning: sentence-transformers not installed")

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Local embedding generation using BGE-M3.
    """
    
    def __init__(self, model_path: str, use_gpu: bool = True):
        """
        Initialize embedding service.
        
        Args:
            model_path: Path to local BGE-M3 model
            use_gpu: Whether to use GPU if available
        """
        if not HAS_EMBEDDINGS:
            raise RuntimeError("sentence-transformers not installed")
        
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}. Run: python models/download_bge_m3.py")
        
        # Determine device
        if use_gpu and torch.cuda.is_available():
            self.device = 'cuda'
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            self.device = 'cpu'
            logger.info("Using CPU for embeddings")
        
        # Load model
        logger.info(f"Loading BGE-M3 model from {model_path}...")
        self.model = SentenceTransformer(str(self.model_path))
        self.model.to(self.device)
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        
        # Cache for repeated texts
        self._cache: dict[str, np.ndarray] = {}
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for processing
            normalize: Whether to L2 normalize embeddings
            use_cache: Whether to use cache for repeated texts
        
        Returns:
            Numpy array of embeddings (single or batch)
        """
        # Handle single text
        single_text = isinstance(texts, str)
        if single_text:
            texts = [texts]
        
        # Check cache
        if use_cache:
            embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(texts):
                if text in self._cache:
                    embeddings.append(self._cache[text])
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self.model.encode(
                    uncached_texts,
                    batch_size=batch_size,
                    normalize_embeddings=normalize,
                    show_progress_bar=False
                )
                
                # Cache new embeddings
                for text, emb in zip(uncached_texts, new_embeddings):
                    self._cache[text] = emb
                
                # Merge cached and new embeddings in correct order
                result = [None] * len(texts)
                
                # Fill cached
                cached_idx = 0
                for i in range(len(texts)):
                    if i not in uncached_indices:
                        result[i] = embeddings[cached_idx]
                        cached_idx += 1
                
                # Fill uncached
                for i, emb in zip(uncached_indices, new_embeddings):
                    result[i] = emb
                
                embeddings = np.array(result)
            else:
                embeddings = np.array(embeddings)
        else:
            # Direct encoding without cache
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
        
        # Return single embedding if single text
        if single_text:
            return embeddings[0]
        
        return embeddings
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """Convenience method for batch encoding."""
        return self.encode(texts, batch_size=batch_size, normalize=normalize, use_cache=False)
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Cosine similarity score
        """
        emb1 = self.encode(text1, normalize=True)
        emb2 = self.encode(text2, normalize=True)
        
        return float(np.dot(emb1, emb2))
    
    def clear_cache(self):
        """Clear embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_size(self) -> int:
        """Get number of cached embeddings."""
        return len(self._cache)


def main():
    """CLI entry point for testing."""
    import sys
    from ..app.config import get_settings
    
    settings = get_settings()
    
    # Initialize service
    service = EmbeddingService(
        model_path=settings.embedding_model_path,
        use_gpu=True
    )
    
    # Test encoding
    test_texts = [
        "This is a test function.",
        "def process_data(input: str) -> dict:",
        "Calculate the sum of two numbers."
    ]
    
    print(f"\n🔢 Generating embeddings for {len(test_texts)} texts...")
    
    embeddings = service.encode(test_texts)
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"   Embedding shape: {embeddings[0].shape}")
    print(f"   Dimension: {service.embedding_dim}")
    
    # Test similarity
    sim = service.similarity(test_texts[0], test_texts[1])
    print(f"\n📊 Similarity between first two texts: {sim:.4f}")
    
    # Cache info
    print(f"\n💾 Cache size: {service.get_cache_size()}")


if __name__ == "__main__":
    main()
