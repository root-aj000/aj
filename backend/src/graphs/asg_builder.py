"""
ASG (Abstract Semantic Graph) Builder

Extracts semantic relationships and builds graph in Neo4j.
"""

from typing import Dict, List, Any, Optional, Set
import logging
import re
import sys
from .neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)



class ASGBuilder:
    """
    Build Abstract Semantic Graph from code.
    
    Nodes: Function, Class, Variable, Import
    Edges: CALLS, DEFINES, IMPORTS, REFERENCES, OVERRIDES, EXTENDS
    """
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize ASG builder.
        
        Args:
            neo4j_client: Neo4j client instance
        """
        self.client = neo4j_client
        self.node_cache: Dict[str, str] = {}  # (type, identifier) -> node_id
    
    def build_from_manifest(self, manifest: Dict[str, Any]):
        """
        Build ASG from indexing manifest.
        
        Args:
            manifest: Complete indexing manifest
        """
        logger.info("Building ASG from manifest...")
        
        files = manifest.get('files', [])
        
        # First pass: Create nodes
        for file_data in files:
            self._process_file(file_data)
        
        # Second pass: Create relationships
        for file_data in files:
            self._create_relationships(file_data)
        
        logger.info("ASG build complete")
    
    def _process_file(self, file_data: Dict[str, Any]):
        """Process a single file and create nodes."""
        file_path = file_data['path']
        
        # Create file node
        file_node_id = self.client.create_file_node({
            'path': file_path,
            'language': file_data['language'],
            'size_bytes': file_data['size_bytes']
        })
        
        self.node_cache[('file', file_path)] = file_node_id
        
        # Create function nodes
        for func in file_data.get('functions', []):
            func_id = self._create_function_node(func, file_path)
            
            # Link function to file
            self.client.create_relationship(
                file_node_id,
                func_id,
                'CONTAINS'
            )
        
        # Create class nodes
        for cls in file_data.get('classes', []):
            cls_id = self._create_class_node(cls, file_path)
            
            # Link class to file
            self.client.create_relationship(
                file_node_id,
                cls_id,
                'CONTAINS'
            )
    
    def _create_function_node(self, func: Dict[str, Any], file_path: str) -> str:
        """Create a function node."""
        func_identifier = f"{file_path}::{func['name']}"
        
        if ('function', func_identifier) in self.node_cache:
            return self.node_cache[('function', func_identifier)]
        
        # Extract signature (simplified)
        signature = f"{func['name']}()"
        
        node_id = self.client.create_function_node({
            'name': func['name'],
            'file': file_path,
            'start_line': func['start_line'],
            'end_line': func['end_line'],
            'signature': signature,
            'language': func.get('language', 'unknown'),
            'complexity': 0  # Will be filled by static analyzer
        })
        
        self.node_cache[('function', func_identifier)] = node_id
        
        return node_id
    
    def _create_class_node(self, cls: Dict[str, Any], file_path: str) -> str:
        """Create a class node."""
        cls_identifier = f"{file_path}::{cls['name']}"
        
        if ('class', cls_identifier) in self.node_cache:
            return self.node_cache[('class', cls_identifier)]
        
        node_id = self.client.create_class_node({
            'name': cls['name'],
            'file': file_path,
            'start_line': cls['start_line'],
            'end_line': cls['end_line'],
            'language': cls.get('language', 'unknown')
        })
        
        self.node_cache[('class', cls_identifier)] = node_id
        
        return node_id
    
    def _create_relationships(self, file_data: Dict[str, Any]):
        """Create relationships between nodes (second pass)."""
        file_path = file_data['path']
        
        # For now, we'll extract basic CALLS relationships from function content
        # In a production system, this would use AST analysis
        
        for func in file_data.get('functions', []):
            func_identifier = f"{file_path}::{func['name']}"
            func_id = self.node_cache.get(('function', func_identifier))
            
            if not func_id:
                continue
            
            # Extract function calls from chunks
            # This is simplified - real implementation would use AST
            calls = self._extract_function_calls(file_data, func)
            
            for called_func in calls:
                callee_id = self.node_cache.get(('function', called_func))
                
                if callee_id:
                    try:
                        self.client.create_relationship(
                            func_id,
                            callee_id,
                            'CALLS'
                        )
                    except Exception as e:
                        logger.debug(f"Could not create CALLS relationship: {e}")
    
    def _extract_function_calls(self, file_data: Dict[str, Any], function: Dict[str, Any]) -> Set[str]:
        """
        Extract function calls (simplified).
        
        In production, this would use the AST to find actual function calls.
        For now, we'll use a simple heuristic.
        """
        calls: Set[str] = set()
        
        # Get chunks that overlap with this function
        start = function['start_line']
        end = function['end_line']
        
        for chunk in file_data.get('chunks', []):
            if chunk['start_line'] <= end and chunk['end_line'] >= start:
                # Simple pattern matching for function calls
                # Pattern: word followed by (
                pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                matches = re.findall(pattern, chunk['content'])
                
                for match in matches:
                    # Try to find this function in the same file
                    for other_func in file_data.get('functions', []):
                        if other_func['name'] == match and other_func['name'] != function['name']:
                            identifier = f"{file_data['path']}::{match}"
                            calls.add(identifier)
        
        return calls
    
    def get_call_graph(self, function_name: str) -> Dict[str, Any]:
        """
        Get call graph for a function.
        
        Args:
            function_name: Function name
        
        Returns:
            Dictionary with callers and callees
        """
        func = self.client.find_function(function_name)
        
        if not func:
            return {'error': 'Function not found'}
        
        callers = self.client.get_function_callers(func['id'])
        callees = self.client.get_function_callees(func['id'])
        
        return {
            'function': func,
            'callers': callers,
            'callees': callees
        }
    
    def find_all_paths(
        self,
        from_function: str,
        to_function: str,
        max_depth: int = 5
    ) -> List[List[str]]:
        """
        Find all paths between two functions.
        
        Args:
            from_function: Source function name
            to_function: Target function name
            max_depth: Maximum path depth
        
        Returns:
            List of paths (each path is a list of function names)
        """
        query = """
            MATCH path = (f1:Function {name: $from})-[:CALLS*1..5]->(f2:Function {name: $to})
            RETURN [node in nodes(path) | node.name] as path_names
            LIMIT 10
        """
        
        results = self.client.execute_cypher(query, {
            'from': from_function,
            'to': to_function
        })
        
        return [r['path_names'] for r in results]


def main():
    """CLI entry point."""
    
    from ..app.config import get_settings
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python asg_builder.py <manifest.json>")
        sys.exit(1)
    
    manifest_path = sys.argv[1]
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    settings = get_settings()
    
    with Neo4jClient(settings.neo4j_url, settings.neo4j_username, settings.neo4j_password) as client:
        # Clear existing data (optional)
        # client.clear_database()
        
        # Create indexes
        client.create_indexes()
        
        # Build ASG
        builder = ASGBuilder(client)
        builder.build_from_manifest(manifest)
        
        # Show stats
        stats = client.get_graph_stats()
        print("\n✅ ASG built successfully")
        print(f"\n📊 Graph Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
