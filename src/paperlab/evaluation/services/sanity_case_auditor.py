"""Service for auditing sanity test case coverage.

Business logic for finding missing sanity test cases.
Separates data processing from CLI presentation.
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from paperlab.data.repositories.evaluation import test_cases, validation_types
from paperlab.data.repositories.marking import questions
from paperlab.evaluation.constants import VALIDATION_TYPE_MARK_SCHEME_SANITY
from paperlab.evaluation.loading.test_case_validators import (
    format_test_case_filenames,
    test_case_identifier_to_case_dir,
)


@dataclass
class MissingCase:
    """Information about a missing sanity test case."""

    paper_identifier: str
    question_number: int
    case_dir: Path
    json_filename: str
    image_filename: str | list[str]  # Can be single string or list for multi-image


@dataclass
class AuditReport:
    """Result of sanity case audit."""

    total_questions: int
    with_cases: int
    missing_cases: list[MissingCase]


def audit_sanity_cases(
    prod_conn: sqlite3.Connection,
    eval_conn: sqlite3.Connection,
) -> AuditReport:
    """Audit sanity test case coverage.

    Finds all questions that don't have corresponding sanity test cases.

    Args:
        prod_conn: Connection to production marking.db
        eval_conn: Connection to evaluation_results.db

    Returns:
        AuditReport with coverage statistics and missing cases

    Raises:
        ValueError: If validation_type 'mark_scheme_sanity' not found
    """
    # Get sanity validation type ID
    sanity_type_id = validation_types.get_by_code(VALIDATION_TYPE_MARK_SCHEME_SANITY, eval_conn)

    # Get existing sanity test cases
    existing_cases = test_cases.get_sanity_cases_by_validation_type(sanity_type_id, eval_conn)
    existing_keys = {(tc.paper_identifier, tc.question_number) for tc in existing_cases}

    # Get all questions from production
    all_questions = questions.get_all_with_paper_identifiers(prod_conn)

    # Calculate missing cases
    missing = []
    for q in all_questions:
        if (q.paper_identifier, q.question_number) not in existing_keys:
            case_dir = test_case_identifier_to_case_dir(q.paper_identifier)
            json_filename, image_filename = format_test_case_filenames(
                q.question_number, VALIDATION_TYPE_MARK_SCHEME_SANITY
            )
            missing.append(
                MissingCase(
                    paper_identifier=q.paper_identifier,
                    question_number=q.question_number,
                    case_dir=case_dir,
                    json_filename=json_filename,
                    image_filename=image_filename,
                )
            )

    return AuditReport(
        total_questions=len(all_questions),
        with_cases=len(existing_keys),
        missing_cases=missing,
    )
