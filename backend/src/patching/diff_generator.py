"""
Diff Generator

Generates unified diffs for code patches.
"""

from typing import List, Dict, Any, Optional
import difflib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DiffGenerator:
    """
    Generate unified diff patches for code changes.
    """
    
    def __init__(self):
        """Initialize diff generator."""
        pass
    
    def generate_diff(
        self,
        original_content: str,
        modified_content: str,
        file_path: str
    ) -> str:
        """
        Generate unified diff.
        
        Args:
            original_content: Original file content
            modified_content: Modified file content
            file_path: File path for context
        
        Returns:
            Unified diff string
        """
        original_lines = original_content.splitlines(keepends=True)
        modified_lines = modified_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    def generate_patch(
        self,
        changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a complete patch for multiple file changes.
        
        Args:
            changes: List of change dicts with file_path, original, modified
        
        Returns:
            Patch dictionary with diffs and metadata
        """
        patches = []
        
        for change in changes:
            file_path = change['file_path']
            original = change.get('original_content', '')
            modified = change.get('modified_content', '')
            
            diff = self.generate_diff(original, modified, file_path)
            
            if diff:
                patches.append({
                    'file': file_path,
                    'diff': diff,
                    'additions': self._count_additions(diff),
                    'deletions': self._count_deletions(diff)
                })
        
        return {
            'patches': patches,
            'total_files': len(patches),
            'total_additions': sum(p['additions'] for p in patches),
            'total_deletions': sum(p['deletions'] for p in patches)
        }
    
    def _count_additions(self, diff: str) -> int:
        """Count added lines in diff."""
        return sum(1 for line in diff.splitlines() if line.startswith('+') and not line.startswith('+++'))
    
    def _count_deletions(self, diff: str) -> int:
        """Count deleted lines in diff."""
        return sum(1 for line in diff.splitlines() if line.startswith('-') and not line.startswith('---'))
    
    def apply_patch(
        self,
        file_path: str,
        patch_content: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Apply a patch to a file.
        
        Args:
            file_path: Target file path
            patch_content: Patch content
            dry_run: If True, don't actually modify file
        
        Returns:
            Result dictionary
        """
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Parse patch and apply
            # This is simplified - production would use proper patch library
            modified_content = self._apply_unified_diff(original_content, patch_content)
            
            if not dry_run:
                # Write modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                logger.info(f"Applied patch to {file_path}")
            
            return {
                'success': True,
                'file': file_path,
                'dry_run': dry_run
            }
        
        except Exception as e:
            logger.error(f"Failed to apply patch: {e}")
            
            return {
                'success': False,
                'file': file_path,
                'error': str(e)
            }
    
    def _apply_unified_diff(self, original: str, diff: str) -> str:
        """Apply unified diff to content (simplified)."""
        # In production, use a proper patch library
        # This is a placeholder
        return original


def main():
    """CLI entry point."""
    # Test diff generation
    original = """def hello():
    print("Hello")
    return True
"""
    
    modified = """def hello(name):
    print(f"Hello {name}")
    return True
"""
    
    generator = DiffGenerator()
    diff = generator.generate_diff(original, modified, "test.py")
    
    print("\n📝 Generated Diff:\n")
    print(diff)
    
    patch = generator.generate_patch([
        {
            'file_path': 'test.py',
            'original_content': original,
            'modified_content': modified
        }
    ])
    
    print(f"\n📊 Patch Stats:")
    print(f"  Files: {patch['total_files']}")
    print(f"  Additions: +{patch['total_additions']}")
    print(f"  Deletions: -{patch['total_deletions']}")


if __name__ == "__main__":
    main()
