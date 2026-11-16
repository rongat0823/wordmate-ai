"""SQLite access for WordMate AI. Data is stored in the Docker named volume."""
import sqlite3
from pathlib import Path

DB_PATH = Path('/data/vocabulary.db')


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            explanation TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_vocabulary_unique_word
                        ON vocabulary (LOWER(TRIM(word)))''')


def save_word(word: str, explanation: str) -> int:
    with connect() as conn:
        cursor = conn.execute(
            'INSERT INTO vocabulary (word, explanation) VALUES (?, ?)',
            (word.strip(), explanation)
        )
        return cursor.lastrowid


def get_words() -> list[dict]:
    with connect() as conn:
        rows = conn.execute('''SELECT id, word, explanation, created_at
                               FROM vocabulary ORDER BY id DESC''').fetchall()
        return [dict(row) for row in rows]


def get_word_by_id(word_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute('''SELECT id, word, explanation, created_at
                              FROM vocabulary WHERE id = ?''', (word_id,)).fetchone()
        return dict(row) if row else None


def delete_word(word_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute('DELETE FROM vocabulary WHERE id = ?', (word_id,))
        return cursor.rowcount > 0


def clear_test_words() -> int:
    """Developer-only Python helper: not exposed as an unauthenticated HTTP endpoint."""
    with connect() as conn:
        cursor = conn.execute('DELETE FROM vocabulary')
        return cursor.rowcount
