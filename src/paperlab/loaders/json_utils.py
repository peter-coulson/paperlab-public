"""Shared JSON loading and validation utilities.

Generic utilities for JSON file operations, used across all loaders.
Domain-specific validation (e.g., paper file paths) belongs in domain modules.

Extracts common patterns from all loaders:
- File existence checking
- JSON parsing
- Pydantic validation

Used by: paper_loader, marks_loader, test_case_loader, test_suite_loader
"""

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_and_parse_json(file_path: str, model_class: type[T]) -> T:
    """Load JSON file and validate with Pydantic model.

    Handles:
    - File existence check (FileNotFoundError)
    - JSON parsing (JSONDecodeError)
    - Pydantic validation (ValidationError)

    Args:
        file_path: Path to JSON file
        model_class: Pydantic model class for validation

    Returns:
        Validated Pydantic model instance

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is malformed
        ValidationError: If JSON validation fails (Pydantic)

    Example:
        >>> from paperlab.models.paper import PaperStructureInput
        >>> paper = load_and_parse_json("data/papers/exam.json", PaperStructureInput)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(path) as f:
        json_data = json.load(f)

    return model_class.model_validate(json_data)
