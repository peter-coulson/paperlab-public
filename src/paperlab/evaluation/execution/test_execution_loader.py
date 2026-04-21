"""Strategic loading orchestrator for test execution database.

This module coordinates loading of required data into test_execution.db:
- Resolves required papers from test cases
- Loads full JSON files (no partial loading)
- Reuses existing production loaders unchanged

Design principles:
- Load at JSON level (full files, never partial)
- Reuse production loaders (zero logic duplication)
- Fail fast (validate all files exist before loading)
- All-or-nothing (single transaction)
"""

import sqlite3
from dataclasses import dataclass

from paperlab.config import settings
from paperlab.config.paper_identifier_parser import parse_paper_identifier
from paperlab.data.repositories.evaluation import test_suite_cases
from paperlab.loading.exam_config_file_paths import (
    exam_type_to_config_path,
    validate_exam_config_exists,
)
from paperlab.loading.exam_config_loader import load_exam_config
from paperlab.loading.llm_models_loader import load_llm_models
from paperlab.loading.marks_loader import load_mark_scheme
from paperlab.loading.paper_file_paths import (
    paper_identifier_to_json_paths,
    validate_paper_files_exist,
)
from paperlab.loading.paper_loader import load_paper


@dataclass
class PaperRequirement:
    """Represents a paper that needs to be loaded.

    Attributes:
        paper_identifier: Full paper identifier
        paper_json_path: Path to paper structure JSON
        marks_json_path: Path to mark scheme JSON
        exam_board: Exam board (for config loading)
        exam_level: Exam level (for config loading)
        subject: Subject (for config loading)
    """

    paper_identifier: str
    paper_json_path: str
    marks_json_path: str
    exam_board: str
    exam_level: str
    subject: str


def load_test_execution_data(
    test_suite_id: int,
    evaluation_conn: sqlite3.Connection,
    test_execution_conn: sqlite3.Connection,
) -> None:
    """Load required data into test_execution.db for test suite.

    Strategically loads data by:
    1. Querying test cases to find unique paper_identifiers
    2. Parsing identifiers to extract exam type components
    3. Loading full exam config JSONs (all papers + mark types for each subject)
    4. Loading full paper JSONs (one per unique paper_identifier)
    5. Loading full mark scheme JSONs (one per unique paper_identifier)
    6. Loading all LLM models (lightweight metadata)

    Key principle: Loads complete JSON files using existing loaders unchanged.

    Args:
        test_suite_id: Test suite ID from evaluation_results.db
        evaluation_conn: Connection to evaluation_results.db (read-only)
        test_execution_conn: Connection to test_execution.db (write)

    Raises:
        ValueError: If test suite doesn't exist or has no test cases
        FileNotFoundError: If any required JSON file is missing
        sqlite3.Error: If database operations fail

    Example:
        >>> with connection(eval_db) as eval_conn, connection(test_db) as test_conn:
        ...     load_test_execution_data(suite_id, eval_conn, test_conn)
    """
    # 1. Resolve required papers from test cases
    paper_requirements = _resolve_paper_requirements(test_suite_id, evaluation_conn)

    if not paper_requirements:
        raise ValueError(
            f"Test suite {test_suite_id} has no test cases. Cannot execute empty test suite."
        )

    # 2. Validate all required files exist BEFORE loading
    _validate_all_files_exist(paper_requirements)

    # 3. Load data in correct order (dependencies first)
    try:
        # Phase 1: Load LLM models (no dependencies)
        _load_llm_models(test_execution_conn)

        # Phase 2: Load exam configs (grouped by subject)
        _load_exam_configs(paper_requirements, test_execution_conn)

        # Phase 3: Load papers and mark schemes
        _load_papers_and_marks(paper_requirements, test_execution_conn)

        # Commit all changes
        test_execution_conn.commit()

    except Exception:
        # Rollback on any error
        test_execution_conn.rollback()
        raise


def _resolve_paper_requirements(
    test_suite_id: int,
    evaluation_conn: sqlite3.Connection,
) -> list[PaperRequirement]:
    """Resolve unique papers required for test suite.

    Queries test cases to extract paper_identifiers, then maps each to:
    - Paper JSON path
    - Mark scheme JSON path
    - Exam type components (for config loading)

    Args:
        test_suite_id: Test suite ID
        evaluation_conn: Connection to evaluation_results.db

    Returns:
        List of PaperRequirement objects (one per unique paper)

    Raises:
        ValueError: If test suite has no test cases
    """
    # Query unique paper identifiers for this suite
    paper_identifiers = test_suite_cases.get_unique_paper_identifiers_for_suite(
        test_suite_id, evaluation_conn
    )

    if not paper_identifiers:
        return []

    # Map each paper_identifier to file paths and exam type
    requirements = []
    for paper_id in paper_identifiers:
        # Get JSON paths
        paper_path, marks_path = paper_identifier_to_json_paths(paper_id)

        # Parse paper_identifier to extract exam type components
        components = parse_paper_identifier(paper_id)

        requirements.append(
            PaperRequirement(
                paper_identifier=paper_id,
                paper_json_path=str(paper_path),
                marks_json_path=str(marks_path),
                exam_board=components.board,
                exam_level=components.level,
                subject=components.subject,
            )
        )

    return requirements


def _validate_all_files_exist(requirements: list[PaperRequirement]) -> None:
    """Validate all required JSON files exist before loading.

    Fails fast if any file is missing. Better to fail before database
    operations than halfway through loading.

    Args:
        requirements: List of paper requirements

    Raises:
        FileNotFoundError: If any required file doesn't exist
    """
    # Check paper and marks files
    for req in requirements:
        validate_paper_files_exist(req.paper_identifier)

    # Check exam config files (unique subjects only)
    unique_subjects = {(req.exam_board, req.exam_level, req.subject) for req in requirements}

    for board, level, subject in unique_subjects:
        validate_exam_config_exists(board, level, subject)

    # Check LLM models file
    llm_models_path = settings.config_path / "llm_models.json"
    if not llm_models_path.exists():
        raise FileNotFoundError(
            f"LLM models config not found: {llm_models_path}\nRequired for test execution."
        )


def _load_llm_models(conn: sqlite3.Connection) -> None:
    """Load all LLM models from config JSON.

    Loads complete llm_models.json file (all models).
    Uses production loader unchanged.

    Args:
        conn: Connection to test_execution.db
    """
    llm_models_path = settings.config_path / "llm_models.json"
    load_llm_models(str(llm_models_path), conn)


def _load_exam_configs(
    requirements: list[PaperRequirement],
    conn: sqlite3.Connection,
) -> None:
    """Load exam configs for all unique subjects.

    Loads complete exam config JSONs (all papers + mark types per subject).
    Uses production loader unchanged.

    Args:
        requirements: List of paper requirements
        conn: Connection to test_execution.db
    """
    # Group by unique subject (only load each config once)
    unique_subjects = {(req.exam_board, req.exam_level, req.subject) for req in requirements}

    for board, level, subject in sorted(unique_subjects):
        config_path = exam_type_to_config_path(board, level, subject)
        load_exam_config(str(config_path), conn)


def _load_papers_and_marks(
    requirements: list[PaperRequirement],
    conn: sqlite3.Connection,
) -> None:
    """Load papers and mark schemes for all required papers.

    Loads complete paper and mark scheme JSONs (one per paper_identifier).
    Uses production loaders unchanged.

    Args:
        requirements: List of paper requirements
        conn: Connection to test_execution.db
    """
    for req in requirements:
        # Load paper structure
        load_paper(req.paper_json_path, conn)

        # Load mark scheme
        load_mark_scheme(req.marks_json_path, conn)
