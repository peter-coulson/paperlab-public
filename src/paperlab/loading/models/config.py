"""Pydantic models for configuration loading.

These models define the contract for configuration JSON files that will be loaded
into the database. They provide type safety and validation before business
rule validation and database insertion.

Contains models for:
- LLM Models configuration (data/config/llm_models.json)
- Validation Types configuration (data/evaluation/config/validation_types.json)
- Exam Config (papers + mark types) (data/config/{board}/{level}/{subject}.json)

Model to SQL Table Mapping:
- LLMModel → llm_models
- ValidationType → validation_types
- ExamPaper → exam_types
- MarkType → mark_types (expanded from mark_type_groups)
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from paperlab.config import FieldLengthLimits

# ============================================================================
# LLM Models Configuration
# ============================================================================


class LLMModel(BaseModel):
    """Single LLM model metadata.

    Represents one model available for marking operations.
    Validates field lengths and provider constraints.
    """

    model_identifier: str = Field(
        ...,
        description="Unique model identifier (e.g., 'claude-sonnet-4-5-20250929')",
        min_length=1,
        max_length=FieldLengthLimits.DISPLAY_NAME_MAX,
    )
    display_name: str = Field(
        ...,
        description="Human-readable display name (e.g., 'Claude Sonnet 4.5')",
        min_length=1,
        max_length=FieldLengthLimits.DISPLAY_NAME_MAX,
    )
    provider: str = Field(
        ...,
        description="Provider name (e.g., 'anthropic', 'openai')",
        min_length=1,
        max_length=FieldLengthLimits.EXAM_BOARD_MAX,
    )

    @field_validator("model_identifier", "display_name", "provider")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip()

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is a known provider from LLMProviders constants."""
        from paperlab.config import LLMProviders

        valid_providers = LLMProviders.all()
        if v not in valid_providers:
            raise ValueError(
                f"Unknown provider: '{v}'. Must be one of: {', '.join(valid_providers)}"
            )
        return v


class LLMModelsInput(BaseModel):
    """Root structure for LLM models configuration JSON.

    Validates entire models list and ensures no duplicate identifiers.
    """

    models: list[LLMModel] = Field(..., description="List of available LLM models")

    @field_validator("models")
    @classmethod
    def validate_unique_identifiers(cls, models: list[LLMModel]) -> list[LLMModel]:
        """Ensure all model identifiers are unique within the list."""
        identifiers = [model.model_identifier for model in models]
        duplicates = [identifier for identifier in identifiers if identifiers.count(identifier) > 1]

        if duplicates:
            unique_duplicates = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate model identifiers found: {', '.join(unique_duplicates)}. "
                f"Each model_identifier must be unique."
            )

        return models


# ============================================================================
# Validation Types Configuration
# ============================================================================


class ValidationType(BaseModel):
    """Single validation type metadata.

    Represents one category of test validation (e.g., mark_scheme_sanity, nuanced_marking).
    Used for organizing test cases in the evaluation system.
    """

    code: str = Field(
        ...,
        description="Validation type code (snake_case identifier, e.g., 'mark_scheme_sanity')",
        min_length=1,
        max_length=FieldLengthLimits.VALIDATION_TYPE_CODE_MAX,
    )
    display_name: str = Field(
        ...,
        description="Human-readable display name (e.g., 'Mark Scheme Sanity Check')",
        min_length=1,
        max_length=FieldLengthLimits.DISPLAY_NAME_MAX,
    )
    description: str = Field(
        ...,
        description="Detailed description of what this validation type tests",
        min_length=1,
        max_length=FieldLengthLimits.VALIDATION_TYPE_DESCRIPTION_MAX,
    )

    @field_validator("code", "display_name", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip()

    @field_validator("code")
    @classmethod
    def validate_snake_case(cls, v: str) -> str:
        """Validate code is in snake_case format."""
        import re

        from paperlab.config import ValidationPatterns

        if not re.match(ValidationPatterns.VALIDATION_TYPE_CODE_REGEX, v):
            raise ValueError(
                f"Validation type code must be snake_case "
                f"(lowercase letters, numbers, underscores). Must start with a letter. Got: '{v}'"
            )
        return v


class ValidationTypesInput(BaseModel):
    """Root structure for validation types configuration JSON.

    Validates entire validation types list and ensures no duplicate codes.
    """

    validation_types: list[ValidationType] = Field(
        ..., description="List of validation type categories"
    )

    @field_validator("validation_types")
    @classmethod
    def validate_unique_codes(cls, types: list[ValidationType]) -> list[ValidationType]:
        """Ensure all validation type codes are unique within the list."""
        codes = [t.code for t in types]
        duplicates = [code for code in codes if codes.count(code) > 1]

        if duplicates:
            unique_duplicates = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate validation type codes found: {', '.join(unique_duplicates)}. "
                f"Each code must be unique."
            )

        return types


