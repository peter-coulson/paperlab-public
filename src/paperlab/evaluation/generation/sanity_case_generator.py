"""Service for generating sanity test case JSON files.

Separates business logic from CLI presentation.
All file I/O happens here - CLI just orchestrates.
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from paperlab.config import settings
from paperlab.data.repositories.marking import mark_criteria, questions
from paperlab.evaluation.constants import VALIDATION_TYPE_MARK_SCHEME_SANITY
from paperlab.evaluation.services.sanity_case_auditor import audit_sanity_cases


@dataclass
class GenerationResult:
    """Result of test case generation."""

    files_created: list[tuple[Path, str | list[str]]]  # (json_path, image_filename(s))
    files_skipped: list[tuple[Path, str | list[str]]]  # (json_path, image_filename(s))
    errors: list[str]


def generate_sanity_test_cases(
    prod_conn: sqlite3.Connection,
    eval_conn: sqlite3.Connection,
) -> GenerationResult:
    """Generate sanity test case JSONs for all questions missing them.

    Only creates JSONs for questions that don't already have sanity cases.
    Uses repository layer for all database access.

    Args:
        prod_conn: Connection to production marking.db
        eval_conn: Connection to evaluation_results.db

    Returns:
        GenerationResult with list of created files and any errors

    Raises:
        ValueError: If validation_type 'mark_scheme_sanity' not found
    """
    errors = []

    # Find missing sanity cases (reuses audit logic)
    audit_report = audit_sanity_cases(prod_conn, eval_conn)
    missing_cases = audit_report.missing_cases

    if not missing_cases:
        return GenerationResult(files_created=[], files_skipped=[], errors=[])

    # Get mark criteria for missing questions (batch query)
    # Group by (paper_identifier, question_number) for efficient lookup
    criteria_by_question: dict[tuple[str, int], dict[int, int]] = {}

    for case in missing_cases:
        try:
            # Get question_id from paper_identifier + question_number
            question_id = questions.get_question_id_by_paper(
                case.paper_identifier, case.question_number, prod_conn
            )

            # Get criteria for this question (returns dict[int, int])
            expected_marks = mark_criteria.get_criteria_info_for_question(question_id, prod_conn)

            criteria_by_question[(case.paper_identifier, case.question_number)] = expected_marks

        except ValueError as e:
            errors.append(
                f"Failed to get criteria for {case.paper_identifier} Q{case.question_number}: {e}"
            )
            continue

    # Generate JSON files
    files_created = []
    files_skipped = []

    for case in missing_cases:
        key = (case.paper_identifier, case.question_number)

        if key not in criteria_by_question:
            continue  # Skip if criteria fetch failed

        expected_marks = criteria_by_question[key]

        # Create directory (case already has the directory path)
        case.case_dir.mkdir(parents=True, exist_ok=True)

        json_path = case.case_dir / case.json_filename

        # Skip if JSON already exists (preserve manually created multi-image cases)
        if json_path.exists():
            files_skipped.append((json_path, case.image_filename))
            continue

        # Use relative path from project root for portability
        # Handle both single image (string) and multi-image (list)
        if isinstance(case.image_filename, list):
            image_paths_rel = [
                str((case.case_dir / img_file).relative_to(settings.project_root))
                for img_file in case.image_filename
            ]
        else:
            image_paths_rel = [
                str((case.case_dir / case.image_filename).relative_to(settings.project_root))
            ]

        # Create test case JSON (relative path for portability)
        test_case_json = {
            "paper_identifier": case.paper_identifier,
            "question_number": case.question_number,
            "student_work_image_paths": image_paths_rel,
            "validation_type": VALIDATION_TYPE_MARK_SCHEME_SANITY,
            "notes": "Sanity check: perfect answer with full marks to validate correctness",
            "expected_marks": {str(idx): marks for idx, marks in expected_marks.items()},
        }

        # Write JSON file
        try:
            with open(json_path, "w") as f:
                json.dump(test_case_json, f, indent=2)
                f.write("\n")  # Add trailing newline

            files_created.append((json_path, case.image_filename))

        except OSError as e:
            errors.append(f"Failed to write {json_path}: {e}")
            continue

    return GenerationResult(files_created=files_created, files_skipped=files_skipped, errors=errors)
