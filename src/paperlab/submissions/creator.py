"""Submission creation orchestrator.

Handles the complete submission pipeline: validation, image storage,
and database record creation.

Database Context Handling:
- Production (marking.db): Enforces R2 paths only, rejects local paths
- Evaluation (test_execution.db): Accepts both R2 and local paths
- Unknown databases: Fails with explicit error (safety check)

This dual-path architecture enables:
- Production submissions use cloud storage (R2)
- Evaluation tests use version-controlled local fixtures
- Clear separation prevents accidental data leakage

Design principles:
- Orchestration only - delegates to repositories
- Connection provided by caller (dependency injection)
- Clear data flow: request → validate → store images → store submission → result
- Atomic transaction (commit handled by caller)
"""

import sqlite3
from pathlib import Path

from paperlab.config import ErrorMessages, ImageSequence
from paperlab.data.repositories.marking import (
    question_submissions,
    questions,
    students,
    submission_images,
)
from paperlab.loaders.path_utils import is_r2_path, to_logical_path
from paperlab.submissions.exceptions import InvalidImageError
from paperlab.submissions.models import SubmissionRequest


def _is_production_database(conn: sqlite3.Connection) -> bool:
    """Detect if connected to production database.

    Returns:
        True if marking.db (production), False if test_execution.db (eval)

    Raises:
        ValueError: If connected to neither database (safety check)
    """
    cursor = conn.execute("PRAGMA database_list")
    db_info = cursor.fetchone()
    db_path = db_info[2] if db_info else ""

    if "marking.db" in db_path:
        return True
    elif "test_execution.db" in db_path:
        return False
    else:
        raise ValueError(
            f"Cannot determine database context from path: {db_path}\n"
            f"Expected 'marking.db' (production) or 'test_execution.db' (evaluation)."
        )


class SubmissionCreator:
    """Orchestrates creation of question submissions.

    Responsibilities:
    - Validate submission request
    - Store images in database
    - Create submission record
    - Verify successful storage
    """

    def create_submission(self, request: SubmissionRequest, conn: sqlite3.Connection) -> int:
        """Create a submission record with images.

        This is PHASE A of the upload workflow: create submission atomically.
        Marking (PHASE B) is separate and happens later (immediate, deferred, or batch).

        Args:
            request: Submission request with student, question, and images
            conn: Database connection (transaction managed by caller)

        Returns:
            submission_id: Database ID of created submission

        Raises:
            ValueError: If validation fails
            InvalidImageError: If images are invalid
            RuntimeError: If storage verification fails
        """
        # Validation: Student exists
        if not students.exists(request.student_id, conn):
            raise ValueError(ErrorMessages.STUDENT_NOT_FOUND.format(student_id=request.student_id))

        # Validation: Question exists
        try:
            questions.get_question_structure(request.question_id, conn)
        except ValueError as e:
            raise ValueError(
                ErrorMessages.QUESTION_NOT_FOUND.format(question_id=request.question_id)
            ) from e

        # Validation: At least one image (already checked in SubmissionRequest.__post_init__)
        if not request.image_paths:
            raise ValueError("At least one image is required for submission")

        # Validation: All images exist and accessible
        self._validate_images(request.image_paths)

        # Validation: Production database requires R2 paths only
        if _is_production_database(conn):
            for img_path in request.image_paths:
                path_str = str(img_path)
                if not is_r2_path(path_str):
                    raise ValueError(
                        f"Production database requires R2 paths only.\n"
                        f"Got local path: {img_path}\n"
                        f"Convert to R2 path or use test_execution.db for local testing."
                    )

        # Create submission record FIRST (submission-first workflow)
        # UUID provided by caller (validated in SubmissionRequest.__post_init__)
        submission_id = question_submissions.create(
            student_id=request.student_id,
            question_id=request.question_id,
            submission_uuid=request.submission_uuid,
            conn=conn,
        )

        # Store images linked to submission
        for idx, image_path in enumerate(request.image_paths, start=ImageSequence.START):
            # Convert to logical path for database storage
            # R2 paths are already logical (not filesystem paths), store as-is
            path_str = str(image_path)
            logical_path = path_str if is_r2_path(path_str) else to_logical_path(Path(image_path))

            submission_images.create(
                submission_id=submission_id,
                image_path=logical_path,
                image_sequence=idx,
                conn=conn,
            )

        # Verify storage
        self._verify_storage(submission_id, len(request.image_paths), conn)

        return submission_id

    def _validate_images(self, image_paths: list[Path]) -> None:
        """Validate all images exist and are accessible.

        For local paths: Checks file existence and type
        For R2 paths: Skips validation (remote storage)

        Args:
            image_paths: Paths to validate

        Raises:
            InvalidImageError: If any image is invalid
        """
        for idx, image_path in enumerate(image_paths, start=1):
            path_str = str(image_path)

            # Skip existence check for R2 paths (remote storage)
            if is_r2_path(path_str):
                continue

            # Validate local paths only
            if not image_path.exists():
                total = len(image_paths)
                raise InvalidImageError(f"Image {idx}/{total} not found: {image_path}")
            if not image_path.is_file():
                total = len(image_paths)
                raise InvalidImageError(f"Image {idx}/{total} is not a file: {image_path}")

    def _verify_storage(
        self, submission_id: int, expected_image_count: int, conn: sqlite3.Connection
    ) -> None:
        """Verify submission and images were stored correctly.

        Args:
            submission_id: Submission to verify
            expected_image_count: Expected number of images
            conn: Database connection

        Raises:
            RuntimeError: If verification fails
        """
        # Verify submission exists
        if not question_submissions.exists(submission_id, conn):
            raise RuntimeError(
                f"Failed to verify submission storage (submission_id={submission_id})"
            )

        # Verify images stored
        stored_image_count = submission_images.count_images_for_submission(submission_id, conn)
        if stored_image_count != expected_image_count:
            raise RuntimeError(
                f"Image storage verification failed: expected {expected_image_count}, "
                f"got {stored_image_count}"
            )

        # Verify image sequences are sequential (no gaps)
        self._verify_sequential_images(submission_id, expected_image_count, conn)

    def _verify_sequential_images(
        self, submission_id: int, expected_count: int, conn: sqlite3.Connection
    ) -> None:
        """Verify image sequences are sequential with no gaps.

        Args:
            submission_id: Submission to verify
            expected_count: Expected number of images
            conn: Database connection

        Raises:
            RuntimeError: If sequences are not sequential
        """
        images = submission_images.get_images_for_submission(submission_id, conn)
        sequences = [img["image_sequence"] for img in images]

        # Expected: [1, 2, 3, ..., expected_count]
        expected_sequences = list(range(ImageSequence.START, expected_count + ImageSequence.START))

        if sequences != expected_sequences:
            raise RuntimeError(
                f"Image sequences are not sequential for submission {submission_id}. "
                f"Expected: {expected_sequences}, Got: {sequences}"
            )
