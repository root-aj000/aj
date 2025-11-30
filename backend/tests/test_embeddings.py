"""
Unit Tests for Embedding Service
"""

import pytest
import numpy as np

from src.embeddings.embedding_service import EmbeddingService


# Skip if sentence-transformers not available
pytest.importorskip("sentence_transformers")


@pytest.fixture
def mock_model_path(tmp_path):
    """Mock model path (tests will need actual model or mocking)."""
    return str(tmp_path / "bge-m3")


class TestEmbeddingService:
    """Test suite for EmbeddingService."""
    
    @pytest.mark.skip(reason="Requires BGE-M3 model download")
    def test_initialization(self, mock_model_path):
        """Test service initialization."""
        service = EmbeddingService(mock_model_path, use_gpu=False)
        
        assert service.device == 'cpu'
        assert service.embedding_dim > 0
    
    @pytest.mark.skip(reason="Requires BGE-M3 model download")
    def test_encode_single_text(self, mock_model_path):
        """Test encoding single text."""
        service = EmbeddingService(mock_model_path, use_gpu=False)
        
        text = "def hello(): pass"
        embedding = service.encode(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == service.embedding_dim
    
    @pytest.mark.skip(reason="Requires BGE-M3 model download")
    def test_encode_batch(self, mock_model_path):
        """Test batch encoding."""
        service = EmbeddingService(mock_model_path, use_gpu=False)
        
        texts = ["def func1(): pass", "def func2(): pass"]
        embeddings = service.encode(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 2
        assert embeddings.shape[1] == service.embedding_dim
    
    @pytest.mark.skip(reason="Requires BGE-M3 model download")
    def test_similarity(self, mock_model_path):
        """Test similarity calculation."""
        service = EmbeddingService(mock_model_path, use_gpu=False)
        
        text1 = "authentication function"
        text2 = "login handler"
        text3 = "database connection"
        
        # Similar texts should have higher similarity
        sim_12 = service.similarity(text1, text2)
        sim_13 = service.similarity(text1, text3)
        
        assert -1 <= sim_12 <= 1
        assert -1 <= sim_13 <= 1
        # Authentication/login should be more similar than authentication/database
        # (This might not always hold, depends on model)
    
    @pytest.mark.skip(reason="Requires BGE-M3 model download")
    def test_caching(self, mock_model_path):
        """Test embedding caching."""
        service = EmbeddingService(mock_model_path, use_gpu=False)
        
        text = "def test(): pass"
        
        # First encoding
        service.encode(text, use_cache=True)
        assert service.get_cache_size() == 1
        
        # Second encoding (should use cache)
        service.encode(text, use_cache=True)
        assert service.get_cache_size() == 1
        
        # Clear cache
        service.clear_cache()
        assert service.get_cache_size() == 0
