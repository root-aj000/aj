"""
Advanced Error-Path Retrieval

Traces error propagation through call graph using weighted traversal.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from collections import deque

logger = logging.getLogger(__name__)


class ErrorPathRetriever:
    """
    Advanced error-path retrieval using graph traversal.
    
    Finds execution paths that might lead to an error by:
    1. Starting from error location
    2. Traversing call graph backward (who calls this?)
    3. Weighting paths by relevance
    4. Ranking by likelihood
    """
    
    def __init__(self, neo4j_client, semantic_search):
        """
        Initialize error-path retriever.
        
        Args:
            neo4j_client: Neo4j client for graph queries
            semantic_search: Semantic search for code retrieval
        """
        self.neo4j_client = neo4j_client
        self.semantic_search = semantic_search
    
    def find_error_paths(
        self,
        error_function: str,
        error_file: str,
        max_depth: int = 3,
        max_paths: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find possible execution paths leading to error.
        
        Args:
            error_function: Function where error occurred
            error_file: File containing error
            max_depth: Maximum traversal depth
            max_paths: Maximum paths to return
        
        Returns:
            List of execution paths
        """
        logger.info(f"Finding error paths for {error_function} in {error_file}")
        
        paths = []
        
        # Start from error location
        start_node = {
            'function': error_function,
            'file': error_file,
            'depth': 0,
        }
        
        # BFS traversal backward through call graph
        paths = self._backward_traversal(start_node, max_depth)
        
        # Weight and rank paths
        ranked_paths = self._rank_paths(paths)
        
        return ranked_paths[:max_paths]
    
    def _backward_traversal(
        self,
        start_node: Dict[str, Any],
        max_depth: int
    ) -> List[List[Dict[str, Any]]]:
        """
        Traverse backward through call graph (BFS).
        
        Returns all paths from root callers to error location.
        """
        all_paths = []
        queue = deque([[start_node]])
        visited = set()
        
        while queue:
            current_path = queue.popleft()
            current_node = current_path[-1]
            
            # Check depth
            if current_node['depth'] >= max_depth:
                all_paths.append(current_path)
                continue
            
            # Get callers of current function
            callers = self._get_callers(
                current_node['function'],
                current_node['file']
            )
            
            if not callers:
                # No more callers - this is a root
                all_paths.append(current_path)
                continue
            
            # Expand path with each caller
            for caller in callers:
                caller_key = f"{caller['function']}:{caller['file']}"
                
                # Avoid cycles
                if caller_key in visited:
                    continue
                
                visited.add(caller_key)
                
                new_path = current_path + [{
                    'function': caller['function'],
                    'file': caller['file'],
                    'depth': current_node['depth'] + 1,
                    'call_type': caller.get('call_type', 'direct'),
                }]
                
                queue.append(new_path)
        
        return all_paths
    
    def _get_callers(self, function_name: str, file_path: str) -> List[Dict[str, Any]]:
        """Get all functions that call this function."""
        if not self.neo4j_client:
            return []
        
        query = """
        MATCH (caller:Function)-[c:CALLS]->(callee:Function)
        WHERE callee.name = $function_name 
        AND callee.file = $file_path
        RETURN caller.name as function, caller.file as file,
               c.call_type as call_type
        """
        
        results = self.neo4j_client.execute_query(query, {
            'function_name': function_name,
            'file_path': file_path,
        })
        
        return [
            {
                'function': r['function'],
                'file': r['file'],
                'call_type': r.get('call_type', 'direct'),
            }
            for r in results
        ]
    
    def _rank_paths(self, paths: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Rank paths by likelihood of causing error.
        
        Scoring factors:
        - Path length (shorter = more direct)
        - Call types (direct > indirect)
        - Code health (unhealthy code = more likely)
        - Semantic similarity to error
        """
        ranked = []
        
        for path in paths:
            score = self._calculate_path_score(path)
            
            ranked.append({
                'path': path,
                'score': score,
                'length': len(path),
                'root_function': path[-1]['function'] if path else None,
                'root_file': path[-1]['file'] if path else None,
            })
        
        # Sort by score descending
        ranked.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked
    
    def _calculate_path_score(self, path: List[Dict[str, Any]]) -> float:
        """Calculate relevance score for a path."""
        if not path:
            return 0.0
        
        # Base score
        score = 100.0
        
        # Penalty for length (prefer shorter paths)
        length_penalty = len(path) * 5
        score -= length_penalty
        
        # Bonus for direct calls
        direct_calls = sum(1 for node in path if node.get('call_type') == 'direct')
        score += direct_calls * 10
        
        # Normalize to 0-100
        score = max(0, min(100, score))
        
        return score
    
    def get_error_propagation_context(
        self,
        paths: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get code context for error propagation paths.
        
        Retrieves relevant code snippets for each function in paths.
        """
        context = {
            'paths': paths,
            'code_snippets': {},
            'total_functions': 0,
        }
        
        # Collect unique functions
        functions = set()
        for path_data in paths:
            for node in path_data['path']:
                func_key = f"{node['function']}:{node['file']}"
                functions.add((node['function'], node['file']))
        
        context['total_functions'] = len(functions)
        
        # Retrieve code for each function
        for func_name, file_path in functions:
            # This would use semantic search or direct file reading
            context['code_snippets'][f"{func_name}:{file_path}"] = {
                'function': func_name,
                'file': file_path,
                'code': '# Code would be retrieved here',
            }
        
        return context


def main():
    """CLI entry point."""
    retriever = ErrorPathRetriever(None, None)
    
    print("\n🔍 Error-Path Retrieval Example")
    print("=" * 50)
    
    paths = retriever.find_error_paths(
        error_function="process_payment",
        error_file="payment.py",
        max_depth=3
    )
    
    print(f"\nFound {len(paths)} execution paths")
    
    for idx, path_data in enumerate(paths, 1):
        print(f"\nPath {idx} (score: {path_data['score']:.1f}):")
        for node in reversed(path_data['path']):
            print(f"  → {node['function']} ({node['file']})")


if __name__ == "__main__":
    main()
