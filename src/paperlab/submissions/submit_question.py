"""Submission orchestrator for Flow 2 API.

Handles atomic commits for:
- Paper question submission (staging → permanent + DB records)
- Practice question submission (staging → permanent + DB records + marking)

Per CLAUDE.md: API is transport, business logic lives here.
"""

import uuid
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Connection

from botocore.exceptions import ClientError

from paperlab.data.repositories import practice as practice_repo
from paperlab.data.repositories.marking import (
    papers,
    question_attempts,
    question_submissions,
    questions,
    submission_images,
)
from paperlab.marking.marker import QuestionMarker
from paperlab.services.llm_client import LLMClient
from paperlab.storage.storage import R2Storage


class StagingKeyValidationError(ValueError):
    """Raised when staging key validation fails."""

    pass


def validate_staging_keys(staging_keys: list[str], attempt_uuid: str) -> None:
    """Validate that all staging keys belong to the given attempt.

    Args:
        staging_keys: List of staging bucket keys
        attempt_uuid: Expected attempt UUID in key path

    Raises:
        StagingKeyValidationError: If any key doesn't match expected pattern
    """
    expected_prefix = f"staging/{attempt_uuid}/"
    for staging_key in staging_keys:
        if not staging_key.startswith(expected_prefix):
            raise StagingKeyValidationError(
                f"Staging key '{staging_key}' does not belong to attempt {attempt_uuid}"
            )


@dataclass
class PaperQuestionResult:
    """Result of submitting a question to a paper attempt."""

    question_attempt_id: int
    submission_id: int
    question_number: int


@dataclass
class PracticeQuestionResult:
    """Result of submitting a practice question."""

    practice_attempt_id: int
    submission_id: int
    question_display: str
    marking_status: str  # "success" or error status
    created_at: datetime


def submit_paper_question(
    paper_attempt_id: int,
    paper_id: int,
    student_id: int,
    question_number: int,
    staging_keys: list[str],
    r2: R2Storage,
    conn: Connection,
) -> PaperQuestionResult:
    """Atomic commit: staging → permanent + DB records for paper question.

    Does NOT commit - caller manages transaction.

    Args:
        paper_attempt_id: Paper attempt this question belongs to
        paper_id: Paper ID (for question lookup)
        student_id: Student submitting
        question_number: Question number within paper
        staging_keys: Staging bucket keys to copy
        r2: R2 storage client
        conn: Database connection

    Returns:
        PaperQuestionResult with IDs

    Raises:
        ValueError: If question not found
        ClientError: If R2 operations fail
    """
    # 1. Look up question_id
    question_id = questions.get_question_id(paper_id, question_number, conn)

    # 2. Generate permanent keys and copy from staging
    submission_uuid = str(uuid.uuid4())
    permanent_keys = []

    for idx, staging_key in enumerate(staging_keys, start=1):
        ext = staging_key.rsplit(".", 1)[-1] if "." in staging_key else "jpg"
        permanent_key = f"submissions/{submission_uuid}_page{idx:02d}.{ext}"
        permanent_keys.append(permanent_key)
        r2.copy_to_permanent(staging_key, permanent_key)

    # 3. Create submission record
    submission_id = question_submissions.create(
        student_id=student_id,
        question_id=question_id,
        submission_uuid=submission_uuid,
        conn=conn,
    )

    # 4. Create image records
    for idx, permanent_key in enumerate(permanent_keys, start=1):
        submission_images.create(
            submission_id=submission_id,
            image_path=permanent_key,
            image_sequence=idx,
            conn=conn,
        )

    # 5. Link to paper attempt
    question_attempt_id = question_attempts.create_attempt(
        paper_attempt_id=paper_attempt_id,
        submission_id=submission_id,
        inherited_from=None,
        conn=conn,
    )

    # 6. Best-effort cleanup of staging
    with suppress(ClientError, OSError):
        r2.delete_staging_images(staging_keys)

    return PaperQuestionResult(
        question_attempt_id=question_attempt_id,
        submission_id=submission_id,
        question_number=question_number,
    )


def submit_practice_question(
    attempt_uuid: str,
    student_id: int,
    question_id: int,
    staging_keys: list[str],
    r2: R2Storage,
    llm_client: LLMClient,
    llm_model_id: int,
    conn: Connection,
) -> PracticeQuestionResult:
    """Single-phase: staging → permanent + DB records + immediate marking.

    Does NOT commit - caller manages transaction.

    Args:
        attempt_uuid: Client-generated UUID for practice attempt
        student_id: Student submitting
        question_id: Question being practiced
        staging_keys: Staging bucket keys to copy
        r2: R2 storage client
        llm_client: LLM client for marking
        llm_model_id: Model to use for marking
        conn: Database connection

    Returns:
        PracticeQuestionResult with IDs and marking status

    Raises:
        ValueError: If question not found
        ClientError: If R2 operations fail
    """
    # 1. Validate question exists and get display info
    question_structure = questions.get_question_structure(question_id, conn)
    paper_id = questions.get_paper_id_for_question(question_id, conn)
    paper_info = papers.get_paper_full(paper_id, conn)
    question_display = f"Q{question_structure['question_number']} - {paper_info['display_name']}"

    # 2. Generate permanent keys and copy from staging
    submission_uuid = str(uuid.uuid4())
    permanent_keys = []

    for idx, staging_key in enumerate(staging_keys, start=1):
        ext = staging_key.rsplit(".", 1)[-1] if "." in staging_key else "jpg"
        permanent_key = f"submissions/{submission_uuid}_page{idx:02d}.{ext}"
        permanent_keys.append(permanent_key)
        r2.copy_to_permanent(staging_key, permanent_key)

    # 3. Create submission record
    submission_id = question_submissions.create(
        student_id=student_id,
        question_id=question_id,
        submission_uuid=submission_uuid,
        conn=conn,
    )

    # 4. Create image records
    for idx, permanent_key in enumerate(permanent_keys, start=1):
        submission_images.create(
            submission_id=submission_id,
            image_path=permanent_key,
            image_sequence=idx,
            conn=conn,
        )

    # 5. Create practice attempt
    practice_attempt_id = practice_repo.create_practice_attempt(
        attempt_uuid=attempt_uuid,
        student_id=student_id,
        submission_id=submission_id,
        conn=conn,
    )

    # 6. Mark immediately (practice = instant feedback)
    marking_status = "success"
    try:
        marker = QuestionMarker(llm_client)
        marker.mark_submission(submission_id, llm_model_id, conn)
    except Exception:
        marking_status = "marking_failed"

    # 7. Best-effort cleanup of staging
    with suppress(ClientError, OSError):
        r2.delete_staging_images(staging_keys)

    return PracticeQuestionResult(
        practice_attempt_id=practice_attempt_id,
        submission_id=submission_id,
        question_display=question_display,
        marking_status=marking_status,
        created_at=datetime.now(),
    )
