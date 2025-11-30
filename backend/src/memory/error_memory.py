"""
Error Memory Database

Stores error snapshots and debugging history.
"""

import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ErrorMemoryDB:
    """
    SQLite database for error tracking and debugging history.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize error memory database.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Error snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_hash TEXT NOT NULL UNIQUE,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                file_path TEXT,
                line_number INTEGER,
                function_name TEXT,
                stack_trace TEXT,
                context_code TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                occurrence_count INTEGER DEFAULT 1,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        # Error resolutions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_resolutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_hash TEXT NOT NULL,
                resolution_type TEXT NOT NULL,
                patch_applied TEXT,
                llm_model TEXT,
                success BOOLEAN NOT NULL,
                resolution_time_ms INTEGER,
                resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (error_hash) REFERENCES error_snapshots(error_hash)
            )
        ''')
        
        # Debugging sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debug_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL UNIQUE,
                error_hash TEXT,
                query TEXT NOT NULL,
                retrieved_chunks TEXT,
                reasoning_tier TEXT,
                llm_calls INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (error_hash) REFERENCES error_snapshots(error_hash)
            )
        ''')
        
        # Conversation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES debug_sessions(session_id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_hash ON error_snapshots(error_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_file ON error_snapshots(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session ON debug_sessions(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_history(session_id)')
        
        self.conn.commit()
    
    def save_error_snapshot(self, error_data: Dict[str, Any]) -> str:
        """
        Save or update error snapshot.
        
        Args:
            error_data: Error information
        
        Returns:
            Error hash
        """
        cursor = self.conn.cursor()
        
        error_hash = error_data['error_hash']
        
        # Check if error exists
        cursor.execute('SELECT id, occurrence_count FROM error_snapshots WHERE error_hash = ?', (error_hash,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE error_snapshots
                SET last_seen = CURRENT_TIMESTAMP,
                    occurrence_count = occurrence_count + 1
                WHERE error_hash = ?
            ''', (error_hash,))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO error_snapshots
                (error_hash, error_type, error_message, file_path, line_number, 
                 function_name, stack_trace, context_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                error_hash,
                error_data.get('error_type'),
                error_data.get('error_message'),
                error_data.get('file_path'),
                error_data.get('line_number'),
                error_data.get('function_name'),
                error_data.get('stack_trace'),
                error_data.get('context_code')
            ))
        
        self.conn.commit()
        logger.info(f"Saved error snapshot: {error_hash}")
        
        return error_hash
    
    def save_error_resolution(self, resolution_data: Dict[str, Any]):
        """Save error resolution attempt."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_resolutions
            (error_hash, resolution_type, patch_applied, llm_model, success, resolution_time_ms, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            resolution_data['error_hash'],
            resolution_data.get('resolution_type', 'patch'),
            resolution_data.get('patch_applied'),
            resolution_data.get('llm_model'),
            resolution_data['success'],
            resolution_data.get('resolution_time_ms'),
            resolution_data.get('notes')
        ))
        
        # Mark error as resolved if successful
        if resolution_data['success']:
            cursor.execute('''
                UPDATE error_snapshots
                SET resolved = 1
                WHERE error_hash = ?
            ''', (resolution_data['error_hash'],))
        
        self.conn.commit()
    
    def create_debug_session(self, session_id: str, query: str, error_hash: Optional[str] = None) -> str:
        """Create a new debugging session."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO debug_sessions (session_id, error_hash, query)
            VALUES (?, ?, ?)
        ''', (session_id, error_hash, query))
        
        self.conn.commit()
        
        return session_id
    
    def update_debug_session(self, session_id: str, updates: Dict[str, Any]):
        """Update debugging session."""
        cursor = self.conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key == 'retrieved_chunks' and isinstance(value, (list, dict)):
                value = json.dumps(value)
            
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(session_id)
        
        query = f"UPDATE debug_sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
        cursor.execute(query, values)
        
        self.conn.commit()
    
    def save_conversation_turn(self, session_id: str, role: str, content: str):
        """Save a conversation turn."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversation_history (session_id, role, content)
            VALUES (?, ?, ?)
        ''', (session_id, role, content))
        
        self.conn.commit()
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT role, content, timestamp
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (session_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_similar_errors(self, error_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar errors that were resolved."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT e.*, r.resolution_type, r.patch_applied
            FROM error_snapshots e
            JOIN error_resolutions r ON e.error_hash = r.error_hash
            WHERE e.error_type = ? AND e.resolved = 1 AND r.success = 1
            ORDER BY e.last_seen DESC
            LIMIT ?
        ''', (error_type, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM error_snapshots')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as resolved FROM error_snapshots WHERE resolved = 1')
        resolved = cursor.fetchone()['resolved']
        
        cursor.execute('SELECT error_type, COUNT(*) as count FROM error_snapshots GROUP BY error_type ORDER BY count DESC LIMIT 5')
        top_types = [dict(row) for row in cursor.fetchall()]
        
        return {
            'total_errors': total,
            'resolved_errors': resolved,
            'unresolved_errors': total - resolved,
            'top_error_types': top_types
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """CLI entry point."""
    from ..app.config import get_settings
    
    settings = get_settings()
    
    with ErrorMemoryDB(settings.memory_db_path) as db:
        # Test error snapshot
        error_data = {
            'error_hash': 'test_error_123',
            'error_type': 'TypeError',
            'error_message': 'Cannot read property of undefined',
            'file_path': 'test.py',
            'line_number': 42,
            'function_name': 'process_data'
        }
        
        db.save_error_snapshot(error_data)
        
        # Get stats
        stats = db.get_error_stats()
        
        print("\n📊 Error Memory Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
