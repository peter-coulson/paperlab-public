"""Tests for mark_criteria repository.

Tests public interface: create_criterion, get_mark_scheme_for_question.
Uses real database via test_conn fixture.
"""

import sqlite3

import pytest

from paperlab.data.repositories.marking import criteria_content, mark_criteria

from .conftest import (
    MARK_TYPE_A,
    MARK_TYPE_M,
    seed_question,
    seed_question_part,
)


class TestCreateCriterion:
    """Tests for mark_criteria.create_criterion()."""

    def test_create_criterion_returns_valid_id(
        self,
        test_conn: sqlite3.Connection,
        paper_id: int,
        mark_type_ids: dict[str, int],
    ) -> None:
        """Creating a criterion returns a positive integer ID."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=3)
        part_id = seed_question_part(test_conn, question_id, None, None, 0)

        criterion_id = mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_id,
            mark_type_id=mark_type_ids[MARK_TYPE_M],
            criterion_index=0,
            marks_available=1,
            depends_on_criterion_index=None,
            conn=test_conn,
        )

        assert criterion_id > 0
        assert isinstance(criterion_id, int)

    def test_create_criterion_with_dependency(
        self,
        test_conn: sqlite3.Connection,
        paper_id: int,
        mark_type_ids: dict[str, int],
    ) -> None:
        """Creating criterion with dependency stores relationship correctly."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=3)
        part_id = seed_question_part(test_conn, question_id, None, None, 0)

        # Create M mark (criterion_index=0)
        mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_id,
            mark_type_id=mark_type_ids[MARK_TYPE_M],
            criterion_index=0,
            marks_available=1,
            depends_on_criterion_index=None,
            conn=test_conn,
        )

        # Create A mark (criterion_index=1) depending on M mark
        a_criterion_id = mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_id,
            mark_type_id=mark_type_ids[MARK_TYPE_A],
            criterion_index=1,
            marks_available=1,
            depends_on_criterion_index=0,
            conn=test_conn,
        )

        cursor = test_conn.execute(
            "SELECT depends_on_criterion_index FROM mark_criteria WHERE id = ?",
            (a_criterion_id,),
        )
        row = cursor.fetchone()
        assert row[0] == 0

    def test_create_criterion_duplicate_index_raises(
        self,
        test_conn: sqlite3.Connection,
        paper_id: int,
        mark_type_ids: dict[str, int],
    ) -> None:
        """Creating criterion with duplicate criterion_index raises IntegrityError."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=3)
        part_id = seed_question_part(test_conn, question_id, None, None, 0)

        mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_id,
            mark_type_id=mark_type_ids[MARK_TYPE_M],
            criterion_index=0,
            marks_available=1,
            depends_on_criterion_index=None,
            conn=test_conn,
        )

        with pytest.raises(sqlite3.IntegrityError):
            mark_criteria.create_criterion(
                question_id=question_id,
                part_id=part_id,
                mark_type_id=mark_type_ids[MARK_TYPE_A],
                criterion_index=0,  # Duplicate index
                marks_available=1,
                depends_on_criterion_index=None,
                conn=test_conn,
            )


class TestGetMarkSchemeForQuestion:
    """Tests for mark_criteria.get_mark_scheme_for_question()."""

    def test_get_mark_scheme_returns_criteria_grouped_by_part(
        self,
        test_conn: sqlite3.Connection,
        paper_id: int,
        mark_type_ids: dict[str, int],
    ) -> None:
        """get_mark_scheme_for_question returns criteria grouped by part."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=4)
        part_null = seed_question_part(test_conn, question_id, None, None, 0)
        part_a = seed_question_part(test_conn, question_id, "a", None, 1)

        # Create criterion for NULL part
        mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_null,
            mark_type_id=mark_type_ids[MARK_TYPE_M],
            criterion_index=0,
            marks_available=1,
            depends_on_criterion_index=None,
            conn=test_conn,
        )

        # Create criterion for part (a)
        mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_a,
            mark_type_id=mark_type_ids[MARK_TYPE_A],
            criterion_index=1,
            marks_available=2,
            depends_on_criterion_index=None,
            conn=test_conn,
        )

        result = mark_criteria.get_mark_scheme_for_question(question_id, test_conn)

        assert len(result) == 2

        # First part is NULL part
        assert result[0]["part_letter"] is None
        assert len(result[0]["criteria"]) == 1
        assert result[0]["criteria"][0]["marks_available"] == 1

        # Second part is part 'a'
        assert result[1]["part_letter"] == "a"
        assert len(result[1]["criteria"]) == 1
        assert result[1]["criteria"][0]["marks_available"] == 2

    def test_get_mark_scheme_includes_mark_type_info(
        self,
        test_conn: sqlite3.Connection,
        paper_id: int,
        mark_type_ids: dict[str, int],
    ) -> None:
        """Mark scheme includes mark type code and name."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=2)
        part_id = seed_question_part(test_conn, question_id, None, None, 0)

        mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_id,
            mark_type_id=mark_type_ids[MARK_TYPE_M],
            criterion_index=0,
            marks_available=2,
            depends_on_criterion_index=None,
            conn=test_conn,
        )

        result = mark_criteria.get_mark_scheme_for_question(question_id, test_conn)

        criterion = result[0]["criteria"][0]
        assert criterion["mark_type_code"] == "M"
        assert criterion["mark_type_name"] == "Method"

    def test_get_mark_scheme_includes_content_blocks(
        self,
        test_conn: sqlite3.Connection,
        paper_id: int,
        mark_type_ids: dict[str, int],
    ) -> None:
        """Mark scheme includes criterion content blocks."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=2)
        part_id = seed_question_part(test_conn, question_id, None, None, 0)

        criterion_id = mark_criteria.create_criterion(
            question_id=question_id,
            part_id=part_id,
            mark_type_id=mark_type_ids[MARK_TYPE_M],
            criterion_index=0,
            marks_available=2,
            depends_on_criterion_index=None,
            conn=test_conn,
        )

        # Add content block to criterion
        criteria_content.create_content_block(
            criterion_id=criterion_id,
            block_type="text",
            display_order=0,
            content_text="Award for correct method shown",
            diagram_description=None,
            conn=test_conn,
        )

        result = mark_criteria.get_mark_scheme_for_question(question_id, test_conn)

        criterion = result[0]["criteria"][0]
        assert len(criterion["content_blocks"]) == 1
        assert criterion["content_blocks"][0]["block_type"] == "text"
        assert "correct method" in criterion["content_blocks"][0]["content_text"]

    def test_get_mark_scheme_empty_for_question_without_criteria(
        self,
        test_conn: sqlite3.Connection,
        paper_id: int,
    ) -> None:
        """get_mark_scheme_for_question returns empty list if no criteria exist."""
        question_id = seed_question(test_conn, paper_id, question_number=1, total_marks=2)
        seed_question_part(test_conn, question_id, None, None, 0)
        # No criteria added

        result = mark_criteria.get_mark_scheme_for_question(question_id, test_conn)

        assert result == []
