"""Question attempts repository.

Manages question_attempts table, which links paper attempts to question submissions.

Design:
- Each question_attempt links one submission to one paper attempt
- Supports multiple attempts per question (re-submissions before paper submission)
- "Latest" determined by submission timestamp (ORDER BY submitted_at DESC)
- Inheritance tracked via inherited_from_attempt
- Cross-context validation prevents submission appearing in both practice AND paper

Usage:
    # CLI layer opens connection and manages transaction
    from paperlab.data.repositories.marking import question_attempts
    from paperlab.data.database import connection

    with connection() as conn:
        qa_id = question_attempts.create_attempt(
            paper_attempt_id=1,
            submission_id=42,
            inherited_from=None,
            conn=conn
        )
        conn.commit()  # CLI layer commits
"""

from sqlite3 import Connection

from paperlab.config.constants import Tables
from paperlab.data.models.marking import QuestionAttempt


def create_attempt(
    paper_attempt_id: int,
    submission_id: int,
    inherited_from: int | None,
    conn: Connection,
) -> int:
    """Create question attempt linking paper attempt to submission.

    CRITICAL: Must validate submission not already linked to practice_question_attempts
    to prevent cross-context contamination (same submission in practice AND paper).

    Args:
        paper_attempt_id: Paper attempt this belongs to
        submission_id: Submission to link (from question_submissions)
        inherited_from: Optional source attempt ID (for inherited questions)
        conn: Database connection

    Returns:
        Question attempt ID

    Raises:
        ValueError: If submission already linked to any context (cross-context)
        sqlite3.IntegrityError: If database constraint violated
    """
    # CRITICAL: Validate submission not in any context (practice OR paper)
    # Prevents cross-context contamination via centralized validation module
    from paperlab.data.repositories.marking import submission_contexts

    submission_contexts.validate_submission_unlinked(submission_id, conn)

    # Insert question_attempt record
    cursor = conn.execute(
        f"""
        INSERT INTO {Tables.QUESTION_ATTEMPTS}
        (paper_attempt_id, submission_id, inherited_from_attempt)
        VALUES (?, ?, ?)
    """,
        (paper_attempt_id, submission_id, inherited_from),
    )

    qa_id = cursor.lastrowid
    if qa_id is None:
        raise ValueError("Failed to get question_attempt_id after INSERT")

    return int(qa_id)


def get_all_latest_attempts(
    paper_attempt_id: int,
    conn: Connection,
) -> list[QuestionAttempt]:
    """Get latest attempt for EACH question in paper attempt.

    Returns one question_attempt per question, choosing the one with the
    most recent submission timestamp. Used for:
    - Validation: Check all N questions have latest submissions
    - Marking: Determine which submissions need marking
    - Grading: Calculate marks from latest submissions only

    CRITICAL: This function ignores all non-latest attempts (inherited or overridden).

    Args:
        paper_attempt_id: Paper attempt ID
        conn: Database connection

    Returns:
        List of QuestionAttempt records (one per question, empty list if none)
    """
    cursor = conn.execute(
        f"""
        WITH latest_submissions AS (
            SELECT
                qs.question_id,
                qa.id as qa_id,
                qa.paper_attempt_id,
                qa.submission_id,
                qa.inherited_from_attempt,
                qa.created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY qs.question_id
                    ORDER BY qs.submitted_at DESC
                ) as rn
            FROM {Tables.QUESTION_ATTEMPTS} qa
            JOIN {Tables.QUESTION_SUBMISSIONS} qs ON qa.submission_id = qs.id
            WHERE qa.paper_attempt_id = ?
        )
        SELECT qa_id, paper_attempt_id, submission_id,
               inherited_from_attempt, created_at
        FROM latest_submissions
        WHERE rn = 1
        ORDER BY question_id
    """,
        (paper_attempt_id,),
    )

    rows = cursor.fetchall()
    return [
        QuestionAttempt(
            id=row[0],
            paper_attempt_id=row[1],
            submission_id=row[2],
            inherited_from_attempt=row[3],
            created_at=row[4],
        )
        for row in rows
    ]


def get_submitted_questions_with_image_counts(
    paper_attempt_id: int,
    conn: Connection,
) -> dict[int, int]:
    """Get map of submitted questions to their image counts.

    Returns a dictionary mapping question numbers to the count of images
    submitted for each question. Used when resuming draft papers.

    Args:
        paper_attempt_id: Paper attempt ID
        conn: Database connection

    Returns:
        Dict mapping question_number → image_count
        Empty dict if no questions submitted yet
    """
    cursor = conn.execute(
        f"""
        WITH latest_submissions AS (
            SELECT
                q.question_number,
                qa.submission_id,
                ROW_NUMBER() OVER (
                    PARTITION BY qs.question_id
                    ORDER BY qs.submitted_at DESC
                ) as rn
            FROM {Tables.QUESTION_ATTEMPTS} qa
            JOIN {Tables.QUESTION_SUBMISSIONS} qs ON qa.submission_id = qs.id
            JOIN {Tables.QUESTIONS} q ON qs.question_id = q.id
            WHERE qa.paper_attempt_id = ?
        )
        SELECT
            ls.question_number,
            COUNT(si.id) as image_count
        FROM latest_submissions ls
        JOIN {Tables.SUBMISSION_IMAGES} si ON ls.submission_id = si.submission_id
        WHERE ls.rn = 1
        GROUP BY ls.question_number
        ORDER BY ls.question_number
    """,
        (paper_attempt_id,),
    )

    rows = cursor.fetchall()
    return {int(row[0]): int(row[1]) for row in rows}


