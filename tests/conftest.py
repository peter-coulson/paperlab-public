"""Pytest configuration and shared fixtures.

Provides test infrastructure for all test modules:
- test_conn: In-memory database with schema loaded
- Automatic cleanup after each test
"""

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from paperlab.config import DatabaseSettings


@pytest.fixture
def test_conn() -> Generator[sqlite3.Connection, None, None]:
    """Provide in-memory SQLite database with schema loaded.

    Creates a fresh database for each test with:
    - Full production schema loaded from data/db/schema.sql
    - Foreign keys enabled
    - Row factory for dict-like access
    - Automatic cleanup after test

    Yields:
        sqlite3.Connection: In-memory database connection with schema
    """
    conn = sqlite3.connect(":memory:")

    try:
        conn.execute(DatabaseSettings.FOREIGN_KEYS_PRAGMA)
        conn.row_factory = sqlite3.Row

        schema_path = Path(__file__).parent.parent / "data" / "db" / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {schema_path}\n"
                f"Expected location: data/db/schema.sql relative to project root"
            )

        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()

        conn.executescript(schema_sql)
        conn.commit()

        yield conn

    finally:
        conn.close()
