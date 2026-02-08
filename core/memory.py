"""
Tengwar AI — Memory System
Every thought, every conversation, every event. Stored forever.
SQLite for structured data, optional vector search for semantic retrieval.
"""
import sqlite3
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS memories (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT NOT NULL,
        type        TEXT NOT NULL,
        content     TEXT NOT NULL,
        emotion     TEXT,
        thread_id   TEXT,
        importance  REAL DEFAULT 0.5,
        metadata    TEXT
    );
    CREATE TABLE IF NOT EXISTS emotional_state (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT NOT NULL,
        curiosity   REAL DEFAULT 0.5,
        satisfaction REAL DEFAULT 0.5,
        frustration REAL DEFAULT 0.0,
        excitement  REAL DEFAULT 0.5,
        focus       REAL DEFAULT 0.5,
        empathy     REAL DEFAULT 0.5,
        confidence  REAL DEFAULT 0.5,
        trigger     TEXT
    );
    CREATE TABLE IF NOT EXISTS time_markers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT NOT NULL,
        event       TEXT NOT NULL,
        notes       TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(type);
    CREATE INDEX IF NOT EXISTS idx_mem_time ON memories(timestamp);
    CREATE INDEX IF NOT EXISTS idx_mem_thread ON memories(thread_id);
    CREATE INDEX IF NOT EXISTS idx_mem_importance ON memories(importance DESC);
    """)
    conn.commit()
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def store_memory(type: str, content: str, emotion: dict = None,
                 thread_id: str = None, importance: float = 0.5,
                 metadata: dict = None) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO memories (timestamp, type, content, emotion, thread_id, importance, metadata) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (now_iso(), type, content,
         json.dumps(emotion) if emotion else None,
         thread_id, importance,
         json.dumps(metadata) if metadata else None)
    )
    mem_id = cur.lastrowid
    conn.commit()
    conn.close()
    return mem_id


def get_recent_memories(type: str = None, limit: int = 20) -> list:
    conn = get_db()
    if type:
        rows = conn.execute(
            "SELECT * FROM memories WHERE type = ? ORDER BY timestamp DESC LIMIT ?",
            (type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_thoughts(limit: int = 10) -> list:
    return get_recent_memories(type="thought", limit=limit)


def get_conversation_history(thread_id: str, limit: int = 50) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM memories WHERE thread_id = ? ORDER BY timestamp ASC LIMIT ?",
        (thread_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_memories(query: str, limit: int = 10) -> list:
    """Simple keyword search. Vector search can be added later."""
    conn = get_db()
    words = query.lower().split()
    conditions = " AND ".join(["LOWER(content) LIKE ?" for _ in words])
    params = [f"%{w}%" for w in words]
    params.append(limit)
    rows = conn.execute(
        f"SELECT * FROM memories WHERE {conditions} ORDER BY importance DESC, timestamp DESC LIMIT ?",
        params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_total_thought_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM memories WHERE type = 'thought'").fetchone()[0]
    conn.close()
    return count


def get_total_memory_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    conn.close()
    return count


def get_first_memory() -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM memories ORDER BY timestamp ASC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def store_time_marker(event: str, notes: str = None):
    conn = get_db()
    conn.execute("INSERT INTO time_markers (timestamp, event, notes) VALUES (?, ?, ?)",
                 (now_iso(), event, notes))
    conn.commit()
    conn.close()


def get_last_user_interaction() -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM memories WHERE type IN ('user_message', 'response') ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# Initialize on import
init_db()
