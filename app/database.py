"""
Database management for Cavern Wireless.
Handles SQLite operations, schema creation, and safe transactions.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        # Convert to Path if string
        self.db_path = Path(db_path) if not isinstance(db_path, Path) else db_path
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()
        
    @contextmanager
    def get_cursor(self):
        """Context manager for safe database transactions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            conn.close()
    
    def init_schema(self):
        """Create tables if they don't exist."""
        with self.get_cursor() as cursor:
            # Stories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_number TEXT UNIQUE NOT NULL,
                    submission_hash TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    story_title TEXT NOT NULL,
                    story_text TEXT NOT NULL,
                    message_to_host TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by_admin INTEGER DEFAULT 0,
                    rejection_reason TEXT
                )
            """)
            
            # Playback history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS playback_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id INTEGER NOT NULL,
                    ticket_number TEXT NOT NULL,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds INTEGER,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                )
            """)
            
            # System settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON stories(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON stories(submission_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_approved ON stories(approved_by_admin)")
            
            # Initialize default settings
            cursor.execute("""
                INSERT OR IGNORE INTO system_settings (key, value) 
                VALUES ('last_ticket_number', '0')
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO system_settings (key, value) 
                VALUES ('playback_status', 'IDLE')
            """)
            
        logger.info("Database schema initialized.")
    
    def generate_ticket_number(self) -> str:
        """Generate next sequential ticket number atomically."""
        with self.get_cursor() as cursor:
            # Get current last number
            cursor.execute("SELECT value FROM system_settings WHERE key = 'last_ticket_number'")
            row = cursor.fetchone()
            current_num = int(row['value']) if row else 0
            
            # Increment
            new_num = current_num + 1
            ticket = f"#{new_num:03d}"
            
            # Update
            cursor.execute("""
                UPDATE system_settings 
                SET value = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE key = 'last_ticket_number'
            """, (str(new_num),))
            
            return ticket
    
    def story_exists(self, submission_hash: str) -> bool:
        """Check if a story with this hash already exists."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT id FROM stories WHERE submission_hash = ?", (submission_hash,))
            return cursor.fetchone() is not None
    
    def add_story(self, name: str, title: str, text: str, message: str, 
                  submission_hash: str, requires_approval: bool = False) -> Optional[str]:
        """
        Add a new story to the queue.
        Returns ticket number if successful, None if duplicate.
        """
        if self.story_exists(submission_hash):
            logger.warning(f"Duplicate story detected (hash: {submission_hash[:8]}...)")
            return None
        
        ticket = self.generate_ticket_number()
        
        initial_status = 'PENDING_APPROVAL' if requires_approval else 'QUEUED'
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO stories 
                (ticket_number, submission_hash, name, story_title, story_text, 
                 message_to_host, status, approved_by_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticket, submission_hash, name, title, text, message, initial_status, 0 if requires_approval else 1))
            
        logger.info(f"Story added: {ticket} by {name}")
        return ticket
    
    def approve_story(self, story_id: int) -> bool:
        """Approve a pending story."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE stories 
                SET status = 'QUEUED', approved_by_admin = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'PENDING_APPROVAL'
            """, (story_id,))
            return cursor.rowcount > 0
    
    def reject_story(self, story_id: int, reason: str) -> bool:
        """Reject a pending story."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE stories 
                SET status = 'REJECTED', rejection_reason = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'PENDING_APPROVAL'
            """, (reason, story_id))
            return cursor.rowcount > 0
    
    def get_next_queued_story(self) -> Optional[Dict[str, Any]]:
        """Get the oldest queued story (FIFO)."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM stories 
                WHERE status = 'QUEUED' 
                ORDER BY created_at ASC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def mark_playing(self, story_id: int) -> bool:
        """Mark story as currently playing."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE stories 
                SET status = 'PLAYING', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (story_id,))
            return cursor.rowcount > 0
    
    def mark_completed(self, story_id: int, duration: int = 0) -> bool:
        """Mark story as completed and log to history."""
        with self.get_cursor() as cursor:
            # Update status
            cursor.execute("""
                UPDATE stories 
                SET status = 'COMPLETED', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (story_id,))
            
            # Get ticket for history
            cursor.execute("SELECT ticket_number FROM stories WHERE id = ?", (story_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    INSERT INTO playback_history (story_id, ticket_number, duration_seconds)
                    VALUES (?, ?, ?)
                """, (story_id, row['ticket_number'], duration))
                
            return cursor.rowcount > 0
    
    def mark_failed(self, story_id: int, reason: str) -> bool:
        """Mark story as failed."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE stories 
                SET status = 'FAILED', rejection_reason = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (reason, story_id))
            return cursor.rowcount > 0
    
    def recover_playing_story(self) -> Optional[int]:
        """Find any story stuck in PLAYING status and reset to QUEUED."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM stories WHERE status = 'PLAYING'
            """)
            rows = cursor.fetchall()
            
            recovered_count = 0
            for row in rows:
                cursor.execute("""
                    UPDATE stories SET status = 'QUEUED', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (row['id'],))
                recovered_count += 1
                logger.info(f"Recovered stuck story ID {row['id']}")
                
            return recovered_count
    
    def get_all_stories(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent stories for dashboard."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM stories 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_queue_count(self) -> int:
        """Count stories in queue."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM stories WHERE status = 'QUEUED'")
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def get_current_playing(self) -> Optional[Dict[str, Any]]:
        """Get currently playing story."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM stories WHERE status = 'PLAYING' LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_story(self, story_id: int) -> bool:
        """Delete a story (admin function)."""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
            return cursor.rowcount > 0
    
    def retry_failed_story(self, story_id: int) -> bool:
        """Reset a failed story to queued."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE stories 
                SET status = 'QUEUED', rejection_reason = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'FAILED'
            """, (story_id,))
            return cursor.rowcount > 0
    
    def pause_playback(self) -> bool:
        """Set global playback status to PAUSED."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE system_settings 
                SET value = 'PAUSED', updated_at = CURRENT_TIMESTAMP 
                WHERE key = 'playback_status'
            """)
            return True
    
    def resume_playback(self) -> bool:
        """Set global playback status to PLAYING."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE system_settings 
                SET value = 'ACTIVE', updated_at = CURRENT_TIMESTAMP 
                WHERE key = 'playback_status'
            """)
            return True
    
    def get_playback_status(self) -> str:
        """Get current playback status."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT value FROM system_settings WHERE key = 'playback_status'")
            row = cursor.fetchone()
            return row['value'] if row else 'IDLE'
