"""Configuration helper functions.

Pure utility functions for configuration management that don't fit
in Settings or constants modules.
"""


def generate_paper_identifier(
    exam_board: str,
    exam_level: str,
    subject: str,
    paper_code: str,
    exam_date: str,
) -> str:
    """Generate standardized paper identifier from exam components.

    This is the single source of truth for paper identification across both
    production (marking.db) and evaluation (evaluation_results.db) databases.

    Format: {BOARD}-{LEVEL}-{SUBJECT}-{CODE}-{DATE}

    Normalization rules:
    - Convert to uppercase
    - Replace spaces with hyphens
    - Replace forward slashes with hyphens
    - Date kept in ISO format (YYYY-MM-DD)

    Args:
        exam_board: Exam board name (e.g., 'Pearson Edexcel')
        exam_level: Qualification level (e.g., 'GCSE')
        subject: Subject name (e.g., 'Mathematics')
        paper_code: Paper code (e.g., '1MA1/1H')
        exam_date: Exam date in ISO format (YYYY-MM-DD)

    Returns:
        Standardized paper identifier

    Example:
        >>> generate_paper_identifier(
        ...     "Pearson Edexcel", "GCSE", "Mathematics", "1MA1/1H", "2023-11-08"
        ... )
        'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08'

    Design rationale:
    - Derived value (never user input) eliminates inconsistency errors
    - Deterministic: same inputs always produce same identifier
    - Reversible: identifier contains all source components
    - URL-safe: only alphanumerics and hyphens
    - Human-readable: components clearly visible
    """
    # Normalize each component
    board_normalized = exam_board.upper().replace(" ", "-").replace("/", "-")
    level_normalized = exam_level.upper().replace(" ", "-").replace("/", "-")
    subject_normalized = subject.upper().replace(" ", "-").replace("/", "-")
    code_normalized = paper_code.upper().replace(" ", "-").replace("/", "-")

    # Date is already in ISO format, keep as-is
    return (
        f"{board_normalized}-{level_normalized}-{subject_normalized}-{code_normalized}-{exam_date}"
    )


def build_exam_identifier_from_metadata(
    exam_board: str,
    exam_level: str,
    subject: str,
    paper_code: str,
    year: int,
    month: int,
) -> str:
    """Build exam_identifier from year/month metadata (Flow 2 API).

    Wrapper around generate_paper_identifier for API endpoints that receive
    year/month instead of full date. Uses 1st of month as placeholder date
    since papers table requires exam_date.

    Args:
        exam_board: e.g., "Pearson Edexcel"
        exam_level: e.g., "GCSE"
        subject: e.g., "Mathematics"
        paper_code: e.g., "1MA1/3H"
        year: e.g., 2023
        month: e.g., 11 (1-12)

    Returns:
        Exam identifier matching papers.exam_identifier format

    Example:
        >>> build_exam_identifier_from_metadata(
        ...     "Pearson Edexcel", "GCSE", "Mathematics", "1MA1/3H", 2023, 11
        ... )
        'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-3H-2023-11-01'
    """
    # Use 1st of month as placeholder date
    exam_date = f"{year:04d}-{month:02d}-01"
    return generate_paper_identifier(exam_board, exam_level, subject, paper_code, exam_date)
