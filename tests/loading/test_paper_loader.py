"""Tests for paper structure loading.

Tests:
1. Valid JSON loads correctly - creates paper, questions, parts, content blocks
2. Missing exam_type reference fails gracefully
3. Invalid JSON structure is rejected by Pydantic validation
4. Verification counts match expected values
"""

import pytest
from pydantic import ValidationError

from paperlab.data.repositories.marking import (
    grade_boundaries,
    papers,
    question_parts,
    questions,
)
from paperlab.loading.paper_loader import load_paper, verify_paper_loaded
from tests.loading.conftest import (
    TEST_PAPER_JSON,
)


class TestPaperLoadSuccess:
    """Test successful paper loading scenarios."""

    def test_valid_paper_json_loads_correctly(self, test_conn, seed_exam_type):
        """Test that valid paper JSON creates all expected database records."""
        # Act
        paper_id = load_paper(str(TEST_PAPER_JSON), test_conn)
        test_conn.commit()

        # Assert - Paper created
        assert paper_id is not None
        assert paper_id > 0

        # Assert - Paper metadata correct
        paper = papers.get_paper_full(paper_id, test_conn)
        assert paper["total_marks"] == 80
        assert paper["exam_identifier"] == "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08"

    def test_paper_creates_correct_question_count(self, test_conn, seed_exam_type):
        """Test that paper loading creates the expected number of questions."""
        # Act
        paper_id = load_paper(str(TEST_PAPER_JSON), test_conn)
        test_conn.commit()

        # Assert - 22 questions in the paper
        question_count = questions.count_questions(paper_id, test_conn)
        assert question_count == 22

    def test_paper_creates_question_parts(self, test_conn, seed_exam_type):
        """Test that paper loading creates question parts correctly."""
        # Act
        paper_id = load_paper(str(TEST_PAPER_JSON), test_conn)
        test_conn.commit()

        # Assert - Check parts count (each question has at least NULL part)
        parts_count = question_parts.count_parts(paper_id, test_conn)
        assert parts_count > 22  # More parts than questions (multi-part questions)

    def test_paper_creates_grade_boundaries(self, test_conn, seed_exam_type):
        """Test that paper loading creates grade boundaries."""
        # Act
        paper_id = load_paper(str(TEST_PAPER_JSON), test_conn)
        test_conn.commit()

        # Assert - Grade boundaries created (7 grades in JSON + auto-added U = 8)
        boundary_count = grade_boundaries.count_boundaries_for_paper(paper_id, test_conn)
        assert boundary_count == 8  # Grades 9,8,7,6,5,4,3 + U


class TestPaperLoadValidation:
    """Test paper loading validation failures."""

    def test_missing_exam_type_raises_value_error(self, test_conn):
        """Test that loading without seeding exam_type raises ValueError."""
        # Act & Assert - No seed_exam_type fixture, so exam_type lookup fails
        with pytest.raises(ValueError, match="Exam type not found"):
            load_paper(str(TEST_PAPER_JSON), test_conn)

    def test_nonexistent_file_raises_file_not_found(self, test_conn, seed_exam_type):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="JSON file not found"):
            load_paper("/nonexistent/path/paper.json", test_conn)

    def test_invalid_json_raises_validation_error(self, test_conn, seed_exam_type, tmp_path):
        """Test that malformed JSON raises JSONDecodeError."""
        import json

        # Create invalid JSON file (syntactically valid but wrong structure)
        invalid_json_path = tmp_path / "invalid_paper.json"
        invalid_json_path.write_text(json.dumps({"invalid": "structure"}))

        with pytest.raises(ValidationError):
            load_paper(str(invalid_json_path), test_conn)


class TestPaperVerification:
    """Test paper verification logic."""

    def test_verify_paper_loaded_success(self, test_conn, seed_exam_type):
        """Test that verification passes for correctly loaded paper."""
        # Arrange
        paper_id = load_paper(str(TEST_PAPER_JSON), test_conn)
        test_conn.commit()

        # Act & Assert - Should not raise
        # Expected counts from the JSON file:
        # - 22 questions
        # - Variable parts (need to count from JSON)
        # - Variable content blocks
        # - 8 grade boundaries (7 + U)
        question_count = questions.count_questions(paper_id, test_conn)
        parts_count = question_parts.count_parts(paper_id, test_conn)
        blocks_count = papers.count_content_blocks(paper_id, test_conn)
        boundaries_count = grade_boundaries.count_boundaries_for_paper(paper_id, test_conn)

        # Verification should pass
        verify_paper_loaded(
            paper_id,
            expected_questions=question_count,
            expected_parts=parts_count,
            expected_blocks=blocks_count,
            expected_boundaries=boundaries_count,
            conn=test_conn,
        )

    def test_verify_paper_loaded_fails_on_count_mismatch(self, test_conn, seed_exam_type):
        """Test that verification fails when counts don't match."""
        # Arrange
        paper_id = load_paper(str(TEST_PAPER_JSON), test_conn)
        test_conn.commit()

        # Act & Assert - Wrong expected counts should raise
        with pytest.raises(ValueError, match="Question count mismatch"):
            verify_paper_loaded(
                paper_id,
                expected_questions=999,  # Wrong count
                expected_parts=0,
                expected_blocks=0,
                expected_boundaries=0,
                conn=test_conn,
            )
