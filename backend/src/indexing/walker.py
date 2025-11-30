"""
File Walker - Recursively discover and catalog source files

Supports: Python (.py), TypeScript (.ts, .tsx), JavaScript (.js, .jsx)
Excludes: node_modules, .git, dist, __pycache__, .venv, etc.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class FileMetadata:
    """Metadata for a discovered file."""
    path: str
    relative_path: str
    size_bytes: int
    modified_time: str
    language: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FileWalker:
    """
    Recursively walk a directory tree and catalog source code files.
    """
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.js': 'javascript',
        '.jsx': 'javascript',
    }
    
    # Directories to exclude
    EXCLUDED_DIRS = {
        'node_modules',
        '.git',
        'dist',
        'build',
        '__pycache__',
        '.venv',
        'venv',
        'env',
        '.next',
        'out',
        'coverage',
        '.pytest_cache',
        '.mypy_cache',
        '.tox',
        'eggs',
        '.eggs',
        'wheels',
    }
    
    # File patterns to exclude
    EXCLUDED_PATTERNS = {
        '.pyc',
        '.pyo',
        '.so',
        '.dylib',
        '.dll',
        '.egg',
        '.log',
        '.tmp',
        '.swp',
        '.swo',
        '.DS_Store',
    }
    
    def __init__(self, root_path: str):
        """
        Initialize the file walker.
        
        Args:
            root_path: Root directory to start walking from
        """
        self.root_path = Path(root_path).resolve()
        
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")
    
    def should_exclude_dir(self, dir_name: str) -> bool:
        """Check if a directory should be excluded."""
        return dir_name in self.EXCLUDED_DIRS or dir_name.startswith('.')
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded."""
        # Check patterns
        for pattern in self.EXCLUDED_PATTERNS:
            if file_path.name.endswith(pattern):
                return True
        
        # Check extension
        if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
            return True
        
        return False
    
    def get_language(self, file_path: Path) -> str:
        """Determine the programming language from file extension."""
        return self.SUPPORTED_EXTENSIONS.get(file_path.suffix, 'unknown')
    
    def get_file_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata for a file."""
        stat = file_path.stat()
        
        return FileMetadata(
            path=str(file_path),
            relative_path=str(file_path.relative_to(self.root_path)),
            size_bytes=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            language=self.get_language(file_path)
        )
    
    def walk(self) -> List[FileMetadata]:
        """
        Walk the directory tree and collect file metadata.
        
        Returns:
            List of FileMetadata objects for all discovered source files
        """
        discovered_files: List[FileMetadata] = []
        
        for root, dirs, files in os.walk(self.root_path, followlinks=False):
            root_path = Path(root)
            
            # Filter out excluded directories (modify in-place to prune walk)
            dirs[:] = [d for d in dirs if not self.should_exclude_dir(d)]
            
            # Process files
            for filename in files:
                file_path = root_path / filename
                
                # Skip excluded files
                if self.should_exclude_file(file_path):
                    continue
                
                # Add file metadata
                try:
                    metadata = self.get_file_metadata(file_path)
                    discovered_files.append(metadata)
                except (OSError, PermissionError) as e:
                    print(f"Warning: Could not access {file_path}: {e}")
                    continue
        
        return discovered_files
    
    def generate_manifest(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a complete manifest of discovered files.
        
        Args:
            output_path: Optional path to save manifest JSON
        
        Returns:
            Manifest dictionary
        """
        files = self.walk()
        
        manifest = {
            'root_path': str(self.root_path),
            'total_files': len(files),
            'languages': self._count_by_language(files),
            'timestamp': datetime.now().isoformat(),
            'files': [f.to_dict() for f in files]
        }
        
        # Save to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        return manifest
    
    def _count_by_language(self, files: List[FileMetadata]) -> Dict[str, int]:
        """Count files by programming language."""
        counts: Dict[str, int] = {}
        
        for file in files:
            lang = file.language
            counts[lang] = counts.get(lang, 0) + 1
        
        return counts


def main():
    """CLI entry point for testing."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python walker.py <directory_path> [output_manifest.json]")
        sys.exit(1)
    
    root_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    walker = FileWalker(root_path)
    manifest = walker.generate_manifest(output_path)
    
    print(f"\n✅ Discovered {manifest['total_files']} files")
    print(f"\nLanguage breakdown:")
    for lang, count in manifest['languages'].items():
        print(f"  {lang}: {count}")
    
    if output_path:
        print(f"\n📄 Manifest saved to: {output_path}")


if __name__ == "__main__":
    main()
