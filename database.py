"""
Database module for the AI-Based Digital Memory Reconstruction System.
Handles SQLite database initialization, connection management, and all CRUD operations.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.db")

# Maximum allowed upload size: 10 MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initialize the database with all required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Personal',
            tags TEXT DEFAULT '',
            memory_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            extracted_text TEXT DEFAULT '',
            upload_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            sources TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            results_count INTEGER DEFAULT 0,
            searched_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Memory CRUD operations
# ---------------------------------------------------------------------------

def create_memory(
    title: str,
    content: str,
    category: str = "Personal",
    tags: str = "",
    memory_date: Optional[str] = None,
) -> int:
    """Insert a new memory and return its ID."""
    if memory_date is None:
        memory_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO memories (title, content, category, tags, memory_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title.strip(), content.strip(), category, tags.strip(), memory_date),
    )
    conn.commit()
    mem_id = cursor.lastrowid
    conn.close()
    return mem_id


def get_all_memories(
    category_filter: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "DESC",
) -> list[sqlite3.Row]:
    """Return all memories, optionally filtered by category."""
    valid_sort = {"created_at", "memory_date", "title", "updated_at"}
    if sort_by not in valid_sort:
        sort_by = "created_at"
    if sort_order.upper() not in ("ASC", "DESC"):
        sort_order = "DESC"

    conn = get_db_connection()
    if category_filter and category_filter != "All":
        cursor = conn.execute(
            f"SELECT * FROM memories WHERE category = ? ORDER BY {sort_by} {sort_order}",
            (category_filter,),
        )
    else:
        cursor = conn.execute(
            f"SELECT * FROM memories ORDER BY {sort_by} {sort_order}"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_memory_by_id(memory_id: int) -> Optional[sqlite3.Row]:
    """Return a single memory by ID."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def update_memory(
    memory_id: int,
    title: str,
    content: str,
    category: str,
    tags: str,
    memory_date: str,
) -> bool:
    """Update an existing memory. Returns True if a row was updated."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE memories
        SET title = ?, content = ?, category = ?, tags = ?, memory_date = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """,
        (title.strip(), content.strip(), category, tags.strip(), memory_date, memory_id),
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_memory(memory_id: int) -> bool:
    """Delete a memory by ID. Returns True if a row was deleted."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_recent_memories(limit: int = 5) -> list[sqlite3.Row]:
    """Return the most recently created memories."""
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_timeline_memories(
    category_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[sqlite3.Row]:
    """Return memories ordered by memory_date for timeline view."""
    query = "SELECT * FROM memories WHERE 1=1"
    params: list = []

    if category_filter and category_filter != "All":
        query += " AND category = ?"
        params.append(category_filter)
    if date_from:
        query += " AND memory_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND memory_date <= ?"
        params.append(date_to)

    query += " ORDER BY memory_date ASC"
    conn = get_db_connection()
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Document CRUD operations
# ---------------------------------------------------------------------------

def create_document(
    filename: str,
    original_filename: str,
    file_type: str,
    file_size: int,
    extracted_text: str,
) -> int:
    """Insert a new document record and return its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO documents (filename, original_filename, file_type, file_size, extracted_text)
        VALUES (?, ?, ?, ?, ?)
        """,
        (filename, original_filename, file_type, file_size, extracted_text),
    )
    conn.commit()
    doc_id = cursor.lastrowid
    conn.close()
    return doc_id


def get_all_documents() -> list[sqlite3.Row]:
    """Return all documents ordered by upload date descending."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM documents ORDER BY upload_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_document_by_id(doc_id: int) -> Optional[sqlite3.Row]:
    """Return a single document by ID."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def delete_document(doc_id: int) -> Optional[str]:
    """Delete a document by ID. Returns the stored filename if file should be deleted from disk."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = conn.execute("SELECT filename FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if row is None:
        conn.close()
        return None
    stored_filename = row["filename"]
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return stored_filename


# ---------------------------------------------------------------------------
# Chat session operations
# ---------------------------------------------------------------------------

