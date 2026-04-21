"""Pydantic models for evaluation JSON validation.

Simple models for loading ground truth test data.

Model to SQL Table Mapping:
- TestCaseInput → test_cases + test_case_images
- expected_marks dict → test_case_marks (one row per criterion_index)
- TestSuiteInput → test_suites
- test_case_json_paths list → test_suite_cases (many-to-many)
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TestCaseInput(BaseModel):
    """Test case JSON input model.

    Represents a single student answer with ground truth marks.

    Note: paper_identifier IS required as input here (unlike paper/mark scheme JSON).
    Test cases reference papers that already exist in the production database.
    The identifier should match what was generated when the paper was loaded.

    Image path convention (enforced by validator):
        data/evaluation/test_cases/{board}/{level}/{subject}/{paper_code_date}/
        q{qnum:02d}_{validation_type}_{variant:03d}_page{N}.{ext}

    JSON must be colocated with images with matching filename:
        q01_mark_scheme_sanity_001.json
        q01_mark_scheme_sanity_001_page1.png
        q01_mark_scheme_sanity_001_page2.png
    """

    paper_identifier: str = Field(
        ...,
        min_length=1,
        description=(
            "Paper identifier (auto-generated when paper was loaded) "
            "(e.g., 'PEARSON-EDEXCEL-GCSE-MATHEMATICS-1MA1-1H-2023-11-08')"
        ),
    )
    question_number: int = Field(..., gt=0, description="Question number within the paper")
    student_work_image_paths: list[str] = Field(
        ...,
        min_length=1,
        description="List of paths to student work images (relative to project root)",
    )
    validation_type: str = Field(
        ...,
        min_length=1,
        description="Validation type code (e.g., 'mark_scheme_sanity', 'nuanced_marking')",
    )
    notes: str | None = Field(None, description="Optional notes about this test case")
    expected_marks: dict[str, int] = Field(
        ...,
        description="Ground truth marks keyed by criterion_index (e.g., {'0': 1, '1': 1, '2': 0})",
    )

    @field_validator("student_work_image_paths")
    @classmethod
    def validate_at_least_one_image(cls, v: list[str]) -> list[str]:
        """Ensure at least one image path provided."""
        if not v or len(v) == 0:
            raise ValueError("At least one image path required")
        return v

    @field_validator("student_work_image_paths")
    @classmethod
    def validate_image_paths_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure no empty strings in image paths."""
        if any(not path.strip() for path in v):
            raise ValueError("Image paths cannot be empty strings")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class TestSuiteInput(BaseModel):
    """Test suite JSON input model.

    Represents a collection of test cases organized for testing purposes.

    Test suites reference test cases via their JSON path,
    which serves as a natural key (stable across database rebuilds).
    """

    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable suite name (e.g., 'GCSE Maths Baseline - Nov 2023')",
    )
    description: str | None = Field(
        None, description="Optional description of suite purpose and scope"
    )
    test_case_json_paths: list[str] = Field(
        ...,
        min_length=1,
        description="List of test case JSON paths (relative to project root)",
    )

    @field_validator("test_case_json_paths")
    @classmethod
    def validate_at_least_one_test_case(cls, v: list[str]) -> list[str]:
        """Ensure at least one test case referenced."""
        if not v or len(v) == 0:
            raise ValueError("Test suite must reference at least one test case")
        return v

    @field_validator("test_case_json_paths")
    @classmethod
    def validate_non_empty_paths(cls, v: list[str]) -> list[str]:
        """Validate that all JSON paths are non-empty strings."""
        for path in v:
            if not path or not path.strip():
                raise ValueError("test_case_json_paths cannot contain empty strings")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )
