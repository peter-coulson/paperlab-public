"""Tests for question_marking_results repository.

Long-term tests only - validates security boundaries.
"""

import sqlite3

from paperlab.constants.fields import CriterionFields
from paperlab.data.repositories.marking import (
    mark_criteria,
    marking_attempts,
    question_marking_results,
    question_submissions,
)

from .conftest import (
    MARK_TYPE_M,
    seed_exam_type,
    seed_mark_types,
    seed_paper,
    seed_question,
    seed_question_part,
)

# =============================================================================
# Test Constants
# =============================================================================

TEST_SUPABASE_UID = "550e8400-e29b-41d4-a716-446655440000"
TEST_SUBMISSION_UUID = "test-submission-uuid-123"
TEST_MODEL_IDENTIFIER = "claude-sonnet-4-5-20250929"
TEST_DISPLAY_NAME = "Claude 3.5 Sonnet v2"
TEST_PROVIDER = "anthropic"
TEST_FEEDBACK = "Correct application of power rule"
TEST_OBSERVATION = "Student showed clear working. Method is sound."


# =============================================================================
# Helper Functions
# =============================================================================


def seed_student(conn: sqlite3.Connection) -> int:
    """Create test student and return ID."""
    cursor = conn.execute(
        "INSERT INTO students (supabase_uid) VALUES (?)",
        (TEST_SUPABASE_UID,),
    )
    student_id = cursor.lastrowid
    assert student_id is not None
    return student_id


def seed_llm_model(conn: sqlite3.Connection) -> int:
    """Create test LLM model and return ID."""
    cursor = conn.execute(
        """
        INSERT INTO llm_models (model_identifier, display_name, provider)
        VALUES (?, ?, ?)
        """,
        (TEST_MODEL_IDENTIFIER, TEST_DISPLAY_NAME, TEST_PROVIDER),
    )
    model_id = cursor.lastrowid
    assert model_id is not None
    return model_id


def seed_submission(
    conn: sqlite3.Connection,
    student_id: int,
    question_id: int,
) -> int:
    """Create test submission and return ID."""
    return question_submissions.create(
        student_id=student_id,
        question_id=question_id,
        submission_uuid=TEST_SUBMISSION_UUID,
        conn=conn,
    )


def seed_marking_attempt(
    conn: sqlite3.Connection,
    submission_id: int,
    llm_model_id: int,
    status: str = "success",
) -> int:
    """Create test marking attempt and return ID."""
    return marking_attempts.create(
        submission_id=submission_id,
        llm_model_id=llm_model_id,
        system_prompt="Test system prompt",
        user_prompt="Test user prompt",
        status=status,
        processing_time_ms=1000,
        input_tokens=100,
        output_tokens=50,
        raw_response='{"results": []}',
        response_received='{"results": []}' if status == "success" else None,
        error_message=None if status == "success" else "Test error",
        conn=conn,
    )


# =============================================================================
# Long-term Tests (Security Boundary)
# =============================================================================


class TestGetResultsForSubmission:
    """Tests for API-facing query - security boundary."""

    def test_get_results_excludes_observation(self, test_conn: sqlite3.Connection) -> None:
        """API-facing query does NOT return observation field.

        This is a critical security boundary test. The observation field
        contains internal LLM reasoning and must never be exposed to users
        through the API.
        """
        # Setup
        exam_type_id = seed_exam_type(test_conn)
        mark_type_ids = seed_mark_types(test_conn, exam_type_id)
        paper_id = seed_paper(test_conn, exam_type_id)
        question_id = seed_question(test_conn, paper_id, 1, 3)
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
        student_id = seed_student(test_conn)
        llm_model_id = seed_llm_model(test_conn)
        submission_id = seed_submission(test_conn, student_id, question_id)
        marking_attempt_id = seed_marking_attempt(test_conn, submission_id, llm_model_id)

        # Create result with observation
        question_marking_results.create_result(
            marking_attempt_id=marking_attempt_id,
            mark_criteria_id=criterion_id,
            marks_awarded=1,
            feedback=TEST_FEEDBACK,
            observation=TEST_OBSERVATION,
            confidence_score=0.95,
            conn=test_conn,
        )

        # Get results for submission (API-facing)
        results = question_marking_results.get_results_for_submission(submission_id, test_conn)

        # Verify observation is NOT in response
        assert len(results) == 1
        assert "observation" not in results[0]
        assert CriterionFields.FEEDBACK in results[0]
        assert results[0][CriterionFields.FEEDBACK] == TEST_FEEDBACK