# ============================================================================
# Exam Configuration (Papers + Mark Types)
# ============================================================================


class ExamPaper(BaseModel):
    """Single exam paper specification.

    Represents one paper within an exam board/level/subject.
    Maps to one row in exam_types table.
    """

    paper_code: str = Field(
        ...,
        description="Paper code (e.g., '1MA1/1H')",
        min_length=1,
        max_length=FieldLengthLimits.PAPER_CODE_MAX,
    )
    display_name: str = Field(
        ...,
        description="Human-readable paper name (e.g., 'Paper 1 (Non-Calculator)')",
        min_length=1,
        max_length=FieldLengthLimits.DISPLAY_NAME_MAX,
    )

    @field_validator("paper_code", "display_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip()


class MarkType(BaseModel):
    """Single mark type specification.

    Represents one type of mark that can be awarded (e.g., M, A, B, P, C).
    Will be expanded with paper_codes from parent MarkTypeGroup.
    """

    code: str = Field(
        ...,
        description="Mark type code (e.g., 'M', 'A', 'GENERAL')",
        min_length=1,
        max_length=FieldLengthLimits.MARK_TYPE_CODE_MAX,
    )
    display_name: str = Field(
        ...,
        description="Human-readable display name (e.g., 'Method Mark')",
        min_length=1,
        max_length=FieldLengthLimits.DISPLAY_NAME_MAX,
    )
    description: str = Field(
        ...,
        description="Detailed description of when this mark is awarded",
        min_length=1,
        max_length=FieldLengthLimits.CONTENT_TEXT_MAX,
    )

    @field_validator("code", "display_name", "description")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip()


class MarkTypeGroup(BaseModel):
    """Group of papers that share the same mark types.

    Defines which papers use which mark types. Will be expanded to create
    individual mark_types records for each (paper_code, mark_type) combination.

    Expansion logic: For each paper_code × For each mark_type → Create mark_types row
    """

    paper_codes: list[str] = Field(
        ...,
        min_length=1,
        description="List of paper codes this group applies to",
    )
    mark_types: list[MarkType] = Field(
        ...,
        min_length=1,
        description="List of mark types for these papers",
    )

    @field_validator("paper_codes")
    @classmethod
    def validate_unique_paper_codes(cls, codes: list[str]) -> list[str]:
        """Ensure no duplicate paper codes within this group."""
        duplicates = [code for code in codes if codes.count(code) > 1]
        if duplicates:
            unique_duplicates = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate paper codes in group: {', '.join(unique_duplicates)}. "
                f"Each paper_code must appear once per group."
            )
        return codes

    @field_validator("mark_types")
    @classmethod
    def validate_unique_mark_type_codes(cls, types: list[MarkType]) -> list[MarkType]:
        """Ensure no duplicate mark type codes within this group."""
        codes = [t.code for t in types]
        duplicates = [code for code in codes if codes.count(code) > 1]
        if duplicates:
            unique_duplicates = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate mark type codes in group: {', '.join(unique_duplicates)}. "
                f"Each mark type code must be unique within the group."
            )
        return types


