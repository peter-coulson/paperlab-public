"""Path mapping utilities for exam configuration files.

Convention-based path resolution for hierarchical exam config organization.

File Structure:
    data/config/
    └── board/               # exam_board (lowercase, hyphens)
        └── level/           # exam_level (lowercase, hyphens)
            └── subject.json # subject (lowercase, hyphens)

Filename Convention:
    Exam type: PEARSON-EDEXCEL + GCSE + MATHEMATICS
    Components:
      - exam_board:    PEARSON-EDEXCEL  →  pearson-edexcel/
      - exam_level:    GCSE             →  gcse/
      - subject:       MATHEMATICS      →  mathematics.json

    Config path:     data/config/pearson-edexcel/gcse/mathematics.json

Rationale:
    - Mirrors paper file structure (board → level → subject)
    - One config per subject (contains all papers + mark types)
    - Human-navigable and predictable
    - Convention-based (no configuration needed)
"""

from pathlib import Path

from paperlab.config import settings


def exam_type_to_config_path(
    exam_board: str,
    exam_level: str,
    subject: str,
    base_dir: Path | None = None,
) -> Path:
    """Convert exam type components to config JSON path.

    Uses hierarchical directory structure organized by:
    board → level → subject.json

    Args:
        exam_board: Exam board (e.g., "PEARSON-EDEXCEL", "AQA")
        exam_level: Exam level (e.g., "GCSE", "A-LEVEL")
        subject: Subject (e.g., "MATHEMATICS", "ENGLISH-LANGUAGE")
        base_dir: Base directory for config files (default: from settings)

    Returns:
        Path to exam config JSON file

    Example:
        >>> exam_type_to_config_path("PEARSON-EDEXCEL", "GCSE", "MATHEMATICS")
        Path("data/config/pearson-edexcel/gcse/mathematics.json")

        >>> exam_type_to_config_path("AQA", "A-LEVEL", "PHYSICS")
        Path("data/config/aqa/a-level/physics.json")
    """
    # Use config path if not overridden
    if base_dir is None:
        base_dir = settings.config_path

    # Normalize components to lowercase with hyphens
    board = exam_board.lower()
    level = exam_level.lower()
    subject_name = subject.lower()

    # Build config path: board/level/subject.json
    config_path = base_dir / board / level / f"{subject_name}.json"

    return config_path


def validate_exam_config_exists(
    exam_board: str,
    exam_level: str,
    subject: str,
) -> None:
    """Validate that exam config file exists.

    Args:
        exam_board: Exam board
        exam_level: Exam level
        subject: Subject

    Raises:
        FileNotFoundError: If config file doesn't exist

    Example:
        >>> validate_exam_config_exists("PEARSON-EDEXCEL", "GCSE", "MATHEMATICS")
    """
    config_path = exam_type_to_config_path(exam_board, exam_level, subject)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Exam config file not found: {config_path}\n"
            f"Expected from exam type: {exam_board} / {exam_level} / {subject}\n"
            f"Convention: data/config/{{board}}/{{level}}/{{subject}}.json"
        )
