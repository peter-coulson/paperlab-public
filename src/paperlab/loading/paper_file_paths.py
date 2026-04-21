"""Path mapping utilities for paper and mark scheme files.

Convention-based path resolution for hierarchical paper file organization.

File Structure:
    data/papers/structured/
    └── board/               # exam_board (lowercase, hyphens)
        └── level/           # exam_level (lowercase, hyphens)
            └── subject/     # subject (lowercase, hyphens)
                ├── paper_code_date.json        # Paper structure
                └── paper_code_date_marks.json  # Mark scheme

Filename Convention:
    Paper identifier: PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08
    Components:
      - exam_board:    PEARSON-EDEXCEL  →  pearson-edexcel/
      - exam_level:    GCSE             →  gcse/
      - subject:       MATHEMATICS      →  mathematics/
      - paper_code:    1MA1-1H          →  1ma1_1h
      - exam_date:     2023-11-08       →  2023_11_08

    Paper path:      pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08.json
    Mark scheme:     pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08_marks.json

Rationale:
    - Scalable: Hierarchical structure scales to thousands of papers
    - Human-navigable: Browse by board → level → subject
    - Related files together: Paper + marks in same directory
    - Predictable: Deterministic path resolution from identifier
    - Convention-based: No configuration files needed
"""

from pathlib import Path

from paperlab.config import settings


def _parse_paper_identifier(paper_identifier: str) -> tuple[str, str, str, str]:
    """Parse paper identifier into hierarchical components.

    Args:
        paper_identifier: Paper identifier
            (e.g., "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08")

    Returns:
        Tuple of (board, level, subject, base_filename)
        - board: "pearson-edexcel"
        - level: "gcse"
        - subject: "mathematics"
        - base_filename: "1ma1_1h_2023_11_08"

    Raises:
        ValueError: If paper identifier format is invalid

    Example:
        >>> _parse_paper_identifier("PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08")
        ("pearson-edexcel", "gcse", "mathematics", "1ma1_1h_2023_11_08")
    """
    # Split identifier into components
    parts = paper_identifier.split("-")

    # Validate minimum structure (board-level-subject-code-date)
    if len(parts) < 5:
        raise ValueError(
            f"Invalid paper identifier format: {paper_identifier}\n"
            "Expected format: BOARD-LEVEL-SUBJECT-CODE-DATE\n"
            "Example: PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08"
        )

    # Extract date (last 3 parts)
    date_parts = parts[-3:]
    date_str = "_".join(date_parts)  # "2023-11-08" → "2023_11_08"

    # Extract everything except date
    non_date_parts = parts[:-3]

    if len(non_date_parts) < 4:
        raise ValueError(
            f"Invalid paper identifier format: {paper_identifier}\n"
            "Must have at least: BOARD-LEVEL-SUBJECT-CODE-DATE"
        )

    # Detect board structure by checking if part[1] or part[2] is a known level
    from paperlab.config.paper_identifier_parser import KNOWN_EXAM_LEVELS

    known_levels = KNOWN_EXAM_LEVELS

    if non_date_parts[1] in known_levels:
        # Single-word board (e.g., AQA-GCSE-MATHEMATICS-...)
        board = non_date_parts[0].lower()
        level = non_date_parts[1].lower()
        subject = non_date_parts[2].lower()
        code_parts = non_date_parts[3:]
    elif non_date_parts[2] in known_levels:
        # Two-word board (e.g., PEARSON-EDEXCEL-GCSE-MATHEMATICS-...)
        board = "-".join(non_date_parts[0:2]).lower()
        level = non_date_parts[2].lower()
        subject = non_date_parts[3].lower()
        code_parts = non_date_parts[4:]
    else:
        # Default: assume two-word board
        board = "-".join(non_date_parts[0:2]).lower()
        level = non_date_parts[2].lower()
        subject = non_date_parts[3].lower()
        code_parts = non_date_parts[4:]

    # Build code string (replace hyphens with underscores)
    code_str = "_".join(p.lower() for p in code_parts)

    # Build base filename
    base_filename = f"{code_str}_{date_str}"

    return board, level, subject, base_filename


def get_hierarchical_subject_dir(paper_identifier: str, base_dir: Path) -> Path:
    """Get hierarchical directory path for a paper.

    Args:
        paper_identifier: Paper identifier
        base_dir: Base directory for files

    Returns:
        Path to subject directory (base_dir/board/level/subject)

    Raises:
        ValueError: If paper identifier format is invalid

    Example:
        >>> get_hierarchical_subject_dir(
        ...     "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08",
        ...     Path("data/papers/structured")
        ... )
        Path("data/papers/structured/pearson-edexcel/gcse/mathematics")
    """
    board, level, subject, _ = _parse_paper_identifier(paper_identifier)
    return base_dir / board / level / subject


