"""
Code Health Database

SQLite database for storing code health metrics and history.
"""

import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class CodeHealthDB:
    """
    Database for code health tracking.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Code smells table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_smells (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file TEXT NOT NULL,
                line INTEGER NOT NULL,
                smell_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                suggestion TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        # Function risk scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS function_risk_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_id TEXT NOT NULL,
                file TEXT NOT NULL,
                function_name TEXT NOT NULL,
                health_score REAL NOT NULL,
                complexity INTEGER NOT NULL,
                bug_count INTEGER DEFAULT 0,
                churn_rate REAL DEFAULT 0.0,
                last_modified TIMESTAMP,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Change impact table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS change_impact (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_id TEXT NOT NULL,
                file TEXT NOT NULL,
                affected_functions TEXT,  -- JSON array
                risk_level TEXT NOT NULL,
                impact_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bug hotspots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_hotspots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file TEXT NOT NULL,
                function_name TEXT,
                bug_frequency INTEGER DEFAULT 1,
                last_bug_at TIMESTAMP,
                severity TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Refactor history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refactor_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_id TEXT NOT NULL,
                file TEXT NOT NULL,
                function_name TEXT NOT NULL,
                reason TEXT,
                before_score REAL,
                after_score REAL,
                refactored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # File health history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_health_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file TEXT NOT NULL,
                health_score REAL NOT NULL,
                metrics TEXT,  -- JSON
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_smells_file ON code_smells(file)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_smells_resolved ON code_smells(resolved)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_function_risk_file ON function_risk_scores(file)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_function_risk_id ON function_risk_scores(function_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hotspots_file ON bug_hotspots(file)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_health_file ON file_health_history(file)')
        
        self.conn.commit()
    
    def save_code_smells(self, smells: List[Dict[str, Any]]):
        """Save code smells to database."""
        cursor = self.conn.cursor()
        
        for smell in smells:
            cursor.execute('''
                INSERT INTO code_smells (file, line, smell_type, severity, message, suggestion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                smell.get('file'),
                smell.get('line'),
                smell.get('type'),
                smell.get('severity'),
                smell.get('message'),
                smell.get('suggestion')
            ))
        
        self.conn.commit()
        logger.info(f"Saved {len(smells)} code smells")
    
    def save_function_risk_score(self, score_data: Dict[str, Any]):
        """Save function risk score."""
        cursor = self.conn.cursor()
        
        function_id = f"{score_data['file']}::{score_data['function_name']}"
        
        cursor.execute('''
            INSERT INTO function_risk_scores 
            (function_id, file, function_name, health_score, complexity, bug_count, churn_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            function_id,
            score_data['file'],
            score_data['function_name'],
            score_data['health_score'],
            score_data['complexity'],
            score_data.get('bug_count', 0),
            score_data.get('churn_rate', 0.0)
        ))
        
        self.conn.commit()
    
    def save_bug_hotspot(self, hotspot: Dict[str, Any]):
        """Save or update bug hotspot."""
        cursor = self.conn.cursor()
        
        # Check if hotspot exists
        cursor.execute('''
            SELECT id, bug_frequency FROM bug_hotspots
            WHERE file = ? AND function_name = ?
        ''', (hotspot['file'], hotspot.get('function_name', '')))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE bug_hotspots
                SET bug_frequency = bug_frequency + 1,
                    last_bug_at = CURRENT_TIMESTAMP,
                    severity = ?,
                    notes = ?
                WHERE id = ?
            ''', (
                hotspot.get('severity', 'medium'),
                hotspot.get('notes', ''),
                existing['id']
            ))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO bug_hotspots
                (file, function_name, bug_frequency, last_bug_at, severity, notes)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?, ?)
            ''', (
                hotspot['file'],
                hotspot.get('function_name', ''),
                hotspot.get('severity', 'medium'),
                hotspot.get('notes', '')
            ))
        
        self.conn.commit()
    
    def save_file_health(self, file_path: str, health_score: float, metrics: Dict[str, Any]):
        """Save file health history."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO file_health_history (file, health_score, metrics)
            VALUES (?, ?, ?)
        ''', (
            file_path,
            health_score,
            json.dumps(metrics)
        ))
        
        self.conn.commit()
    
    def get_file_health_trend(self, file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get health trend for a file."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT health_score, scanned_at
            FROM file_health_history
            WHERE file = ?
            ORDER BY scanned_at DESC
            LIMIT ?
        ''', (file_path, limit))
        
        rows = cursor.fetchall()
        
        return [
            {
                'health_score': row['health_score'],
                'scanned_at': row['scanned_at']
            }
            for row in rows
        ]
    
    def get_top_hotspots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top bug hotspots."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT file, function_name, bug_frequency, last_bug_at, severity, notes
            FROM bug_hotspots
            ORDER BY bug_frequency DESC, last_bug_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_unresolved_smells(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get unresolved code smells."""
        cursor = self.conn.cursor()
        
        if file_path:
            cursor.execute('''
                SELECT file, line, smell_type, severity, message, suggestion, detected_at
                FROM code_smells
                WHERE resolved = 0 AND file = ?
                ORDER BY severity DESC, detected_at DESC
            ''', (file_path,))
        else:
            cursor.execute('''
                SELECT file, line, smell_type, severity, message, suggestion, detected_at
                FROM code_smells
                WHERE resolved = 0
                ORDER BY severity DESC, detected_at DESC
            ''')
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def mark_smell_resolved(self, smell_id: int):
        """Mark a code smell as resolved."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            UPDATE code_smells
            SET resolved = 1
            WHERE id = ?
        ''', (smell_id,))
        
        self.conn.commit()
    
    def get_function_history(self, function_id: str) -> List[Dict[str, Any]]:
        """Get health history for a function."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT health_score, complexity, bug_count, churn_rate, calculated_at
            FROM function_risk_scores
            WHERE function_id = ?
            ORDER BY calculated_at DESC
        ''', (function_id,))
        
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
