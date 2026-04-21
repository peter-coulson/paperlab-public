"""Tests for mark scheme loading.

Tests:
1. Valid marks JSON loads correctly - creates criteria, content blocks
2. Loading without paper loaded first fails
3. Marks and paper total consistency verification
"""

import pytest

from paperlab.data.repositories.marking import (
    criteria_content,
    mark_criteria,
)
from paperlab.loading.marks_loader import (
    load_mark_scheme,
    verify_marks_loaded,
    verify_paper_marks_consistency,
)
from tests.loading.conftest import TEST_MARKS_JSON


class TestMarksLoadSuccess:
    """Test successful mark scheme loading scenarios."""

    def test_valid_marks_json_loads_correctly(self, test_conn, loaded_paper_with_marks):
        """Test that valid marks JSON creates all expected database records."""
        # Arrange
        paper_id = loaded_paper_with_marks

        # Act
        result_paper_id = load_mark_scheme(str(TEST_MARKS_JSON), test_conn)
        test_conn.commit()

        # Assert
        assert result_paper_id == paper_id

        # Assert - Mark criteria created
        criteria_count = mark_criteria.count_criteria(paper_id, test_conn)
        assert criteria_count > 0  # At least some criteria created

    def test_marks_creates_criteria_content_blocks(self, test_conn, loaded_paper_with_marks):
        """Test that mark scheme loading creates criteria content blocks."""
        # Arrange
        paper_id = loaded_paper_with_marks

        # Act
        load_mark_scheme(str(TEST_MARKS_JSON), test_conn)
        test_conn.commit()

        # Assert - Content blocks created for criteria
        blocks_count = criteria_content.count_content_blocks_for_paper(paper_id, test_conn)
        assert blocks_count > 0  # At least some content blocks created


class TestMarksLoadValidation:
    """Test mark scheme loading validation failures."""

    def test_loading_without_paper_raises_value_error(self, test_conn, seed_mark_types):
        """Test that loading marks without paper first raises ValueError."""
        # seed_mark_types is used but loaded_paper is NOT used
        # So exam_type and mark_types exist, but paper doesn't

        with pytest.raises(ValueError, match="not found"):
            load_mark_scheme(str(TEST_MARKS_JSON), test_conn)

    def test_nonexistent_file_raises_file_not_found(self, test_conn, loaded_paper_with_marks):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="JSON file not found"):
            load_mark_scheme("/nonexistent/path/marks.json", test_conn)


class TestMarksVerification:
    """Test mark scheme verification logic."""

    def test_verify_marks_loaded_success(self, test_conn, loaded_paper_with_marks):
        """Test that verification passes for correctly loaded marks."""
        # Arrange
        paper_id = loaded_paper_with_marks
        load_mark_scheme(str(TEST_MARKS_JSON), test_conn)
        test_conn.commit()

        # Get actual counts
        criteria_count = mark_criteria.count_criteria(paper_id, test_conn)
        blocks_count = criteria_content.count_content_blocks_for_paper(paper_id, test_conn)

        # Act & Assert - Should not raise
        verify_marks_loaded(
            paper_id,
            expected_criteria=criteria_count,
            expected_blocks=blocks_count,
            conn=test_conn,
        )

    def test_verify_paper_marks_consistency_success(self, test_conn, loaded_paper_with_marks):
        """Test that paper/marks consistency check passes."""
        # Arrange
        paper_id = loaded_paper_with_marks
        load_mark_scheme(str(TEST_MARKS_JSON), test_conn)
        test_conn.commit()

        # Act & Assert - Should not raise
        verify_paper_marks_consistency(paper_id, test_conn)

    def test_verify_marks_loaded_fails_on_count_mismatch(self, test_conn, loaded_paper_with_marks):
        """Test that verification fails when counts don't match."""
        # Arrange
        paper_id = loaded_paper_with_marks
        load_mark_scheme(str(TEST_MARKS_JSON), test_conn)
        test_conn.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="Mark criteria count mismatch"):
            verify_marks_loaded(
                paper_id,
                expected_criteria=999,  # Wrong count
                expected_blocks=0,
                conn=test_conn,
            )
