"""Helper functions for exam configuration loading.

Provides utilities for:
- Mark type group expansion (cross product of papers × mark_types)
- Expected count calculations for verification
- Path component normalization for CLI
"""

import sqlite3
from pathlib import Path

from paperlab.data.repositories.marking import exam_types
from paperlab.loading.models.config import ExamConfigInput, MarkTypeGroup


def expand_mark_type_groups(
    config: ExamConfigInput, conn: sqlite3.Connection
) -> list[tuple[int, str, str, str]]:
    """Expand mark_type_groups into flat list of mark_types inserts.

    For each group:
        For each paper_code in group.paper_codes:
            Look up exam_type_id for paper_code
            For each mark_type in group.mark_types:
                Create tuple: (exam_type_id, code, display_name, description)

    Args:
        config: Parsed exam configuration from JSON
        conn: Database connection (needed to look up exam_type_ids)

    Returns:
        List of (exam_type_id, code, display_name, description) tuples
        ready for batch insert via mark_types.create_mark_types_batch()

    Example:
        If group has paper_codes=['1MA1/1H', '1MA1/2H']
        and mark_types=[{code: 'M', ...}, {code: 'A', ...}]

        Result: 4 tuples (2 papers × 2 mark_types)
        - (exam_type_id_for_1H, 'M', 'Method Mark', '...')
        - (exam_type_id_for_1H, 'A', 'Accuracy Mark', '...')
        - (exam_type_id_for_2H, 'M', 'Method Mark', '...')
        - (exam_type_id_for_2H, 'A', 'Accuracy Mark', '...')
    """
    mark_type_tuples: list[tuple[int, str, str, str]] = []

    for group in config.mark_type_groups:
        for paper_code in group.paper_codes:
            # Look up exam_type_id for this paper
            exam_type_id = exam_types.get_by_exam_type(
                config.exam_board, config.exam_level, config.subject, paper_code, conn
            )

            # Create mark_type for each mark type in group
            for mark_type in group.mark_types:
                mark_type_tuples.append(
                    (exam_type_id, mark_type.code, mark_type.display_name, mark_type.description)
                )

    return mark_type_tuples


def calculate_expected_mark_types(mark_type_groups: list[MarkTypeGroup]) -> int:
    """Calculate expected mark_types count after expansion.

    Args:
        mark_type_groups: List of mark type groups from JSON

    Returns:
        Expected count: sum(len(group.paper_codes) × len(group.mark_types) for each group)

    Example:
        Group 1: paper_codes=[A, B], mark_types=[M, A] → 2 × 2 = 4
        Group 2: paper_codes=[C], mark_types=[M, A, X] → 1 × 3 = 3
        Total: 4 + 3 = 7
    """
    return sum(len(group.paper_codes) * len(group.mark_types) for group in mark_type_groups)


def normalize_path_component(component: str) -> str:
    """Normalize path component for file system.

    Converts exam board/level/subject names to lowercase with hyphens.

    Args:
        component: Component to normalize (e.g., 'Pearson Edexcel', 'GCSE', 'Mathematics')

    Returns:
        Normalized component (e.g., 'pearson-edexcel', 'gcse', 'mathematics')

    Rules:
        - Convert to lowercase
        - Replace spaces with hyphens
        - Preserve other characters as-is

    Examples:
        'Pearson Edexcel' → 'pearson-edexcel'
        'GCSE' → 'gcse'
        'Mathematics' → 'mathematics'
        'A-Level' → 'a-level' (hyphen preserved)
    """
    return component.lower().replace(" ", "-")


def construct_config_path(
    exam_board: str, exam_level: str, subject: str, config_base_path: Path
) -> Path:
    """Construct file path for exam config JSON.

    Args:
        exam_board: Exam board name (e.g., 'Pearson Edexcel')
        exam_level: Qualification level (e.g., 'GCSE')
        subject: Subject name (e.g., 'Mathematics')
        config_base_path: Base config directory (e.g., settings.config_path)

    Returns:
        Path to config file: {base}/{board}/{level}/{subject}.json

    Example:
        construct_config_path('Pearson Edexcel', 'GCSE', 'Mathematics', Path('data/config'))
        → Path('data/config/pearson-edexcel/gcse/mathematics.json')
    """
    board_normalized = normalize_path_component(exam_board)
    level_normalized = normalize_path_component(exam_level)
    subject_normalized = normalize_path_component(subject)

    return config_base_path / board_normalized / level_normalized / f"{subject_normalized}.json"
