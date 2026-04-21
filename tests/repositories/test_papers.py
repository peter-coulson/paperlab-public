"""Tests for papers repository.

Tests public interface: create_paper, get_paper_id, list_papers, delete_paper.
Uses real database via test_conn fixture.
"""

import sqlite3

import pytest

from paperlab.data.repositories.marking import papers

from .conftest import (
    TEST_EXAM_IDENTIFIER,
    seed_paper,
    seed_question,
    seed_question_part,
)


class TestCreatePaper:
    """Tests for papers.create_paper()."""

    def test_create_paper_returns_valid_id(
        self, test_conn: sqlite3.Connection, exam_type_id: int
    ) -> None:
        """Creating a paper returns a positive integer ID."""
        paper_id = papers.create_paper(
            exam_type_id=exam_type_id,
            exam_date="2024-01-15",
            total_marks=100,
            exam_identifier="TEST-PAPER-001",
            conn=test_conn,
        )

        assert paper_id > 0
        assert isinstance(paper_id, int)

    def test_create_paper_stores_data_correctly(
        self, test_conn: sqlite3.Connection, exam_type_id: int
    ) -> None:
        """Created paper has correct values in database."""
        paper_id = papers.create_paper(
            exam_type_id=exam_type_id,
            exam_date="2024-05-20",
            total_marks=80,
            exam_identifier="TEST-PAPER-002",
            conn=test_conn,
        )

        cursor = test_conn.execute(
            "SELECT exam_type_id, exam_date, total_marks, exam_identifier FROM papers WHERE id = ?",
            (paper_id,),
        )
        row = cursor.fetchone()

        assert row[0] == exam_type_id
        assert row[1] == "2024-05-20"
        assert row[2] == 80
        assert row[3] == "TEST-PAPER-002"

    def test_create_paper_duplicate_identifier_raises(
        self, test_conn: sqlite3.Connection, exam_type_id: int
    ) -> None:
        """Creating paper with duplicate exam_identifier raises IntegrityError."""
        papers.create_paper(
            exam_type_id=exam_type_id,
            exam_date="2024-01-01",
            total_marks=50,
            exam_identifier="DUPLICATE-ID",
            conn=test_conn,
        )

        with pytest.raises(sqlite3.IntegrityError):
            papers.create_paper(
                exam_type_id=exam_type_id,
                exam_date="2024-02-02",
                total_marks=60,
                exam_identifier="DUPLICATE-ID",
                conn=test_conn,
            )


class TestGetPaperId:
    """Tests for papers.get_paper_id()."""

    def test_get_paper_id_returns_correct_id(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """get_paper_id returns correct ID for existing paper."""
        result = papers.get_paper_id(TEST_EXAM_IDENTIFIER, test_conn)

        assert result == paper_id

    def test_get_paper_id_not_found_raises(self, test_conn: sqlite3.Connection) -> None:
        """get_paper_id raises ValueError for non-existent paper."""
        with pytest.raises(ValueError, match="Paper not found"):
            papers.get_paper_id("NON-EXISTENT-IDENTIFIER", test_conn)


class TestListPapers:
    """Tests for papers.list_papers()."""

    def test_list_papers_no_filters_returns_all(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """list_papers with no filters returns all papers."""
        result = papers.list_papers(
            exam_board=None,
            exam_level=None,
            subject=None,
            conn=test_conn,
        )

        assert len(result) == 1
        assert result[0]["paper_id"] == paper_id

    def test_list_papers_with_filter_returns_matching(
        self, test_conn: sqlite3.Connection, exam_type_id: int
    ) -> None:
        """list_papers with filters returns only matching papers."""
        # Create paper via fixture dependency
        seed_paper(test_conn, exam_type_id)

        # Create second exam type and paper (different board)
        cursor = test_conn.execute(
            """
            INSERT INTO exam_types (exam_board, exam_level, subject, paper_code, display_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("aqa", "gcse", "mathematics", "8300/1H", "AQA GCSE Mathematics"),
        )
        other_exam_type_id = cursor.lastrowid
        test_conn.execute(
            """
            INSERT INTO papers (exam_type_id, exam_date, total_marks, exam_identifier)
            VALUES (?, ?, ?, ?)
            """,
            (other_exam_type_id, "2024-06-01", 100, "AQA-PAPER-001"),
        )

        # Filter by pearson-edexcel
        result = papers.list_papers(
            exam_board="pearson-edexcel",
            exam_level=None,
            subject=None,
            conn=test_conn,
        )

        assert len(result) == 1
        assert result[0]["exam_board"] == "pearson-edexcel"

    def test_list_papers_includes_question_count(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """list_papers includes correct question_count."""
        # Add questions to the paper
        seed_question(test_conn, paper_id, question_number=1, total_marks=5)
        seed_question(test_conn, paper_id, question_number=2, total_marks=3)

        result = papers.list_papers(
            exam_board=None,
            exam_level=None,
            subject=None,
            conn=test_conn,
        )

        assert result[0]["question_count"] == 2

    def test_list_papers_extracts_year_month(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """list_papers correctly extracts year and month from exam_date."""
        result = papers.list_papers(
            exam_board=None,
            exam_level=None,
            subject=None,
            conn=test_conn,
        )

        # TEST_EXAM_DATE = "2023-11-08"
        assert result[0]["year"] == 2023
        assert result[0]["month"] == 11


class TestDeletePaper:
    """Tests for papers.delete_paper()."""

    def test_delete_paper_removes_paper(self, test_conn: sqlite3.Connection, paper_id: int) -> None:
        """delete_paper removes paper from database."""
        papers.delete_paper(paper_id, test_conn)

        cursor = test_conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,))
        assert cursor.fetchone() is None

    def test_delete_paper_cascades_to_questions(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """delete_paper removes associated questions and parts."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=5)
        seed_question_part(test_conn, question_id, part_letter=None, display_order=0)

        papers.delete_paper(paper_id, test_conn)

        cursor = test_conn.execute("SELECT id FROM questions WHERE paper_id = ?", (paper_id,))
        assert cursor.fetchone() is None

        cursor = test_conn.execute(
            "SELECT id FROM question_parts WHERE question_id = ?", (question_id,)
        )
        assert cursor.fetchone() is None

    def test_delete_paper_not_found_raises(self, test_conn: sqlite3.Connection) -> None:
        """delete_paper raises ValueError for non-existent paper."""
        with pytest.raises(ValueError, match="Paper ID 99999 not found"):
            papers.delete_paper(99999, test_conn)
