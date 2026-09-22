"""
SQLite database for tracking processed finance news.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DATABASE_PATH = Path("news.db")


def initialize_database() -> None:
    """Create the processed articles table if it does not exist."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_articles (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                processed_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def is_article_processed(url: str) -> bool:
    """Return True if an article URL has already been processed."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "SELECT 1 FROM processed_articles WHERE url = ?",
            (url,),
        )
        return cursor.fetchone() is not None


def mark_article_processed(
    url: str,
    title: str,
    processed_at: str,
) -> None:
    """Mark an article as processed."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO processed_articles
            (url, title, processed_at)
            VALUES (?, ?, ?)
            """,
            (url, title, processed_at),
        )
        connection.commit()
