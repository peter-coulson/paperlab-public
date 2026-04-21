"""Path conversion utilities for logical/absolute path handling.

Logical paths are relative to project root and used for:
- Database storage (portable across environments)
- JSON references (version control friendly)
- Cloud deployment (environment-independent)

Absolute paths are resolved at runtime for:
- File system operations (reading, validation)
- Image processing
- Actual file access

R2 paths are cloud storage keys used for:
- Production student submissions (stored in R2 bucket)
- Image retrieval via presigned URLs
- Format: submissions/{uuid}_page{NN}.{ext}

Design principles:
- Single source of truth: settings.project_root
- Consistent conversion: always use these utilities
- Type safety: Path objects for filesystem, strings for storage
"""

import re
from pathlib import Path


def to_logical_path(absolute_path: Path) -> str:
    """Convert absolute path to logical path (relative to project root).

    Args:
        absolute_path: Absolute filesystem path

    Returns:
        Logical path (string, relative to project root)

    Raises:
        ValueError: If path is not under project root

    Example:
        >>> from pathlib import Path
        >>> # Assuming project_root = /Users/user/paperlab
        >>> to_logical_path(Path("/Users/user/paperlab/data/foo.json"))
        "data/foo.json"
    """
    from paperlab.config.settings import settings

    try:
        relative = absolute_path.relative_to(settings.project_root)
        return str(relative)
    except ValueError as e:
        raise ValueError(
            f"Path is not under project root.\n"
            f"Path: {absolute_path}\n"
            f"Project root: {settings.project_root}"
        ) from e


def to_absolute_path(logical_path: str) -> Path:
    """Convert logical path to absolute path.

    Args:
        logical_path: Logical path (relative to project root)

    Returns:
        Absolute filesystem path

    Example:
        >>> # Assuming project_root = /Users/user/paperlab
        >>> to_absolute_path("data/foo.json")
        Path("/Users/user/paperlab/data/foo.json")
    """
    from paperlab.config.settings import settings

    return settings.project_root / logical_path


def to_logical_paths(absolute_paths: list[Path]) -> list[str]:
    """Convert multiple absolute paths to logical paths.

    Convenience function for batch conversion.

    Args:
        absolute_paths: List of absolute filesystem paths

    Returns:
        List of logical paths (relative to project root)

    Example:
        >>> paths = [Path("/proj/data/a.png"), Path("/proj/data/b.png")]
        >>> to_logical_paths(paths)
        ["data/a.png", "data/b.png"]
    """
    return [to_logical_path(p) for p in absolute_paths]


def to_absolute_paths(logical_paths: list[str]) -> list[Path]:
    """Convert multiple logical paths to absolute paths.

    Convenience function for batch conversion.

    Args:
        logical_paths: List of logical paths (relative to project root)

    Returns:
        List of absolute filesystem paths

    Example:
        >>> to_absolute_paths(["data/a.png", "data/b.png"])
        [Path("/proj/data/a.png"), Path("/proj/data/b.png")]
    """
    return [to_absolute_path(p) for p in logical_paths]


# R2 path format constants
R2_PATH_PREFIX = "submissions/"
R2_MAX_PATH_LENGTH = 1024  # R2 limit for object keys

# R2 path validation regex
# Format: submissions/{uuid}_page{NN}.{ext}
# - uuid: 36-character UUID v4 (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
# - page: Zero-padded 2 digits (01-99)
# - ext: jpg, png, or pdf
R2_PATH_PATTERN = re.compile(
    r"^submissions/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}_page\d{2}\.(jpg|png|pdf)$"
)


def is_r2_path(path: Path | str) -> bool:
    """Detect if path is R2 storage key vs. local filesystem path.

    Detection is based on path format (starts with submissions/).
    Not based on environment variables or database context.

    Args:
        path: Path to check (can be Path object or string)

    Returns:
        True if R2 path, False if local path

    Example:
        >>> is_r2_path("submissions/a7b3c4d5-e6f7-8901-2345-6789abcdef01_page01.jpg")
        True
        >>> is_r2_path("data/students/work/image.jpg")
        False
        >>> is_r2_path(Path("/absolute/path/image.jpg"))
        False
    """
    path_str = str(path)
    return path_str.startswith(R2_PATH_PREFIX)


def validate_r2_path(path: str) -> None:
    """Validate R2 path follows standardized format.

    Validates:
    - Path format matches submissions/{uuid}_page{NN}.{ext}
    - UUID is valid format (36 chars, lowercase hex with hyphens)
    - Page number is zero-padded 2 digits
    - File extension is jpg, png, or pdf
    - Path length is under 1024 characters (R2 limit)

    Args:
        path: R2 key to validate

    Raises:
        ValueError: If path doesn't match expected format with detailed message

    Example:
        >>> validate_r2_path("submissions/a7b3c4d5-e6f7-8901-2345-6789abcdef01_page01.jpg")
        # No error
        >>> validate_r2_path("invalid/path")
        ValueError: Invalid R2 path format: 'invalid/path'
                   Expected: submissions/{uuid}_page{NN}.{jpg|png|pdf}
    """
    # Validate path length
    if len(path) > R2_MAX_PATH_LENGTH:
        raise ValueError(
            f"R2 path exceeds {R2_MAX_PATH_LENGTH} character limit: {len(path)} chars\n"
            f"Path: {path[:100]}..."
        )

    # Validate format using regex
    if not R2_PATH_PATTERN.match(path):
        raise ValueError(
            f"Invalid R2 path format: '{path}'\n"
            f"Expected: submissions/{{uuid}}_page{{NN}}.{{jpg|png|pdf}}\n"
            f"Example: submissions/a7b3c4d5-e6f7-8901-2345-6789abcdef01_page01.jpg\n"
            f"Details:\n"
            f"  - UUID must be 36 chars (lowercase hex with hyphens)\n"
            f"  - Page number must be zero-padded 2 digits (01-99)\n"
            f"  - Extension must be jpg, png, or pdf"
        )