class ExamConfigInput(BaseModel):
    """Root structure for exam configuration JSON.

    Contains papers and mark type groups for one subject within a board/level.
    One file per exam board/level/subject combination.

    File location: data/config/{board}/{level}/{subject}.json
    Example: data/config/pearson-edexcel/gcse/mathematics.json
    """

    exam_board: str = Field(
        ...,
        description="Exam board name (e.g., 'Pearson Edexcel')",
        min_length=1,
        max_length=FieldLengthLimits.EXAM_BOARD_MAX,
    )
    exam_level: str = Field(
        ...,
        description="Qualification level (e.g., 'GCSE')",
        min_length=1,
        max_length=FieldLengthLimits.EXAM_LEVEL_MAX,
    )
    subject: str = Field(
        ...,
        description="Subject name (e.g., 'Mathematics')",
        min_length=1,
        max_length=FieldLengthLimits.SUBJECT_MAX,
    )
    papers: list[ExamPaper] = Field(
        ...,
        min_length=1,
        description="All papers for this subject",
    )
    mark_type_groups: list[MarkTypeGroup] = Field(
        ...,
        min_length=1,
        description="Mark type groups (papers → mark types mappings)",
    )

    @field_validator("exam_board", "exam_level", "subject")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace."""
        return v.strip()

    @field_validator("papers")
    @classmethod
    def validate_unique_paper_codes(cls, papers: list[ExamPaper]) -> list[ExamPaper]:
        """Ensure all paper codes are unique within papers list."""
        codes = [p.paper_code for p in papers]
        duplicates = [code for code in codes if codes.count(code) > 1]
        if duplicates:
            unique_duplicates = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate paper codes found: {', '.join(unique_duplicates)}. "
                f"Each paper_code must be unique."
            )
        return papers

    @field_validator("mark_type_groups")
    @classmethod
    def validate_paper_codes_exist(
        cls, groups: list[MarkTypeGroup], info: Any
    ) -> list[MarkTypeGroup]:
        """Ensure all paper_codes in groups exist in papers list."""
        # Get papers from context (already validated)
        papers = info.data.get("papers", [])
        valid_codes = {p.paper_code for p in papers}

        # Check all group paper codes
        for group in groups:
            for paper_code in group.paper_codes:
                if paper_code not in valid_codes:
                    raise ValueError(
                        f"Mark type group references unknown paper code: '{paper_code}'. "
                        f"Valid paper codes: {sorted(valid_codes)}"
                    )
        return groups

    @field_validator("mark_type_groups")
    @classmethod
    def validate_no_duplicate_papers_across_groups(
        cls, groups: list[MarkTypeGroup], info: Any
    ) -> list[MarkTypeGroup]:
        """Ensure each paper appears in exactly one group (no duplicates across groups)."""
        all_paper_codes = [code for group in groups for code in group.paper_codes]
        duplicates = [code for code in all_paper_codes if all_paper_codes.count(code) > 1]

        if duplicates:
            unique_duplicates = sorted(set(duplicates))
            raise ValueError(
                f"Paper codes appear in multiple groups: {', '.join(unique_duplicates)}. "
                f"Each paper must appear in exactly one mark_type_group."
            )
        return groups

    @field_validator("mark_type_groups")
    @classmethod
    def validate_all_papers_covered(
        cls, groups: list[MarkTypeGroup], info: Any
    ) -> list[MarkTypeGroup]:
        """Ensure every paper in papers list appears in at least one group."""
        papers = info.data.get("papers", [])
        valid_codes = {p.paper_code for p in papers}
        covered_codes = {code for group in groups for code in group.paper_codes}

        missing = valid_codes - covered_codes
        if missing:
            raise ValueError(
                f"Papers missing from mark_type_groups: {sorted(missing)}. "
                f"Every paper must appear in exactly one mark_type_group."
            )
        return groups