def inherit_latest_attempts(
    new_attempt_id: int,
    previous_attempt_id: int,
    conn: Connection,
) -> int:
    """Inherit latest question attempt per question from previous attempt.

    Copies only the most recent submission for each question based on
    submission timestamp. Intermediate replacements (Edge Case 4) remain
    in source attempt for audit trail but are not carried forward.

    Example:
        Source Attempt #1:
          - Q7 uploaded at 10:00 (submission_1)
          - Q7 replaced at 10:05 (submission_2) <- latest

        New Attempt #2:
          - Only submission_2 is inherited for Q7
          - submission_1 stays in Attempt #1 (audit trail)

    Data Cost Rationale:
        - At scale: 30-50% fewer rows vs copying all attempts
        - Query performance: Less data to scan in ROW_NUMBER() queries
        - Audit trail: Replacements preserved in source attempt
        - Semantic clarity: "Retry" = snapshot of final state

    Student can override any inherited questions by creating new submissions,
    which will have later timestamps and become the "latest" automatically.

    Args:
        new_attempt_id: Target attempt to copy into
        previous_attempt_id: Source attempt to copy from
        conn: Database connection

    Returns:
        Number of question attempts copied (one per question)

    Raises:
        ValueError: If source attempt incomplete, wrong paper, or target has
                   existing inherited attempts
    """
    # 1. Validate source exists and is complete
    from paperlab.data.repositories.marking import paper_attempts

    source = paper_attempts.get_attempt(previous_attempt_id, conn)
    if source.completed_at is None:
        raise ValueError(f"Cannot inherit from incomplete attempt {previous_attempt_id}")

    # 2. Validate same paper
    target = paper_attempts.get_attempt(new_attempt_id, conn)
    if source.paper_id != target.paper_id:
        raise ValueError(
            f"Cannot inherit from different paper "
            f"(source: {source.paper_id}, target: {target.paper_id})"
        )

    # CRITICAL SECURITY: Validate same student (prevent stealing answers)
    if source.student_id != target.student_id:
        raise ValueError(
            f"Cannot inherit from another student's attempt\n"
            f"Source attempt belongs to student {source.student_id}, "
            f"target belongs to student {target.student_id}"
        )

    # 3. Validate target has no inherited attempts yet (prevent duplicate inheritance)
    cursor = conn.execute(
        f"""
        SELECT COUNT(*) FROM {Tables.QUESTION_ATTEMPTS}
        WHERE paper_attempt_id = ? AND inherited_from_attempt IS NOT NULL
    """,
        (new_attempt_id,),
    )
    existing = cursor.fetchone()
    existing_count = int(existing[0]) if existing else 0

    if existing_count > 0:
        raise ValueError(
            f"Attempt {new_attempt_id} already has {existing_count} inherited questions"
        )

    # 4. Inherit latest submission per question from source attempt
    # Only copies most recent submission per question (not intermediate replacements)
    cursor = conn.execute(
        f"""
        WITH latest_submissions AS (
            SELECT
                qa.submission_id,
                qs.question_id,
                ROW_NUMBER() OVER (
                    PARTITION BY qs.question_id
                    ORDER BY qs.submitted_at DESC
                ) as rn
            FROM {Tables.QUESTION_ATTEMPTS} qa
            JOIN {Tables.QUESTION_SUBMISSIONS} qs ON qa.submission_id = qs.id
            WHERE qa.paper_attempt_id = ?
        )
        INSERT INTO {Tables.QUESTION_ATTEMPTS}
        (paper_attempt_id, submission_id, inherited_from_attempt)
        SELECT ?, submission_id, ?
        FROM latest_submissions
        WHERE rn = 1
    """,
        (previous_attempt_id, new_attempt_id, previous_attempt_id),
    )

    return cursor.rowcount


def count_non_inherited_attempts(
    paper_attempt_id: int,
    conn: Connection,
) -> int:
    """Count question attempts that are not inherited.

    Returns the number of question attempts for this paper attempt where
    inherited_from_attempt IS NULL, indicating new submissions (not carried
    over from a previous attempt).

    Used by validation to prevent zero-effort retry submissions.

    Args:
        paper_attempt_id: Paper attempt ID
        conn: Database connection

    Returns:
        Count of non-inherited attempts (0 if all inherited or none exist)
    """
    cursor = conn.execute(
        f"""
        SELECT COUNT(*) FROM {Tables.QUESTION_ATTEMPTS}
        WHERE paper_attempt_id = ? AND inherited_from_attempt IS NULL
    """,
        (paper_attempt_id,),
    )

    result = cursor.fetchone()
    return result[0] if result else 0


def get_attempt(
    question_attempt_id: int,
    conn: Connection,
) -> QuestionAttempt:
    """Get single question attempt by ID.

    Args:
        question_attempt_id: Question attempt ID
        conn: Database connection

    Returns:
        QuestionAttempt record

    Raises:
        ValueError: If question attempt not found
    """
    cursor = conn.execute(
        f"""
        SELECT id, paper_attempt_id, submission_id, inherited_from_attempt, created_at
        FROM {Tables.QUESTION_ATTEMPTS}
        WHERE id = ?
        """,
        (question_attempt_id,),
    )

    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"Question attempt {question_attempt_id} not found")

    return QuestionAttempt(
        id=row[0],
        paper_attempt_id=row[1],
        submission_id=row[2],
        inherited_from_attempt=row[3],
        created_at=row[4],
    )
