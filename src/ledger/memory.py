"""
Episodic User Preference Memory Store (SQLite + FTS5).
Retains tax classification memories, merchant categorization overrides,
and previous vendor matching heuristics across sessions.
"""
import sqlite3
from typing import Optional, List, Dict
from config import settings

class EpisodicMemoryStore:
    """Manages persistent SQLite memory with full-text search capability."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or settings.SQLITE_PATH)
        self.conn = sqlite3.connect(self.db_path)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_preferences (
                vendor_key TEXT PRIMARY KEY,
                preferred_category TEXT NOT NULL,
                notes TEXT,
                confidence REAL DEFAULT 1.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # FTS5 virtual table for semantic pattern search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_search USING fts5(
                vendor_key,
                notes,
                preferred_category
            );
        """)
        self.conn.commit()

    def remember_vendor_category(self, vendor: str, category: str, notes: str = "") -> None:
        """Stores or updates episodic recollection of user categorization preference."""
        vendor_clean = vendor.strip().lower()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO vendor_preferences (vendor_key, preferred_category, notes)
            VALUES (?, ?, ?)
            ON CONFLICT(vendor_key) DO UPDATE SET
                preferred_category = excluded.preferred_category,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP;
        """, (vendor_clean, category, notes))

        cursor.execute("""
            INSERT INTO memory_search (vendor_key, notes, preferred_category)
            VALUES (?, ?, ?);
        """, (vendor_clean, notes, category))
        self.conn.commit()

    def recall_vendor_category(self, vendor: str) -> Optional[str]:
        """Recalls preferred classification category for a given merchant string."""
        vendor_clean = vendor.strip().lower()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT preferred_category FROM vendor_preferences WHERE vendor_key = ?",
            (vendor_clean,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        # Try partial match
        cursor.execute(
            "SELECT preferred_category FROM vendor_preferences WHERE ? LIKE '%' || vendor_key || '%' LIMIT 1",
            (vendor_clean,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def get_all_memories(self) -> List[Dict[str, str]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT vendor_key, preferred_category, notes, updated_at FROM vendor_preferences")
        return [
            {"vendor": r[0], "category": r[1], "notes": r[2], "updated_at": r[3]}
            for r in cursor.fetchall()
        ]

    def close(self) -> None:
        self.conn.close()
