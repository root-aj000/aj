"""
Unit Tests for File Walker
"""

import pytest
from pathlib import Path
import tempfile
import os

from src.indexing.walker import FileWalker


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create test files
        (repo_path / "main.py").write_text("def main():\n    pass\n")
        (repo_path / "utils.py").write_text("def helper():\n    return True\n")
        
        # Create subdirectory
        sub_dir = repo_path / "src"
        sub_dir.mkdir()
        (sub_dir / "module.py").write_text("class Module:\n    pass\n")
        
        # Create files to be excluded
        (repo_path / ".git").mkdir()
        (repo_path / "__pycache__").mkdir()
        (repo_path / "node_modules").mkdir()
        
        yield repo_path


class TestFileWalker:
    """Test suite for FileWalker."""
    
    def test_initialization(self, temp_repo):
        """Test FileWalker initialization."""
        walker = FileWalker(str(temp_repo))
        
        assert walker.root_path == temp_repo
        assert walker.exclude_dirs is not None
        assert walker.supported_extensions is not None
    
    def test_walk_finds_python_files(self, temp_repo):
        """Test that walker finds Python files."""
        walker = FileWalker(str(temp_repo))
        manifest = walker.walk()
        
        files = manifest['files']
        file_paths = [f['path'] for f in files]
        
        assert any('main.py' in p for p in file_paths)
        assert any('utils.py' in p for p in file_paths)
        assert any('module.py' in p for p in file_paths)
    
    def test_walk_excludes_directories(self, temp_repo):
        """Test that walker excludes specified directories."""
        walker = FileWalker(str(temp_repo))
        manifest = walker.walk()
        
        files = manifest['files']
        file_paths = [f['path'] for f in files]
        
        # Should not include files from excluded dirs
        assert not any('.git' in p for p in file_paths)
        assert not any('__pycache__' in p for p in file_paths)
        assert not any('node_modules' in p for p in file_paths)
    
    def test_language_detection(self, temp_repo):
        """Test language detection."""
        walker = FileWalker(str(temp_repo))
        manifest = walker.walk()
        
        files = manifest['files']
        
        for file_data in files:
            if file_data['path'].endswith('.py'):
                assert file_data['language'] == 'python'
    
    def test_metadata_extraction(self, temp_repo):
        """Test that metadata is extracted correctly."""
        walker = FileWalker(str(temp_repo))
        manifest = walker.walk()
        
        files = manifest['files']
        
        assert len(files) > 0
        
        for file_data in files:
            assert 'path' in file_data
            assert 'relative_path' in file_data
            assert 'language' in file_data
            assert 'size_bytes' in file_data
            assert file_data['size_bytes'] > 0
    
    def test_manifest_statistics(self, temp_repo):
        """Test manifest statistics."""
        walker = FileWalker(str(temp_repo))
        manifest = walker.walk()
        
        assert 'stats' in manifest
        assert manifest['stats']['total_files'] == 3
        assert 'total_size_bytes' in manifest['stats']


@pytest.mark.integration
def test_walker_with_real_structure(temp_repo):
    """Integration test with realistic file structure."""
    # Create more complex structure
    (temp_repo / "tests").mkdir()
    (temp_repo / "tests" / "test_main.py").write_text("def test_func():\n    pass\n")
    
    walker = FileWalker(str(temp_repo))
    manifest = walker.walk()
    
    assert manifest['stats']['total_files'] == 4
    assert len(manifest['files']) == 4
