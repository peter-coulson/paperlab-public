"""Repository for question_marking_results table.

Provides data access methods for individual criterion marking results.
Each record represents one criterion's marking outcome from an LLM response.
"""

import sqlite3
from typing import Any

from paperlab.config import ErrorMessages
from paperlab.constants.fields import CriterionFields


def create_result(
    marking_attempt_id: int,
    mark_criteria_id: int,
    marks_awarded: int,
    feedback: str,
    confidence_score: float,
    conn: sqlite3.Connection,
    observation: str | None = None,
) -> int:
    """Create single criterion marking result.

    Does NOT commit - caller manages transaction.

    Args:
        marking_attempt_id: Database ID of parent marking attempt
        mark_criteria_id: Database ID of mark criterion
        marks_awarded: Marks awarded for this criterion
        feedback: Specific feedback for this criterion
        confidence_score: LLM confidence (0.0-1.0)
        conn: Database connection
        observation: Internal LLM reasoning (not shown to students)

    Returns:
        result_id

    Raises:
        sqlite3.IntegrityError: If foreign keys invalid or constraints violated
        ValueError: If failed to get result_id after INSERT

    Example:
        >>> result_id = create_result(
        ...     marking_attempt_id=1,
        ...     mark_criteria_id=1,
        ...     marks_awarded=1,
        ...     feedback="Correct application of power rule",
        ...     confidence_score=0.95,
        ...     conn=conn
        ... )
    """
    cursor = conn.execute(
        """
        INSERT INTO question_marking_results (
            marking_attempt_id,
            mark_criteria_id,
            marks_awarded,
            observation,
            feedback,
            confidence_score
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            marking_attempt_id,
            mark_criteria_id,
            marks_awarded,
            observation,
            feedback,
            confidence_score,
        ),
    )

    result_id = cursor.lastrowid
    if result_id is None:
        raise ValueError(ErrorMessages.INSERT_FAILED.format(entity="question_marking_result"))
    return result_id


def create_results_batch(
    marking_attempt_id: int,
    results: list[dict[str, Any]],
    conn: sqlite3.Connection,
) -> int:
    """Create multiple criterion results in batch using single SQL operation.

    Uses executemany() for efficient batch insertion.
    Accepts list of dictionaries with primitive values (no domain model dependency).

    Does NOT commit - caller manages transaction.

    Args:
        marking_attempt_id: Database ID of parent marking attempt
        results: List of criterion result dictionaries with keys:
            - criterion_id: int (database ID of mark criterion)
            - observation: str (optional, internal LLM reasoning)
            - marks_awarded: int
            - feedback: str
            - confidence_score: float
        conn: Database connection

    Returns:
        Number of rows inserted (should equal len(results))

    Raises:
        sqlite3.IntegrityError: If foreign keys invalid or constraints violated
        ValueError: If required keys missing

    Example:
        >>> from paperlab.constants.fields import CriterionFields
        >>> results = [
        ...     {
        ...         CriterionFields.CRITERION_ID: 1,
        ...         CriterionFields.MARKS_AWARDED: 1,
        ...         CriterionFields.FEEDBACK: "Correct",
        ...         CriterionFields.CONFIDENCE_SCORE: 0.95
        ...     }
        ... ]
        >>> count = create_results_batch(
        ...     marking_attempt_id=1,
        ...     results=results,
        ...     conn=conn
        ... )
    """
    if not results:
        return 0

    # Prepare data tuples for executemany
    data = [
        (
            marking_attempt_id,
            result[CriterionFields.CRITERION_ID],
            result[CriterionFields.MARKS_AWARDED],
            result.get(CriterionFields.OBSERVATION),
            result[CriterionFields.FEEDBACK],
            result[CriterionFields.CONFIDENCE_SCORE],
        )
        for result in results
    ]

    # Single batch INSERT
    cursor = conn.executemany(
        """
        INSERT INTO question_marking_results (
            marking_attempt_id,
            mark_criteria_id,
            marks_awarded,
            observation,
            feedback,
            confidence_score
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        data,
    )

    return cursor.rowcount


def count_results_for_attempt(
    marking_attempt_id: int,
    conn: sqlite3.Connection,
) -> int:
    """Count results for verification.

    Args:
        marking_attempt_id: Marking attempt to count results for
        conn: Database connection

    Returns:
        Number of results for this marking attempt
    """
    cursor = conn.execute(
        "SELECT COUNT(*) FROM question_marking_results WHERE marking_attempt_id = ?",
        (marking_attempt_id,),
    )
    result = cursor.fetchone()
    return int(result[0]) if result else 0


def get_results_for_marking_attempt(
    marking_attempt_id: int, conn: sqlite3.Connection
) -> list[dict[str, int | str | float | None]]:
    """Get all criterion results for a marking attempt.

    Args:
        marking_attempt_id: Database ID of marking attempt
        conn: Database connection

    Returns:
        List of dictionaries with result fields

    Example:
        >>> results = get_results_for_marking_attempt(marking_attempt_id=1, conn)
        >>> for r in results:
        ...     print(f"Criterion {r['mark_criteria_id']}: {r['marks_awarded']} marks")
    """
    cursor = conn.execute(
        """
        SELECT
            id,
            marking_attempt_id,
            mark_criteria_id,
            marks_awarded,
            observation,
            feedback,
            confidence_score
        FROM question_marking_results
        WHERE marking_attempt_id = ?
        ORDER BY mark_criteria_id
        """,
        (marking_attempt_id,),
    )

    results = []
    for row in cursor:
        results.append(
            {
                "result_id": row[0],
                "marking_attempt_id": row[1],
                "mark_criteria_id": row[2],
                CriterionFields.MARKS_AWARDED: row[3],
                CriterionFields.OBSERVATION: row[4],
                CriterionFields.FEEDBACK: row[5],
                CriterionFields.CONFIDENCE_SCORE: row[6],
            }
        )

    return results


def get_results_for_submission(
    submission_id: int, conn: sqlite3.Connection
) -> list[dict[str, Any]]:
    """Get all marking results for a submission's successful marking attempt.

    Used by grading pipeline to sum marks awarded per question.

    Args:
        submission_id: Submission to get results for
        conn: Database connection

    Returns:
        List of dicts with keys:
        - mark_criteria_id: int
        - marks_awarded: int
        - feedback: str
        - confidence_score: float

    Raises:
        ValueError: If no successful marking attempt found for submission
    """
    # First get successful marking attempt
    cursor = conn.execute(
        """
        SELECT id
        FROM marking_attempts
        WHERE submission_id = ? AND status = 'success'
        ORDER BY attempted_at DESC
        LIMIT 1
        """,
        (submission_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"No successful marking attempt found for submission {submission_id}")

    marking_attempt_id = row[0]

    # Get all results for this attempt
    cursor = conn.execute(
        """
        SELECT
            mark_criteria_id,
            marks_awarded,
            feedback,
            confidence_score
        FROM question_marking_results
        WHERE marking_attempt_id = ?
        ORDER BY mark_criteria_id
        """,
        (marking_attempt_id,),
    )

    results = []
    for row in cursor:
        results.append(
            {
                "mark_criteria_id": row[0],
                "marks_awarded": row[1],
                "feedback": row[2],
                "confidence_score": row[3],
            }
        )

    return results


def get_scores_for_paper_attempt(
    paper_attempt_id: int, conn: sqlite3.Connection
) -> list[dict[str, int]]:
    """Aggregate marks by question for a completed paper attempt.

    Joins through question_attempts → question_submissions → marking_attempts
    → question_marking_results to sum marks per question.

    Only includes results from successful marking attempts and latest
    question attempts (in case of re-submissions).

    Args:
        paper_attempt_id: Paper attempt to get scores for
        conn: Database connection

    Returns:
        List of dicts with keys:
        - question_number: int
        - question_attempt_id: int
        - awarded: int (sum of marks awarded)
        - available: int (sum of marks available)

    Note:
        Returns empty list if no marking results found.
        Caller should verify paper attempt is complete before calling.
    """
    cursor = conn.execute(
        """
        WITH latest_attempts AS (
            -- Get the latest question attempt per question for this paper attempt
            SELECT
                qa.id AS question_attempt_id,
                qa.submission_id,
                qs.question_id,
                ROW_NUMBER() OVER (
                    PARTITION BY qs.question_id
                    ORDER BY qs.submitted_at DESC
                ) AS rn
            FROM question_attempts qa
            JOIN question_submissions qs ON qa.submission_id = qs.id
            WHERE qa.paper_attempt_id = ?
        )
        SELECT
            q.question_number,
            la.question_attempt_id,
            COALESCE(SUM(qmr.marks_awarded), 0) AS awarded,
            COALESCE(SUM(mc.marks_available), 0) AS available
        FROM latest_attempts la
        JOIN questions q ON la.question_id = q.id
        JOIN marking_attempts ma ON la.submission_id = ma.submission_id
            AND ma.status = 'success'
        LEFT JOIN question_marking_results qmr ON ma.id = qmr.marking_attempt_id
        LEFT JOIN mark_criteria mc ON qmr.mark_criteria_id = mc.id
        WHERE la.rn = 1
        GROUP BY q.question_number, la.question_attempt_id
        ORDER BY q.question_number
        """,
        (paper_attempt_id,),
    )

    return [
        {
            "question_number": int(row[0]),
            "question_attempt_id": int(row[1]),
            "awarded": int(row[2]),
            "available": int(row[3]),
        }
        for row in cursor.fetchall()
    ]
