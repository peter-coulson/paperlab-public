"""Fixtures for API tests.

Provides:
- TestClient with database override
- Auth fixtures for authenticated requests
- R2Storage mock
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from paperlab.api.auth import DEV_TOKEN
from paperlab.api.main import app
from paperlab.config import DatabaseSettings


def _mock_decode_supabase_jwt(token: str) -> dict[str, str]:
    """Mock JWT decoder that rejects all tokens (dev token handled separately)."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


@pytest.fixture
def api_test_conn() -> Generator[sqlite3.Connection, None, None]:
    """Provide in-memory SQLite database for API tests.

    Unlike the root test_conn fixture, this allows cross-thread access
    which is required because TestClient runs requests in a separate thread.

    Yields:
        sqlite3.Connection: In-memory database connection with schema
    """
    # check_same_thread=False allows TestClient's request thread to use the connection
    conn = sqlite3.connect(":memory:", check_same_thread=False)

    try:
        conn.execute(DatabaseSettings.FOREIGN_KEYS_PRAGMA)
        conn.row_factory = sqlite3.Row

        schema_path = Path(__file__).parent.parent.parent / "data" / "db" / "schema.sql"

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


@pytest.fixture
def mock_r2() -> MagicMock:
    """Create mock R2Storage that returns dummy URLs."""
    mock = MagicMock()
    mock.generate_presigned_upload_url.return_value = "https://mock-r2.example.com/upload"
    mock.generate_presigned_download_url.return_value = "https://mock-r2.example.com/download"
    mock.copy_to_permanent.return_value = None
    mock.delete_staging_images.return_value = None
    mock.list_staging_objects.return_value = []
    return mock


@pytest.fixture
def client(
    api_test_conn: sqlite3.Connection, mock_r2: MagicMock
) -> Generator[TestClient, None, None]:
    """Provide TestClient with mocked database and R2 storage.

    Args:
        api_test_conn: In-memory database with schema loaded (cross-thread safe)
        mock_r2: Mocked R2Storage

    Yields:
        TestClient configured for testing
    """

    # Create a context manager that yields our test connection
    @contextmanager
    def mock_connection(*args: Any, **kwargs: Any) -> Generator[sqlite3.Connection, None, None]:
        yield api_test_conn

    # Patch the connection function, R2Storage, environment, and JWT decoder
    with (
        patch("paperlab.api.main.connection", mock_connection),
        patch("paperlab.api.auth.connection", mock_connection),
        patch("paperlab.api.main.R2Storage", return_value=mock_r2),
        patch("paperlab.api.auth.settings.environment", "development"),
        patch("paperlab.api.auth._decode_supabase_jwt", _mock_decode_supabase_jwt),
        TestClient(app) as test_client,
    ):
        yield test_client


@pytest.fixture
def auth_headers(api_test_conn: sqlite3.Connection) -> dict[str, str]:
    """Provide auth headers using dev token.

    Creates test student in database and returns dev token Authorization header.
    Dev token bypasses JWT verification in development mode.
    """
    # Insert test student with known Supabase UID
    # (matches DatabaseSettings.TEST_STUDENT_SUPABASE_UID)
    api_test_conn.execute(
        """
        INSERT INTO students (id, supabase_uid)
        VALUES (1, ?)
        """,
        (DatabaseSettings.TEST_STUDENT_SUPABASE_UID,),
    )
    api_test_conn.commit()

    # Use dev token (bypasses JWT verification in development mode)
    return {"Authorization": f"Bearer {DEV_TOKEN}"}


@pytest.fixture
def seed_paper_data(api_test_conn: sqlite3.Connection) -> dict[str, int | list[int]]:
    """Seed database with exam type, paper, and questions.

    Returns dict with created IDs:
        - exam_type_id: int
        - paper_id: int
        - question_ids: list[int]
    """
    # Create exam type
    cursor = api_test_conn.execute(
        """
        INSERT INTO exam_types (exam_board, exam_level, subject, paper_code, display_name)
        VALUES ('pearson-edexcel', 'gcse', 'mathematics', '1MA1/3H', 'GCSE Maths Paper 3H')
        """
    )
    exam_type_id = cursor.lastrowid
    assert exam_type_id is not None

    # Create paper
    cursor = api_test_conn.execute(
        """
        INSERT INTO papers (exam_type_id, exam_date, total_marks, exam_identifier)
        VALUES (?, '2023-11-13', 80, 'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-3H-2023-11-13')
        """,
        (exam_type_id,),
    )
    paper_id = cursor.lastrowid
    assert paper_id is not None

    # Create questions (3 questions for testing)
    question_ids: list[int] = []
    for q_num in range(1, 4):
        cursor = api_test_conn.execute(
            """
            INSERT INTO questions (paper_id, question_number, total_marks)
            VALUES (?, ?, ?)
            """,
            (paper_id, q_num, 5),
        )
        question_id = cursor.lastrowid
        assert question_id is not None
        question_ids.append(question_id)

        # Create question part (required for question structure)
        part_id = api_test_conn.execute(
            """
            INSERT INTO question_parts (question_id, display_order)
            VALUES (?, 1)
            """,
            (question_id,),
        ).lastrowid
        assert part_id is not None

        # Create content block for part
        api_test_conn.execute(
            """
            INSERT INTO question_content_blocks
                (question_part_id, block_type, display_order, content_text)
            VALUES (?, 'text', 1, 'Solve the equation.')
            """,
            (part_id,),
        )

    api_test_conn.commit()

    return {
        "exam_type_id": exam_type_id,
        "paper_id": paper_id,
        "question_ids": question_ids,
    }
