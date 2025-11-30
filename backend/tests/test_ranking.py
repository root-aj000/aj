"""
Unit Tests for Hybrid Ranking
"""

import pytest
from src.retrieval.ranking import HybridRanker


class TestHybridRanker:
    """Test suite for HybridRanker."""
    
    def test_initialization(self):
        """Test ranker initialization."""
        ranker = HybridRanker()
        
        assert ranker.use_graph is True
        assert ranker.use_health is True
        assert ranker.use_recency is True
    
    def test_rank_with_semantic_only(self):
        """Test ranking with only semantic scores."""
        ranker = HybridRanker(use_graph=False, use_health=False, use_recency=False)
        
        results = [
            {'chunk_id': 'c1', 'score': 0.9},
            {'chunk_id': 'c2', 'score': 0.7},
            {'chunk_id': 'c3', 'score': 0.8},
        ]
        
        ranked = ranker.rank(results)
        
        assert ranked[0]['chunk_id'] == 'c1'  # Highest score first
        assert ranked[1]['chunk_id'] == 'c3'
        assert ranked[2]['chunk_id'] == 'c2'
    
    def test_rank_with_graph_boost(self):
        """Test ranking with graph relevance boost."""
        ranker = HybridRanker(use_graph=True, use_health=False, use_recency=False)
        
        results = [
            {'chunk_id': 'c1', 'score': 0.7},
            {'chunk_id': 'c2', 'score': 0.9},
        ]
        
        graph_scores = {
            'c1': 1.0,  # Very relevant in graph
            'c2': 0.0,  # Not relevant in graph
        }
        
        ranked = ranker.rank(results, graph_scores=graph_scores)
        
        # c1 should rank higher despite lower semantic score
        assert ranked[0]['chunk_id'] == 'c1'
    
    def test_rank_with_health_scores(self):
        """Test ranking with code health consideration."""
        ranker = HybridRanker(use_graph=False, use_health=True, use_recency=False)
        
        results = [
            {'chunk_id': 'c1', 'file_path': 'good.py', 'score': 0.8},
            {'chunk_id': 'c2', 'file_path': 'bad.py', 'score': 0.8},
        ]
        
        health_scores = {
            'good.py': 90.0,
            'bad.py': 30.0,
        }
        
        ranked = ranker.rank(results, health_scores=health_scores)
        
        # Good health file should rank higher
        assert ranked[0]['file_path'] == 'good.py'
    
    def test_deduplication(self):
        """Test duplicate chunk removal."""
        ranker = HybridRanker()
        
        results = [
            {'chunk_id': 'c1', 'file_path': 'test.py', 'start_line': 1, 'end_line': 10, 'score': 0.9},
            {'chunk_id': 'c2', 'file_path': 'test.py', 'start_line': 5, 'end_line': 15, 'score': 0.8},  # Overlaps
            {'chunk_id': 'c3', 'file_path': 'other.py', 'start_line': 1, 'end_line': 10, 'score': 0.7},
        ]
        
        deduplicated = ranker.deduplicate(results)
        
        # Should remove c2 as it overlaps with c1
        assert len(deduplicated) == 2
        assert any(r['chunk_id'] == 'c1' for r in deduplicated)
        assert any(r['chunk_id'] == 'c3' for r in deduplicated)
    
    def test_normalized_scores(self):
        """Test score normalization."""
        ranker = HybridRanker()
        
        results = [
            {'chunk_id': 'c1', 'score': 0.9},
            {'chunk_id': 'c2', 'score': 0.5},
        ]
        
        ranked = ranker.rank(results, normalize=True)
        
        assert 'normalized_score' in ranked[0]
        assert ranked[0]['normalized_score'] == 1.0  # Top score normalized to 1.0
        assert ranked[1]['normalized_score'] == 0.0  # Bottom score normalized to 0.0
