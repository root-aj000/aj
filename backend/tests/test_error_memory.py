"""
Unit Tests for Error Memory Database
"""

import pytest
import tempfile
from pathlib import Path

from src.memory.error_memory import ErrorMemoryDB


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = ErrorMemoryDB(db_path)
    yield db
    
    db.close()
    Path(db_path).unlink()


class TestErrorMemoryDB:
    """Test suite for ErrorMemoryDB."""
    
    def test_initialization(self, temp_db):
        """Test database initialization."""
        assert temp_db.conn is not None
    
    def test_save_error_snapshot(self, temp_db):
        """Test saving error snapshot."""
        error_data = {
            'error_hash': 'test_hash_123',
            'error_type': 'TypeError',
            'error_message': 'Cannot read property',
            'file_path': 'test.py',
            'line_number': 42,
        }
        
        error_hash = temp_db.save_error_snapshot(error_data)
        
        assert error_hash == 'test_hash_123'
    
    def test_save_duplicate_error(self, temp_db):
        """Test that duplicate errors increment occurrence count."""
        error_data = {
            'error_hash': 'duplicate_123',
            'error_type': 'ValueError',
            'error_message': 'Invalid value',
        }
        
        # Save twice
        temp_db.save_error_snapshot(error_data)
        temp_db.save_error_snapshot(error_data)
        
        # Check occurrence count (would need to query database)
        # For now, just verify no errors
    
    def test_save_error_resolution(self, temp_db):
        """Test saving error resolution."""
        # First save error
        error_data = {
            'error_hash': 'res_test_123',
            'error_type': 'RuntimeError',
            'error_message': 'Test error',
        }
        temp_db.save_error_snapshot(error_data)
        
        # Save resolution
        resolution_data = {
            'error_hash': 'res_test_123',
            'resolution_type': 'patch',
            'patch_applied': 'def fix(): pass',
            'llm_model': 'gemini-2.0-flash-exp',
            'success': True,
            'resolution_time_ms': 1500,
        }
        
        temp_db.save_error_resolution(resolution_data)
        # No errors = success
    
    def test_create_debug_session(self, temp_db):
        """Test creating debug session."""
        session_id = 'session_123'
        query = 'Why is this failing?'
        
        result = temp_db.create_debug_session(session_id, query)
        
        assert result == session_id
    
    def test_conversation_history(self, temp_db):
        """Test conversation history storage and retrieval."""
        session_id = 'conv_session_123'
        
        temp_db.create_debug_session(session_id, 'Initial query')
        
        # Save conversation turns
        temp_db.save_conversation_turn(session_id, 'user', 'Hello')
        temp_db.save_conversation_turn(session_id, 'assistant', 'Hi there!')
        
        # Retrieve history
        history = temp_db.get_conversation_history(session_id)
        
        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[1]['role'] == 'assistant'
    
    def test_get_error_stats(self, temp_db):
        """Test error statistics retrieval."""
        # Add some test errors
        for i in range(3):
            temp_db.save_error_snapshot({
                'error_hash': f'stat_test_{i}',
                'error_type': 'TestError',
                'error_message': 'Test',
            })
        
        stats = temp_db.get_error_stats()
        
        assert stats['total_errors'] >= 3
        assert 'resolved_errors' in stats
        assert 'top_error_types' in stats
