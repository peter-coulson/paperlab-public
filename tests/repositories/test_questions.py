"""Tests for questions repository.

Tests public interface: create_question, get_question_structure.
Uses real database via test_conn fixture.
"""

import sqlite3

import pytest

from paperlab.data.repositories.marking import questions

from .conftest import (
    seed_question,
    seed_question_part,
)


class TestCreateQuestion:
    """Tests for questions.create_question()."""

    def test_create_question_returns_valid_id(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """Creating a question returns a positive integer ID."""
        question_id = questions.create_question(
            paper_id=paper_id,
            question_number=1,
            total_marks=5,
            conn=test_conn,
        )

        assert question_id > 0
        assert isinstance(question_id, int)

    def test_create_question_stores_data_correctly(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """Created question has correct values in database."""
        question_id = questions.create_question(
            paper_id=paper_id,
            question_number=3,
            total_marks=8,
            conn=test_conn,
        )

        cursor = test_conn.execute(
            "SELECT paper_id, question_number, total_marks FROM questions WHERE id = ?",
            (question_id,),
        )
        row = cursor.fetchone()

        assert row[0] == paper_id
        assert row[1] == 3
        assert row[2] == 8

    def test_create_question_duplicate_number_raises(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """Creating question with duplicate number for same paper raises IntegrityError."""
        questions.create_question(
            paper_id=paper_id,
            question_number=1,
            total_marks=5,
            conn=test_conn,
        )

        with pytest.raises(sqlite3.IntegrityError):
            questions.create_question(
                paper_id=paper_id,
                question_number=1,
                total_marks=3,
                conn=test_conn,
            )


class TestGetQuestionStructure:
    """Tests for questions.get_question_structure()."""

    def test_get_question_structure_returns_complete_hierarchy(
        self, test_conn: sqlite3.Connection, question_with_parts: tuple[int, list[int]]
    ) -> None:
        """get_question_structure returns question with parts and content blocks."""
        question_id, _ = question_with_parts

        result = questions.get_question_structure(question_id, test_conn)

        assert result["question_id"] == question_id
        assert result["question_number"] == 1
        assert result["total_marks"] == 4
        assert len(result["parts"]) == 2

    def test_get_question_structure_parts_ordered_correctly(
        self, test_conn: sqlite3.Connection, question_with_parts: tuple[int, list[int]]
    ) -> None:
        """Parts are returned in display_order sequence."""
        question_id, part_ids = question_with_parts

        result = questions.get_question_structure(question_id, test_conn)

        # First part is NULL part (display_order=0)
        assert result["parts"][0]["part_letter"] is None
        assert result["parts"][0]["display_order"] == 0

        # Second part is part 'a' (display_order=1)
        assert result["parts"][1]["part_letter"] == "a"
        assert result["parts"][1]["display_order"] == 1

    def test_get_question_structure_includes_content_blocks(
        self, test_conn: sqlite3.Connection, question_with_parts: tuple[int, list[int]]
    ) -> None:
        """Content blocks are included in part structure."""
        question_id, _ = question_with_parts

        result = questions.get_question_structure(question_id, test_conn)

        # Check NULL part has content block
        null_part = result["parts"][0]
        assert len(null_part["content_blocks"]) == 1
        assert null_part["content_blocks"][0]["block_type"] == "text"
        assert "equation" in null_part["content_blocks"][0]["content_text"]

    def test_get_question_structure_not_found_raises(self, test_conn: sqlite3.Connection) -> None:
        """get_question_structure raises ValueError for non-existent question."""
        with pytest.raises(ValueError, match="Question with id=99999 not found"):
            questions.get_question_structure(99999, test_conn)

    def test_get_question_structure_part_without_content(
        self, test_conn: sqlite3.Connection, paper_id: int
    ) -> None:
        """Part with no content blocks returns empty content_blocks list."""
        question_id = seed_question(test_conn, paper_id, question_number=2, total_marks=3)
        seed_question_part(test_conn, question_id, None, None, 0)
        # No content blocks added

        result = questions.get_question_structure(question_id, test_conn)

        assert len(result["parts"]) == 1
        assert result["parts"][0]["content_blocks"] == []
