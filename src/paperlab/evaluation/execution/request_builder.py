"""Build submissions from test cases for marking execution.

Converts test cases from evaluation_results.db into submissions in test_execution.db
that can be passed to BatchMarker for parallel marking execution.

This module implements Phase A of the two-phase marking workflow:
- Phase A: Create submissions (this module)
- Phase B: Mark submissions (batch_marker.py)

Design principles:
- Single responsibility: test case → submission conversion only
- Batch operations: minimize database round-trips
- Fail fast: validate all data exists before building submissions
- Clear errors: identify missing questions/images explicitly
- Two-mode operation: normal creation vs retry-extraction reuse
"""

import sqlite3
import uuid

from paperlab.config import ImageSequence
from paperlab.data.repositories.evaluation import test_case_images, test_suite_cases
from paperlab.data.repositories.evaluation import test_cases as test_cases_repo
from paperlab.data.repositories.evaluation.execution_correlation import CorrelationData
from paperlab.data.repositories.marking import question_submissions, questions
from paperlab.loaders.path_utils import to_absolute_paths
from paperlab.submissions import SubmissionCreator, SubmissionRequest


def build_submissions_and_correlation(
    test_suite_id: int,
    student_id: int,
    eval_conn: sqlite3.Connection,
    test_conn: sqlite3.Connection,
    skip_existing: bool = False,
) -> tuple[list[int], CorrelationData]:
    """Build submissions for test suite and return correlation data.

    This function supports two modes:
    1. Normal mode (skip_existing=False): Creates new submissions for test execution
    2. Retry-extraction mode (skip_existing=True): Reuses existing submissions when
       rebuilding correlation

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        student_id: Student ID from test_execution.db (typically synthetic test student)
        eval_conn: Database connection to evaluation_results.db
        test_conn: Database connection to test_execution.db
        skip_existing: If True, reuse existing submissions instead of creating duplicates.
                      Used for retry-extraction when test_execution.db is preserved.
                      Default False for normal test execution.

    Returns:
        Tuple of (submission_ids, correlation_data):
        - submission_ids: List of submission IDs (created or reused) from test_execution.db
        - correlation_data: List of (question_id, test_case_id, first_image_path) tuples
                           for artifact extraction

    Raises:
        ValueError: If test suite has no test cases
        ValueError: If any question not found in test_execution.db
        ValueError: If skip_existing=True and submission cannot be found (data inconsistency)
        FileNotFoundError: If any student work image missing

    Example:
        >>> from paperlab.data.database import connection
        >>> from paperlab.data.evaluation_database import evaluation_connection
        >>> from paperlab.evaluation.execution.test_database import TEST_EXECUTION_DB_PATH
        >>>
        >>> with evaluation_connection() as eval_conn, \\
        ...      connection(TEST_EXECUTION_DB_PATH) as test_conn:
        ...     submission_ids, correlation = build_submissions_and_correlation(
        ...         test_suite_id=1,
        ...         student_id=1,
        ...         eval_conn=eval_conn,
        ...         test_conn=test_conn
        ...     )
        >>> # Returns: ([submission_id1, ...], [(question_id, test_case_id, first_image_path)])
    """
    # Step 1: Query all test cases for suite (single query)
    test_cases = test_suite_cases.get_test_cases_for_suite(test_suite_id, eval_conn)

    if not test_cases:
        raise ValueError(
            f"Test suite {test_suite_id} has no test cases. "
            "Cannot build submissions for empty suite."
        )

    # Step 2: Batch lookup question IDs from test_execution.db
    paper_question_pairs: list[tuple[str, int]] = [
        (str(test_case["paper_identifier"]), int(test_case["question_number"]))
        for test_case in test_cases
    ]

    question_id_map = questions.get_question_ids_batch(paper_question_pairs, test_conn)

    # Step 3: Validate all questions found
    missing_questions = [
        (paper_id, q_num)
        for (paper_id, q_num) in paper_question_pairs
        if (paper_id, q_num) not in question_id_map
    ]

    if missing_questions:
        raise ValueError(
            f"Questions not found in test_execution.db: {missing_questions}\n"
            "Ensure all required papers have been loaded into test_execution.db "
            "before building submissions."
        )

    # Step 4: Create submissions and build correlation data
    submission_ids: list[int] = []
    correlation_data: CorrelationData = []
    creator = SubmissionCreator()

    # Track first images for collision detection (within current batch)
    seen_first_images: dict[str, int] = {}  # first_image_path -> test_case_id

    # EDGE CASE: Check for collisions with existing submissions in test_execution.db
    # This handles retry-extraction or preserved test databases
    if skip_existing:
        existing_cursor = test_conn.execute(
            """
            SELECT DISTINCT si.image_path
            FROM submission_images si
            WHERE si.image_sequence = ?
            """,
            (ImageSequence.FIRST,),
        )
        existing_first_images = {row[0] for row in existing_cursor.fetchall()}
    else:
        existing_first_images = set()

    for test_case in test_cases:
        paper_id = str(test_case["paper_identifier"])
        q_num = int(test_case["question_number"])
        test_case_id = int(test_case["id"])

        # Look up question_id from batch lookup results
        question_id = question_id_map[(paper_id, q_num)]

        # Get all images for this test case (ordered by sequence)
        images = test_case_images.get_images_for_test_case(test_case_id, eval_conn)

        if not images:
            raise ValueError(
                f"Test case {test_case_id} has no images. "
                f"Every test case must have at least one image."
            )

        # Build image paths (resolve from logical to absolute)
        image_paths = to_absolute_paths([str(img["image_path"]) for img in images])

        # Validate all images exist
        for idx, image_path in enumerate(image_paths, start=1):
            if not image_path.exists():
                raise FileNotFoundError(
                    f"Image {idx}/{len(image_paths)} not found: {image_path}\n"
                    f"Referenced by test case {test_case_id}"
                )
            if not image_path.is_file():
                raise ValueError(
                    f"Image {idx}/{len(image_paths)} is not a file: {image_path}\n"
                    f"Referenced by test case {test_case_id}"
                )

        # CRITICAL: Validate first image uniqueness (runtime check)
        first_image_path = str(images[0]["image_path"])

        # Check collision within current batch
        if first_image_path in seen_first_images:
            existing_case_id = seen_first_images[first_image_path]

            # Look up existing test case details for error message
            existing_tc = test_cases_repo.get_by_id(existing_case_id, eval_conn)
            if existing_tc:
                from paperlab.evaluation.validators import format_first_image_collision_error

                # Type narrowing for mypy
                q_num_val = existing_tc["question_number"]
                if not isinstance(q_num_val, int):
                    raise TypeError(f"question_number must be int, got {type(q_num_val)}")

                error_msg = format_first_image_collision_error(
                    image_path=first_image_path,
                    existing_case_id=existing_case_id,
                    existing_json_path=str(existing_tc["test_case_json_path"]),
                    paper_identifier=str(existing_tc["paper_identifier"]),
                    question_number=q_num_val,
                    context="runtime (test suite execution)",
                )
                raise ValueError(error_msg)
            else:
                # Fallback if test case lookup fails
                raise ValueError(
                    f"CRITICAL: First image path collision in test suite!\n"
                    f"Image: {first_image_path}\n"
                    f"Used by test cases: {existing_case_id}, {test_case_id}\n"
                    f"Cannot determine which test case a marking response belongs to."
                )

        # Check collision with existing submissions (if not skip_existing mode)
        if not skip_existing and first_image_path in existing_first_images:
            raise ValueError(
                f"CRITICAL: First image collision with existing submission in test_execution.db!\n"
                f"Image: {first_image_path}\n"
                f"Test case: {test_case_id}\n"
                f"This submission already exists in the preserved test database.\n"
                f"If retry-extraction, use skip_existing=True to reuse existing submissions."
            )

        seen_first_images[first_image_path] = test_case_id

        # Create or reuse submission based on skip_existing flag
        if skip_existing:
            # Retry-extraction mode: Find existing submission by first image
            existing_submission = question_submissions.get_by_first_image(
                first_image_path=first_image_path, conn=test_conn
            )

            if existing_submission:
                submission_id = existing_submission["id"]
                # Verify it matches expected student and question
                if existing_submission["student_id"] != student_id:
                    raise ValueError(
                        f"Submission data inconsistency: expected student_id={student_id}, "
                        f"got {existing_submission['student_id']} for image {first_image_path}"
                    )
                if existing_submission["question_id"] != question_id:
                    raise ValueError(
                        f"Submission data inconsistency: expected question_id={question_id}, "
                        f"got {existing_submission['question_id']} for image {first_image_path}"
                    )
            else:
                # Skip_existing but submission doesn't exist - data inconsistency
                raise ValueError(
                    f"Retry-extraction mode but submission not found for image: "
                    f"{first_image_path}\n"
                    f"This indicates test_execution.db is incomplete or corrupted.\n"
                    f"Expected submission for: student_id={student_id}, "
                    f"question_id={question_id}"
                )
        else:
            # Normal mode: Create new submission
            # Generate UUID for submission (caller generates, not repository)
            submission_uuid = str(uuid.uuid4())

            submission_request = SubmissionRequest(
                submission_uuid=submission_uuid,
                student_id=student_id,
                question_id=question_id,
                image_paths=image_paths,
            )
            submission_id = creator.create_submission(submission_request, test_conn)
            test_conn.commit()  # Commit each submission immediately (atomic per submission)

        submission_ids.append(submission_id)

        # Build correlation (question_id, test_case_id, first_image_path)
        # Denormalized for performance and validation
        correlation_data.append((question_id, test_case_id, first_image_path))

    # Validation: ensure correlation completeness (fail fast)
    if len(correlation_data) != len(submission_ids):
        raise ValueError(
            f"Correlation data mismatch: {len(correlation_data)} correlations "
            f"for {len(submission_ids)} submissions. This indicates a bug in submission building."
        )

    if len(correlation_data) != len(test_cases):
        raise ValueError(
            f"Correlation data mismatch: {len(correlation_data)} correlations "
            f"for {len(test_cases)} test cases. This indicates a bug in submission building."
        )

    return submission_ids, correlation_data
