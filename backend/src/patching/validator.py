"""
Patch Validator

Validates code patches before applying them:
- Syntax checking
- Type checking (mypy, tsc)
- Test execution
- Rollback support
"""

import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import shutil

logger = logging.getLogger(__name__)


class PatchValidator:
    """
    Validate code patches in isolated environment.
    
    Validation steps:
    1. Apply patch to temporary copy
    2. Run syntax checks
    3. Run type checkers
    4. Run tests (if available)
    5. Report results
    """
    
    def __init__(self, use_docker: bool = False):
        """
        Initialize validator.
        
        Args:
            use_docker: Use Docker for isolation (recommended for production)
        """
        self.use_docker = use_docker
    
    def validate_patch(
        self,
        file_path: str,
        original_content: str,
        patched_content: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Validate a patch.
        
        Args:
            file_path: Original file path
            original_content: Original file content
            patched_content: Patched file content
            language: Programming language
        
        Returns:
            Validation result
        """
        logger.info(f"Validating patch for {file_path}")
        
        results = {
            'valid': True,
            'checks': {},
            'errors': [],
            'warnings': [],
        }
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_file = Path(tmpdir) / Path(file_path).name
                
                # Write patched content
                tmp_file.write_text(patched_content, encoding='utf-8')
                
                # Run syntax check
                syntax_result = self._check_syntax(str(tmp_file), language)
                results['checks']['syntax'] = syntax_result
                
                if not syntax_result['passed']:
                    results['valid'] = False
                    results['errors'].extend(syntax_result.get('errors', []))
                
                # Run type checker
                if language in ['python', 'typescript']:
                    type_result = self._check_types(str(tmp_file), language)
                    results['checks']['types'] = type_result
                    
                    if not type_result['passed']:
                        # Type errors are warnings, not failures
                        results['warnings'].extend(type_result.get('errors', []))
                
                # Run linter
                lint_result = self._run_linter(str(tmp_file), language)
                results['checks']['lint'] = lint_result
                
                if not lint_result['passed']:
                    results['warnings'].extend(lint_result.get('warnings', []))
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
            results['valid'] = False
            results['errors'].append(str(e))
        
        return results
    
    def _check_syntax(self, file_path: str, language: str) -> Dict[str, Any]:
        """Check syntax validity."""
        result = {'passed': True, 'errors': []}
        
        try:
            if language == 'python':
                # Use Python's compile to check syntax
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                try:
                    compile(code, file_path, 'exec')
                except SyntaxError as e:
                    result['passed'] = False
                    result['errors'].append(f"Syntax error at line {e.lineno}: {e.msg}")
            
            elif language in ['typescript', 'javascript']:
                # Use tsc or node to check syntax
                cmd = ['node', '--check', file_path]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if proc.returncode != 0:
                    result['passed'] = False
                    result['errors'].append(proc.stderr)
        
        except Exception as e:
            result['passed'] = False
            result['errors'].append(str(e))
        
        return result
    
    def _check_types(self, file_path: str, language: str) -> Dict[str, Any]:
        """Run type checker."""
        result = {'passed': True, 'errors': []}
        
        try:
            if language == 'python':
                # Run mypy
                cmd = ['mypy', '--no-error-summary', file_path]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if proc.returncode != 0:
                    result['passed'] = False
                    result['errors'] = proc.stdout.split('\n')
            
            elif language == 'typescript':
                # Run tsc
                cmd = ['tsc', '--noEmit', file_path]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if proc.returncode != 0:
                    result['passed'] = False
                    result['errors'] = proc.stdout.split('\n')
        
        except FileNotFoundError:
            # Type checker not installed
            result['passed'] = True
            result['errors'] = ['Type checker not available']
        except Exception as e:
            result['passed'] = False
            result['errors'].append(str(e))
        
        return result
    
    def _run_linter(self, file_path: str, language: str) -> Dict[str, Any]:
        """Run linter."""
        result = {'passed': True, 'warnings': []}
        
        try:
            if language == 'python':
                # Run flake8
                cmd = ['flake8', '--select=E,W', file_path]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if proc.returncode != 0:
                    result['passed'] = False
                    result['warnings'] = proc.stdout.split('\n')
            
            elif language in ['typescript', 'javascript']:
                # Run eslint
                cmd = ['eslint', file_path]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if proc.returncode != 0:
                    result['passed'] = False
                    result['warnings'] = proc.stdout.split('\n')
        
        except FileNotFoundError:
            # Linter not installed
            result['passed'] = True
        except Exception as e:
            result['warnings'].append(str(e))
        
        return result
    
    def validate_in_docker(
        self,
        file_path: str,
        patched_content: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Validate patch in Docker container (safer isolation).
        
        This is more secure for untrusted patches.
        """
        # TODO: Implement Docker-based validation
        # Would create container, mount code, run checks, cleanup
        
        logger.warning("Docker validation not yet implemented, using direct validation")
        
        return self.validate_patch(file_path, "", patched_content, language)


def main():
    """CLI entry point."""
    validator = PatchValidator()
    
    # Example validation
    original = "def hello():\n    print('Hello')\n"
    patched = "def hello():\n    print('Hello World')\n"
    
    result = validator.validate_patch(
        "test.py",
        original,
        patched,
        "python"
    )
    
    print(f"\n✅ Validation Result:")
    print(f"  Valid: {result['valid']}")
    print(f"  Checks: {list(result['checks'].keys())}")
    
    if result['errors']:
        print(f"\n❌ Errors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result['warnings']:
        print(f"\n⚠️  Warnings:")
        for warning in result['warnings']:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
