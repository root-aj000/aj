"""
Hybrid Ranking

Combines semantic similarity, graph relevance, code health, and recency.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HybridRanker:
    """
    Rank code chunks using multiple signals.
    
    Ranking formula:
    score = 0.60 * semantic_similarity
          + 0.25 * graph_relevance
          + 0.10 * code_health_score
          + 0.05 * recency
    """
    
    # Weights for different signals
    SEMANTIC_WEIGHT = 0.60
    GRAPH_WEIGHT = 0.25
    HEALTH_WEIGHT = 0.10
    RECENCY_WEIGHT = 0.05
    
    def __init__(
        self,
        use_graph: bool = True,
        use_health: bool = True,
        use_recency: bool = True
    ):
        """
        Initialize hybrid ranker.
        
        Args:
            use_graph: Whether to use graph relevance
            use_health: Whether to use code health scores
            use_recency: Whether to use recency scores
        """
        self.use_graph = use_graph
        self.use_health = use_health
        self.use_recency = use_recency
    
    def rank(
        self,
        results: List[Dict[str, Any]],
        graph_scores: Optional[Dict[str, float]] = None,
        health_scores: Optional[Dict[str, float]] = None,
        normalize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Rank results using hybrid scoring.
        
        Args:
            results: List of search results with semantic scores
            graph_scores: Optional dict of chunk_id -> graph relevance score
            health_scores: Optional dict of file_path -> health score
            normalize: Whether to normalize final scores to 0-1
        
        Returns:
            Ranked list of results with hybrid scores
        """
        if not results:
            return []
        
        # Calculate hybrid scores
        for result in results:
            chunk_id = result.get('chunk_id', '')
            file_path = result.get('file_path', '')
            
            # Semantic score (already provided)
            semantic_score = result.get('score', 0.0)
            
            # Graph relevance score
            graph_score = 0.0
            if self.use_graph and graph_scores:
                graph_score = graph_scores.get(chunk_id, 0.0)
            
            # Code health score
            health_score = 0.0
            if self.use_health and health_scores:
                health_score = health_scores.get(file_path, 0.5)  # Default to 0.5
                health_score = health_score / 100.0  # Normalize to 0-1
            
            # Recency score
            recency_score = 0.0
            if self.use_recency:
                recency_score = self._calculate_recency_score(result)
            
            # Hybrid score
            hybrid_score = (
                self.SEMANTIC_WEIGHT * semantic_score +
                self.GRAPH_WEIGHT * graph_score +
                self.HEALTH_WEIGHT * health_score +
                self.RECENCY_WEIGHT * recency_score
            )
            
            result['hybrid_score'] = hybrid_score
            result['score_breakdown'] = {
                'semantic': semantic_score,
                'graph': graph_score,
                'health': health_score,
                'recency': recency_score
            }
        
        # Sort by hybrid score
        results.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        # Normalize if requested
        if normalize and results:
            max_score = results[0]['hybrid_score']
            min_score = results[-1]['hybrid_score']
            
            if max_score > min_score:
                for result in results:
                    normalized = (result['hybrid_score'] - min_score) / (max_score - min_score)
                    result['normalized_score'] = normalized
        
        return results
    
    def _calculate_recency_score(self, result: Dict[str, Any]) -> float:
        """
        Calculate recency score based on last modified time.
        
        Recent files get higher scores.
        """
        # This would use actual file modification time
        # For now, return default
        return 0.5
    
    def rerank_with_context(
        self,
        results: List[Dict[str, Any]],
        query_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results based on query context.
        
        Args:
            results: Initial results
            query_context: Context information (error type, file, function, etc.)
        
        Returns:
            Re-ranked results
        """
        # Boost scores for results matching context
        error_file = query_context.get('file')
        error_function = query_context.get('function')
        
        for result in results:
            boost = 0.0
            
            # Same file boost
            if error_file and result.get('file_path') == error_file:
                boost += 0.2
            
            # Same function boost (if we had function info)
            if error_function:
                # Would check if result contains the function
                boost += 0.1
            
            # Apply boost
            if boost > 0:
                result['hybrid_score'] = result.get('hybrid_score', 0) * (1 + boost)
        
        # Re-sort
        results.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        return results
    
    def deduplicate(
        self,
        results: List[Dict[str, Any]],
        similarity_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate or highly overlapping results.
        
        Args:
            results: Ranked results
            similarity_threshold: Threshold for considering duplicates
        
        Returns:
            Deduplicated results
        """
        if not results:
            return []
        
        unique_results = [results[0]]  # Always keep top result
        
        for result in results[1:]:
            is_duplicate = False
            
            for unique in unique_results:
                # Check if from same file and overlapping lines
                if (result.get('file_path') == unique.get('file_path') and
                    self._chunks_overlap(result, unique)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        logger.info(f"Deduplicated: {len(results)} -> {len(unique_results)}")
        
        return unique_results
    
    def _chunks_overlap(self, chunk1: Dict[str, Any], chunk2: Dict[str, Any]) -> bool:
        """Check if two chunks overlap significantly."""
        start1 = chunk1.get('start_line', 0)
        end1 = chunk1.get('end_line', 0)
        start2 = chunk2.get('start_line', 0)
        end2 = chunk2.get('end_line', 0)
        
        # Calculate overlap
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_end <= overlap_start:
            return False  # No overlap
        
        overlap_lines = overlap_end - overlap_start
        total_lines = max(end1 - start1, end2 - start2)
        
        # If overlap is more than 80% of the smaller chunk
        return overlap_lines / total_lines > 0.8


def main():
    """CLI entry point for testing."""
    # Test data
    results = [
        {'chunk_id': 'c1', 'file_path': 'file1.py', 'score': 0.9, 'start_line': 1, 'end_line': 10},
        {'chunk_id': 'c2', 'file_path': 'file2.py', 'score': 0.85, 'start_line': 20, 'end_line': 30},
        {'chunk_id': 'c3', 'file_path': 'file1.py', 'score': 0.8, 'start_line': 40, 'end_line': 50},
    ]
    
    graph_scores = {'c1': 0.7, 'c2': 0.9, 'c3': 0.5}
    health_scores = {'file1.py': 80.0, 'file2.py': 60.0}
    
    ranker = HybridRanker(use_graph=True, use_health=True)
    
    ranked = ranker.rank(results, graph_scores, health_scores)
    
    print("\n📊 Hybrid Ranking Results:\n")
    for i, r in enumerate(ranked, 1):
        print(f"{i}. {r['file_path']} (chunk: {r['chunk_id']})")
        print(f"   Hybrid Score: {r['hybrid_score']:.4f}")
        print(f"   Breakdown: {r['score_breakdown']}")
        print()


if __name__ == "__main__":
    main()
