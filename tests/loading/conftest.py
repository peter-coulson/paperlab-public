"""Pytest fixtures for loading tests.

Provides:
- Paths to real test JSON files
- Reference data seeding for exam_types and mark_types
- Pre-loaded paper fixture for mark scheme tests
"""

import sqlite3
from pathlib import Path

import pytest

from paperlab.data.repositories.marking import exam_types, mark_types

# ============================================================================
# Test Data Paths
# ============================================================================

# Base path for structured paper JSON files
PAPERS_PATH = Path(__file__).parent.parent.parent / "data" / "papers" / "structured"

# Specific test paper paths (Pearson Edexcel GCSE Maths 1H November 2023)
TEST_PAPER_JSON = (
    PAPERS_PATH / "pearson-edexcel" / "gcse" / "mathematics" / "1ma1_1h_2023_11_08.json"
)
TEST_MARKS_JSON = (
    PAPERS_PATH / "pearson-edexcel" / "gcse" / "mathematics" / "1ma1_1h_2023_11_08_marks.json"
)

# Reference data constants (must match JSON files)
EXAM_BOARD = "Pearson Edexcel"
EXAM_LEVEL = "GCSE"
SUBJECT = "Mathematics"
PAPER_CODE = "1MA1/1H"
DISPLAY_NAME = "Paper 1 (Non-Calculator)"


# ============================================================================
# Reference Data Seeding Fixtures
# ============================================================================


@pytest.fixture
def seed_exam_type(test_conn: sqlite3.Connection) -> int:
    """Seed exam_types table with required reference data.

    Must be called before loading papers or marks.

    Returns:
        exam_type_id: ID of the created exam type record
    """
    exam_types.create_exam_types_batch(
        [(EXAM_BOARD, EXAM_LEVEL, SUBJECT, PAPER_CODE, DISPLAY_NAME)],
        test_conn,
    )
    test_conn.commit()

    # Return exam_type_id for downstream fixtures
    return exam_types.get_by_exam_type(EXAM_BOARD, EXAM_LEVEL, SUBJECT, PAPER_CODE, test_conn)


@pytest.fixture
def seed_mark_types(test_conn: sqlite3.Connection, seed_exam_type: int) -> int:
    """Seed mark_types table with required reference data.

    Depends on seed_exam_type fixture.
    Creates all mark types used in Pearson Edexcel GCSE Mathematics.

    Returns:
        exam_type_id: ID of the exam type (passed through from seed_exam_type)
    """
    exam_type_id = seed_exam_type

    # Mark types used in the test JSON files (from exam config)
    mark_type_data = [
        (exam_type_id, "M", "Method Mark", "Awarded for correct mathematical method"),
        (
            exam_type_id,
            "A",
            "Accuracy Mark",
            "Awarded for correct answer following correct working",
        ),
        (exam_type_id, "B", "Independent Mark", "Awarded independent of method"),
        (exam_type_id, "C", "Communication Mark", "Awarded for explanation or justification"),
        (exam_type_id, "P", "Process Mark", "Awarded for setting up appropriate process"),
        (
            exam_type_id,
            "ft",
            "Follow Through",
            "Accuracy mark awarded when following through from earlier error",
        ),
        (
            exam_type_id,
            "SC",
            "Special Case",
            "Mark awarded for unique or alternative solution methods",
        ),
    ]

    mark_types.create_mark_types_batch(mark_type_data, test_conn)
    test_conn.commit()

    return exam_type_id


@pytest.fixture
def loaded_paper(test_conn: sqlite3.Connection, seed_exam_type: int) -> int:
    """Load paper structure into database.

    This fixture loads the paper and returns the paper_id.
    Use this for mark scheme tests that require paper to exist first.

    Returns:
        paper_id: ID of the loaded paper
    """
    from paperlab.loading.paper_loader import load_paper

    # seed_exam_type ensures exam type exists (fixture dependency)
    _ = seed_exam_type

    paper_id = load_paper(str(TEST_PAPER_JSON), test_conn)
    test_conn.commit()

    return paper_id


@pytest.fixture
def loaded_paper_with_marks(
    test_conn: sqlite3.Connection, seed_mark_types: int, loaded_paper: int
) -> int:
    """Load paper with mark types seeded, ready for mark scheme loading.

    Returns:
        paper_id: ID of the loaded paper
    """
    # Silence unused variable warnings - these fixtures ensure DB state
    _ = test_conn
    _ = seed_mark_types

    return loaded_paper