def paper_identifier_to_json_paths(
    paper_identifier: str,
    base_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Convert paper identifier to paper and mark scheme JSON paths.

    Uses hierarchical directory structure organized by:
    board → level → subject → {paper_code}_{date}.json

    Args:
        paper_identifier: Paper identifier
            (e.g., "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08")
        base_dir: Base directory for structured papers (default: from config)

    Returns:
        Tuple of (paper_path, marks_path)

    Raises:
        ValueError: If paper identifier format is invalid

    Example:
        >>> paper_identifier_to_json_paths("PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08")
        (
            Path("data/papers/structured/pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08.json"),
            Path("data/papers/structured/pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08_marks.json")
        )
    """
    # Use config path if not overridden
    if base_dir is None:
        base_dir = settings.papers_structured_path

    # Parse identifier components
    _, _, _, base_filename = _parse_paper_identifier(paper_identifier)

    # Build directory path
    subject_dir = get_hierarchical_subject_dir(paper_identifier, base_dir)

    # Build file paths
    paper_path = subject_dir / f"{base_filename}.json"
    marks_path = subject_dir / f"{base_filename}_marks.json"

    return paper_path, marks_path


def validate_paper_files_exist(paper_identifier: str) -> None:
    """Validate that paper and mark scheme files exist.

    Args:
        paper_identifier: Paper identifier

    Raises:
        FileNotFoundError: If paper or mark scheme file doesn't exist

    Example:
        >>> validate_paper_files_exist("PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08")
    """
    paper_path, marks_path = paper_identifier_to_json_paths(paper_identifier)

    if not paper_path.exists():
        raise FileNotFoundError(
            f"Paper file not found: {paper_path}\nExpected from identifier: {paper_identifier}"
        )

    if not marks_path.exists():
        raise FileNotFoundError(
            f"Mark scheme file not found: {marks_path}\n"
            f"Expected from identifier: {paper_identifier}"
        )


def validate_paper_filename_matches_convention(file_path: str, paper_identifier: str) -> None:
    """Validate that paper file path matches the expected hierarchical convention.

    Args:
        file_path: Actual file path to paper JSON
        paper_identifier: Expected paper identifier

    Raises:
        ValueError: If file path doesn't match expected convention

    Example:
        >>> validate_paper_filename_matches_convention(
        ...     "data/papers/structured/pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08.json",
        ...     "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08"
        ... )
    """
    file_path_obj = Path(file_path)
    expected_paper_path, _ = paper_identifier_to_json_paths(paper_identifier)

    # Compare just the filename and parent directory structure
    # Allow for relative vs absolute paths by comparing the meaningful parts
    actual_parts = file_path_obj.parts
    expected_parts = expected_paper_path.parts

    # Check if the last 5 parts match (board/level/subject/filename)
    # This allows flexibility in base directory location
    if len(actual_parts) >= 5 and len(expected_parts) >= 5:
        actual_suffix = "/".join(actual_parts[-5:])
        expected_suffix = "/".join(expected_parts[-5:])

        if actual_suffix == expected_suffix:
            return  # Valid

    # If not matching, provide helpful error
    raise ValueError(
        f"Paper file path doesn't match convention\n"
        f"Actual:   {file_path}\n"
        f"Expected: {expected_paper_path}\n"
        f"Paper identifier: {paper_identifier}\n\n"
        f"Convention: data/papers/structured/board/level/subject/code_date.json"
    )


def validate_marks_filename_matches_convention(file_path: str, paper_identifier: str) -> None:
    """Validate that mark scheme file path matches the expected hierarchical convention.

    Args:
        file_path: Actual file path to mark scheme JSON
        paper_identifier: Expected paper identifier

    Raises:
        ValueError: If file path doesn't match expected convention

    Example:
        >>> validate_marks_filename_matches_convention(
        ...     "data/papers/structured/pearson-edexcel/gcse/mathematics/"
        ...     "1ma1_1h_2023_11_08_marks.json",
        ...     "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08"
        ... )
    """
    file_path_obj = Path(file_path)
    _, expected_marks_path = paper_identifier_to_json_paths(paper_identifier)

    # Compare just the filename and parent directory structure
    # Allow for relative vs absolute paths by comparing the meaningful parts
    actual_parts = file_path_obj.parts
    expected_parts = expected_marks_path.parts

    # Check if the last 5 parts match (board/level/subject/filename)
    # This allows flexibility in base directory location
    if len(actual_parts) >= 5 and len(expected_parts) >= 5:
        actual_suffix = "/".join(actual_parts[-5:])
        expected_suffix = "/".join(expected_parts[-5:])

        if actual_suffix == expected_suffix:
            return  # Valid

    # If not matching, provide helpful error
    raise ValueError(
        f"Mark scheme file path doesn't match convention\n"
        f"Actual:   {file_path}\n"
        f"Expected: {expected_marks_path}\n"
        f"Paper identifier: {paper_identifier}\n\n"
        f"Convention: data/papers/structured/board/level/subject/code_date_marks.json"
    )
