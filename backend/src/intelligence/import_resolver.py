"""
Import Resolver

Maps import statements to actual file paths and detects circular dependencies.
"""

from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Import:
    """Represents an import statement."""
    source_file: str
    module: str
    items: List[str]
    is_relative: bool
    line_number: int


@dataclass
class CircularDependency:
    """Represents a circular dependency."""
    cycle: List[str]  # List of file paths in the cycle
    
    def __str__(self) -> str:
        return " -> ".join(self.cycle + [self.cycle[0]])


class ImportResolver:
    """
    Resolve import statements and detect circular dependencies.
    """
    
    def __init__(self, root_path: str):
        """
        Initialize import resolver.
        
        Args:
            root_path: Root directory of the codebase
        """
        self.root_path = Path(root_path).resolve()
        self.import_graph: Dict[str, Set[str]] = {}  # file -> set of imported files
        self.imports_by_file: Dict[str, List[Import]] = {}
    
    def extract_imports(self, file_path: str, content: str, language: str) -> List[Import]:
        """
        Extract import statements from a file.
        
        Args:
            file_path: Path to file
            content: File content
            language: Programming language
        
        Returns:
            List of Import objects
        """
        if language == 'python':
            return self._extract_python_imports(file_path, content)
        elif language in ['javascript', 'typescript']:
            return self._extract_js_imports(file_path, content)
        else:
            return []
    
    def _extract_python_imports(self, file_path: str, content: str) -> List[Import]:
        """Extract Python imports."""
        imports: List[Import] = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Match: import module
            match = re.match(r'^import\s+([\w.]+)', line)
            if match:
                imports.append(Import(
                    source_file=file_path,
                    module=match.group(1),
                    items=[],
                    is_relative=False,
                    line_number=i
                ))
                continue
            
            # Match: from module import items
            match = re.match(r'^from\s+([\w.]+)\s+import\s+(.+)', line)
            if match:
                module = match.group(1)
                items_str = match.group(2)
                
                # Parse items
                items = [item.strip() for item in items_str.split(',')]
                
                imports.append(Import(
                    source_file=file_path,
                    module=module,
                    items=items,
                    is_relative=module.startswith('.'),
                    line_number=i
                ))
        
        return imports
    
    def _extract_js_imports(self, file_path: str, content: str) -> List[Import]:
        """Extract JavaScript/TypeScript imports."""
        imports: List[Import] = []
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Match: import ... from 'module'
            match = re.match(r'^import\s+.*from\s+[\'"]([^\'"]+)[\'"]', line)
            if match:
                module = match.group(1)
                
                imports.append(Import(
                    source_file=file_path,
                    module=module,
                    items=[],
                    is_relative=module.startswith('.'),
                    line_number=i
                ))
                continue
            
            # Match: import 'module'
            match = re.match(r'^import\s+[\'"]([^\'"]+)[\'"]', line)
            if match:
                module = match.group(1)
                
                imports.append(Import(
                    source_file=file_path,
                    module=module,
                    items=[],
                    is_relative=module.startswith('.'),
                    line_number=i
                ))
        
        return imports
    
    def resolve_import_path(
        self,
        import_stmt: Import,
        language: str
    ) -> Optional[str]:
        """
        Resolve an import to an actual file path.
        
        Args:
            import_stmt: Import statement
            language: Programming language
        
        Returns:
            Resolved file path or None if not found
        """
        source_file = Path(import_stmt.source_file)
        module = import_stmt.module
        
        if import_stmt.is_relative:
            # Relative import
            return self._resolve_relative_import(source_file, module, language)
        else:
            # Absolute import
            return self._resolve_absolute_import(module, language)
    
    def _resolve_relative_import(
        self,
        source_file: Path,
        module: str,
        language: str
    ) -> Optional[str]:
        """Resolve relative import."""
        # Count leading dots
        level = len(module) - len(module.lstrip('.'))
        module_name = module.lstrip('.')
        
        # Go up 'level' directories
        current_dir = source_file.parent
        
        for _ in range(level - 1):
            current_dir = current_dir.parent
        
        # Try different file extensions
        if language == 'python':
            extensions = ['.py']
        else:
            extensions = ['.ts', '.tsx', '.js', '.jsx']
        
        # Try as file
        for ext in extensions:
            target = current_dir / f"{module_name}{ext}"
            if target.exists():
                return str(target)
        
        # Try as directory with __init__ or index
        if language == 'python':
            target = current_dir / module_name / '__init__.py'
        else:
            target = current_dir / module_name / 'index.ts'
            if not target.exists():
                target = current_dir / module_name / 'index.js'
        
        if target.exists():
            return str(target)
        
        return None
    
    def _resolve_absolute_import(
        self,
        module: str,
        language: str
    ) -> Optional[str]:
        """Resolve absolute import."""
        # Convert module path to file path
        module_parts = module.split('.')
        
        if language == 'python':
            # Try as file
            file_path = self.root_path / '/'.join(module_parts) + '.py'
            if file_path.exists():
                return str(file_path)
            
            # Try as package
            file_path = self.root_path / '/'.join(module_parts) / '__init__.py'
            if file_path.exists():
                return str(file_path)
        
        # For JS/TS, would need package.json resolution
        # Simplified: just check local paths
        
        return None
    
    def build_dependency_graph(
        self,
        files: List[Dict[str, str]]  # List of {path, content, language}
    ):
        """
        Build dependency graph from files.
        
        Args:
            files: List of file dictionaries
        """
        # Extract imports from all files
        for file_info in files:
            file_path = file_info['path']
            content = file_info['content']
            language = file_info['language']
            
            imports = self.extract_imports(file_path, content, language)
            self.imports_by_file[file_path] = imports
            
            # Resolve imports and build graph
            if file_path not in self.import_graph:
                self.import_graph[file_path] = set()
            
            for imp in imports:
                resolved = self.resolve_import_path(imp, language)
                if resolved:
                    self.import_graph[file_path].add(resolved)
    
    def detect_circular_dependencies(self) -> List[CircularDependency]:
        """
        Detect circular dependencies in the import graph.
        
        Returns:
            List of circular dependencies
        """
        cycles: List[CircularDependency] = []
        visited: Set[str] = set()
        rec_stack: List[str] = []
        
        def dfs(node: str) -> bool:
            """DFS to detect cycles."""
            visited.add(node)
            rec_stack.append(node)
            
            for neighbor in self.import_graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = rec_stack.index(neighbor)
                    cycle = rec_stack[cycle_start:]
                    cycles.append(CircularDependency(cycle=cycle.copy()))
                    return True
            
            rec_stack.pop()
            return False
        
        # Run DFS from each node
        for node in self.import_graph.keys():
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def get_module_dependencies(self, file_path: str) -> Set[str]:
        """Get all modules that a file depends on."""
        return self.import_graph.get(file_path, set())
    
    def get_module_dependents(self, file_path: str) -> Set[str]:
        """Get all modules that depend on a file."""
        dependents: Set[str] = set()
        
        for source, targets in self.import_graph.items():
            if file_path in targets:
                dependents.add(source)
        
        return dependents


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python import_resolver.py <file_path> <language>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'python'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    resolver = ImportResolver(str(Path(file_path).parent))
    imports = resolver.extract_imports(file_path, content, language)
    
    print(f"\n📦 Found {len(imports)} imports:")
    for imp in imports:
        rel = "(relative)" if imp.is_relative else "(absolute)"
        print(f"  Line {imp.line_number}: {imp.module} {rel}")
        if imp.items:
            print(f"    Items: {', '.join(imp.items)}")


if __name__ == "__main__":
    main()