def save_chat_message(
    session_id: str, role: str, message: str, sources: str = ""
) -> None:
    """Save a chat message to the session history."""
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO chat_sessions (session_id, role, message, sources)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, role, message, sources),
    )
    conn.commit()
    conn.close()


def get_chat_history(session_id: str) -> list[sqlite3.Row]:
    """Return all chat messages for a given session, ordered chronologically."""
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM chat_sessions WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def clear_chat_history(session_id: str) -> None:
    """Delete all chat messages for a given session."""
    conn = get_db_connection()
    conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Search history operations
# ---------------------------------------------------------------------------

def save_search(query: str, results_count: int) -> None:
    """Record a search query in search history."""
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO search_history (query, results_count) VALUES (?, ?)",
        (query, results_count),
    )
    conn.commit()
    conn.close()


def get_recent_searches(limit: int = 5) -> list[sqlite3.Row]:
    """Return recent search queries."""
    conn = get_db_connection()
    cursor = conn.execute(
        "SELECT * FROM search_history ORDER BY searched_at DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Dashboard statistics
# ---------------------------------------------------------------------------

def get_dashboard_stats() -> dict:
    """Return aggregate statistics for the dashboard."""
    conn = get_db_connection()
    stats: dict = {
        "total_memories": 0,
        "total_documents": 0,
        "recent_memories": [],
        "recent_searches": [],
        "categories": {},
    }

    cursor = conn.execute("SELECT COUNT(*) as count FROM memories")
    stats["total_memories"] = cursor.fetchone()["count"]

    cursor = conn.execute("SELECT COUNT(*) as count FROM documents")
    stats["total_documents"] = cursor.fetchone()["count"]

    cursor = conn.execute(
        "SELECT category, COUNT(*) as count FROM memories GROUP BY category"
    )
    for row in cursor.fetchall():
        stats["categories"][row["category"]] = row["count"]

    conn.close()

    stats["recent_memories"] = get_recent_memories(5)
    stats["recent_searches"] = get_recent_searches(5)
    return stats


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

def insert_sample_data() -> None:
    """Insert a small set of clearly-labeled sample memories for demonstration."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT COUNT(*) as count FROM memories")
    if cursor.fetchone()["count"] > 0:
        conn.close()
        return

    samples = [
        (
            "Welcome to Memory Reconstruction System",
            "This is a sample memory to help you get started. You can add your own memories using the 'Add Memory' page. Try asking the Reconstruct chat about this information!",
            "Personal",
            "sample, demo, welcome",
            "2026-01-01",
        ),
        (
            "Project Kickoff: Smart Home Automation",
            "The smart home automation project started in January. Key goals include voice-controlled lighting, automated temperature regulation, and a mobile dashboard. Team members: Alice, Bob, and Charlie. Deadline set for June 2026.",
            "Projects",
            "iot, automation, smart-home",
            "2026-01-15",
        ),
        (
            "Machine Learning Course Notes",
            "Completed the supervised learning module. Key concepts: linear regression, logistic regression, decision trees, and random forests. Next module covers neural networks and deep learning fundamentals.",
            "Education",
            "ml, ai, learning, notes",
            "2026-02-10",
        ),
        (
            "Quarterly Team Meeting Summary",
            "Discussed Q1 performance metrics. Revenue up 15% year over year. Key priorities for Q2: improve customer retention, launch the new product feature set, and hire two additional engineers.",
            "Work",
            "meeting, quarterly, metrics",
            "2026-03-05",
        ),
        (
            "Important: Passport Renewal Deadline",
            "Passport expires in August 2026. Need to submit renewal application by May 2026. Required documents: current passport, two photos, address proof, and fee receipt.",
            "Important Events",
            "passport, renewal, deadline, urgent",
            "2026-02-20",
        ),
    ]

    for title, content, category, tags, mem_date in samples:
        cursor.execute(
            """
            INSERT INTO memories (title, content, category, tags, memory_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, content, category, tags, mem_date),
        )

    conn.commit()
    conn.close()
