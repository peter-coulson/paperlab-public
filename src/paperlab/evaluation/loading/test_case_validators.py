"""Validators for test case loading.

Enforces hierarchical path conventions and atomic JSON/image coupling.
"""

from pathlib import Path

from paperlab.config import SUPPORTED_IMAGE_FORMATS, settings
from paperlab.loading.paper_file_paths import _parse_paper_identifier


def format_test_case_filenames(
    question_number: int,
    validation_type: str,
    sequence: int = 1,
    image_count: int = 1,
) -> tuple[str, list[str]]:
    """Format test case JSON and image filenames.

    Args:
        question_number: Question number (1-indexed)
        validation_type: Validation type code (e.g., "mark_scheme_sanity")
        sequence: Sequence number for this validation type (default: 1)
        image_count: Number of images for this test case (default 1)

    Returns:
        Tuple of (json_filename, image_filenames)
        Example: ("q01_mark_scheme_sanity_001.json",
                  ["q01_mark_scheme_sanity_001_page1.png",
                   "q01_mark_scheme_sanity_001_page2.png"])
    """
    # Base filename (without extension)
    base = f"q{question_number:02d}_{validation_type}_{sequence:03d}"

    json_filename = f"{base}.json"

    # Generate image filenames with page suffixes
    if image_count == 1:
        # Single image: no suffix (backward compatible naming)
        image_filenames = [f"{base}.png"]
    else:
        # Multiple images: add _page1, _page2, etc.
        image_filenames = [f"{base}_page{i}.png" for i in range(1, image_count + 1)]

    return json_filename, image_filenames


def test_case_identifier_to_case_dir(
    paper_identifier: str,
    base_dir: Path | None = None,
) -> Path:
    """Convert paper identifier to test case directory.

    Uses hierarchical directory structure organized by:
    board → level → subject → paper_code_date/

    Reuses paper identifier parsing logic for consistency with paper JSONs.

    Args:
        paper_identifier: Paper identifier
            (e.g., "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08")
        base_dir: Base directory for test cases (default: from config)

    Returns:
        Path to test case directory for this paper (contains JSON + image pairs)

    Raises:
        ValueError: If paper identifier format is invalid

    Example:
        >>> test_case_identifier_to_case_dir(
        ...     "PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08"
        ... )
        Path("data/evaluation/test_cases/pearson-edexcel/gcse/mathematics/1ma1_1h_2023_11_08")
    """
    # Use config path if not overridden
    if base_dir is None:
        base_dir = settings.evaluation_test_cases_path

    # Parse identifier components (reuses paper parsing logic)
    board, level, subject, base_filename = _parse_paper_identifier(paper_identifier)

    # Build directory path: base_dir/board/level/subject/paper_code_date
    return base_dir / board / level / subject / base_filename


def validate_json_and_images_coupling(
    test_case_json_path: Path,
    student_work_image_paths: list[str],
    paper_identifier: str,
    question_number: int,
    validation_type: str,
) -> None:
    """Validate JSON and all its images exist and follow naming conventions.

    Validates:
    1. All image paths are non-empty
    2. All images exist as files
    3. All images in correct directory
    4. Filenames follow convention (optional strict mode)

    Args:
        test_case_json_path: Path to test case JSON
        student_work_image_paths: List of image paths from JSON
        paper_identifier: Paper identifier from test case JSON
        question_number: Question number from test case JSON
        validation_type: Validation type code from test case JSON

    Raises:
        ValueError: If validation fails
        FileNotFoundError: If any image doesn't exist
    """
    # Validate at least one image
    if not student_work_image_paths:
        raise ValueError(f"Test case has no images: {test_case_json_path}")

    # Resolve JSON parent directory (absolute path)
    json_parent_resolved = test_case_json_path.parent.resolve()

    # Validate directory matches convention
    expected_dir = test_case_identifier_to_case_dir(paper_identifier)
    if json_parent_resolved != expected_dir:
        raise ValueError(
            f"Directory doesn't match convention\n"
            f"Actual:   {json_parent_resolved}\n"
            f"Expected: {expected_dir}\n\n"
            f"Convention: data/evaluation/test_cases/"
            f"{{board}}/{{level}}/{{subject}}/{{paper_code_date}}/"
        )

    # Validate all images exist and are colocated
    for idx, image_path_str in enumerate(student_work_image_paths, start=1):
        image_path = Path(image_path_str)

        # Check image exists
        if not image_path.exists():
            raise FileNotFoundError(
                f"Image {idx}/{len(student_work_image_paths)} not found: {image_path}\n"
                f"Referenced by: {test_case_json_path}"
            )

        if not image_path.is_file():
            raise ValueError(
                f"Image {idx}/{len(student_work_image_paths)} is not a file: {image_path}\n"
                f"Referenced by: {test_case_json_path}"
            )

        # Check colocated (atomic coupling requirement)
        image_parent_resolved = image_path.parent.resolve()
        if image_parent_resolved != json_parent_resolved:
            raise ValueError(
                f"Image {idx}/{len(student_work_image_paths)} not colocated with JSON\n"
                f"JSON:  {json_parent_resolved}\n"
                f"Image: {image_parent_resolved}\n"
                f"All images must be in same directory as JSON (atomic coupling)"
            )

        # Validate image extension
        image_ext = image_path.suffix.lower()
        if image_ext not in SUPPORTED_IMAGE_FORMATS:
            supported = ", ".join(SUPPORTED_IMAGE_FORMATS.keys())
            raise ValueError(
                f"Image {idx}/{len(student_work_image_paths)} has unsupported format: {image_ext}\n"
                f"Supported formats: {supported}\n"
                f"Filename: {image_path.name}"
            )
