"""
AST Parser - Parse source code into Abstract Syntax Trees using Tree-sitter

Supports: Python, TypeScript, JavaScript
Provides normalized JSON representation of AST
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    import tree_sitter_typescript as tstype
    import tree_sitter_javascript as tsjs
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    print("Warning: tree-sitter not available. Install with:")
    print("  pip install tree-sitter tree-sitter-python tree-sitter-typescript tree-sitter-javascript")


class ASTParser:
    """
    Parse source code files into AST using Tree-sitter.
    """
    
    def __init__(self):
        """Initialize parsers for supported languages."""
        if not HAS_TREE_SITTER:
            raise RuntimeError("tree-sitter not installed")
        
        # Initialize languages
        self.languages = {
            'python': Language(tspython.language()),
            'typescript': Language(tstype.language_typescript()),
            'tsx': Language(tstype.language_tsx()),
            'javascript': Language(tsjs.language()),
        }
        
        # Initialize parsers
        self.parsers = {}
        for name, lang in self.languages.items():
            parser = Parser(lang)
            self.parsers[name] = parser
    
    def get_parser(self, language: str) -> Optional[Parser]:
        """Get parser for a specific language."""
        lang_map = {
            'python': 'python',
            'typescript': 'typescript',
            'javascript': 'javascript',
        }
        
        parser_name = lang_map.get(language)
        return self.parsers.get(parser_name)
    
    def parse_file(self, file_path: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Parse a file and return AST.
        
        Args:
            file_path: Path to source file
            language: Programming language (python, typescript, javascript)
        
        Returns:
            Dictionary containing AST data or None if parsing fails
        """
        parser = self.get_parser(language)
        if not parser:
            return None
        
        try:
            # Read source code
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            # Parse
            tree = parser.parse(source_code)
            
            # Convert to JSON-serializable format
            ast_json = self._node_to_dict(tree.root_node, source_code)
            
            return {
                'file': str(file_path),
                'language': language,
                'ast': ast_json,
                'has_errors': tree.root_node.has_error
            }
        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None
    
    def _node_to_dict(self, node, source_code: bytes) -> Dict[str, Any]:
        """
        Convert a Tree-sitter node to a dictionary.
        
        Args:
            node: Tree-sitter node
            source_code: Original source code bytes
        
        Returns:
            Dictionary representation of the node
        """
        result = {
            'type': node.type,
            'start_point': node.start_point,
            'end_point': node.end_point,
            'start_byte': node.start_byte,
            'end_byte': node.end_byte,
        }
        
        # Add text for leaf nodes
        if node.child_count == 0:
            text = source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
            result['text'] = text
        
        # Add children
        if node.child_count > 0:
            result['children'] = [
                self._node_to_dict(child, source_code)
                for child in node.children
            ]
        
        return result
    
    def extract_functions(self, ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract function definitions from AST.
        
        Args:
            ast_data: AST dictionary from parse_file
        
        Returns:
            List of function metadata
        """
        functions = []
        
        def traverse(node: Dict[str, Any], depth: int = 0):
            node_type = node.get('type', '')
            
            # Python function
            if node_type == 'function_definition':
                func_info = {
                    'name': self._get_function_name(node),
                    'start_line': node['start_point'][0] + 1,
                    'end_line': node['end_point'][0] + 1,
                    'type': 'function',
                    'language': ast_data.get('language')
                }
                functions.append(func_info)
            
            # TypeScript/JavaScript function
            elif node_type in ['function_declaration', 'method_definition', 'arrow_function']:
                func_info = {
                    'name': self._get_function_name(node),
                    'start_line': node['start_point'][0] + 1,
                    'end_line': node['end_point'][0] + 1,
                    'type': 'function',
                    'language': ast_data.get('language')
                }
                functions.append(func_info)
            
            # Recursively traverse children
            for child in node.get('children', []):
                traverse(child, depth + 1)
        
        if 'ast' in ast_data:
            traverse(ast_data['ast'])
        
        return functions
    
    def _get_function_name(self, node: Dict[str, Any]) -> str:
        """Extract function name from node."""
        for child in node.get('children', []):
            if child.get('type') == 'identifier':
                return child.get('text', 'anonymous')
        return 'anonymous'
    
    def extract_classes(self, ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract class definitions from AST.
        
        Args:
            ast_data: AST dictionary from parse_file
        
        Returns:
            List of class metadata
        """
        classes = []
        
        def traverse(node: Dict[str, Any]):
            node_type = node.get('type', '')
            
            if node_type in ['class_definition', 'class_declaration']:
                class_info = {
                    'name': self._get_class_name(node),
                    'start_line': node['start_point'][0] + 1,
                    'end_line': node['end_point'][0] + 1,
                    'type': 'class',
                    'language': ast_data.get('language')
                }
                classes.append(class_info)
            
            for child in node.get('children', []):
                traverse(child)
        
        if 'ast' in ast_data:
            traverse(ast_data['ast'])
        
        return classes
    
    def _get_class_name(self, node: Dict[str, Any]) -> str:
        """Extract class name from node."""
        for child in node.get('children', []):
            if child.get('type') == 'identifier':
                return child.get('text', 'Anonymous')
        return 'Anonymous'


def main():
    """CLI entry point for testing."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python ast_parser.py <file_path> <language>")
        print("Languages: python, typescript, javascript")
        sys.exit(1)
    
    file_path = sys.argv[1]
    language = sys.argv[2]
    
    parser = ASTParser()
    result = parser.parse_file(file_path, language)
    
    if result:
        print(f"\n✅ Parsed successfully")
        print(f"Has errors: {result['has_errors']}")
        
        # Extract functions
        functions = parser.extract_functions(result)
        print(f"\n📦 Found {len(functions)} functions:")
        for func in functions:
            print(f"  - {func['name']} (lines {func['start_line']}-{func['end_line']})")
        
        # Extract classes
        classes = parser.extract_classes(result)
        print(f"\n📦 Found {len(classes)} classes:")
        for cls in classes:
            print(f"  - {cls['name']} (lines {cls['start_line']}-{cls['end_line']})")
    else:
        print("❌ Parsing failed")


if __name__ == "__main__":
    main()
