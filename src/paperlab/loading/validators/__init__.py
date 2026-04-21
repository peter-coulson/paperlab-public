"""Validators for paper and mark scheme loading.

This module provides Layer 2 validation (business logic) for the data loading pipeline.
Layer 1 (structural validation) is handled by Pydantic models.
Layer 3 (data integrity) is handled by database constraints.

Design principles:
- Functional approach with explicit database connection passing
- Subject-agnostic validation rules that work for all exam types
- Fail fast with clear error messages
- No duplication of database constraint checks

Module structure:
- paper_validators: Paper structure validation
- marks_validators: Mark scheme validation
- shared: Cross-validation helpers (paper ↔ marks consistency)

Usage:
    from paperlab.loading.validators.paper_validators import validate_paper_references
    from paperlab.loading.validators.marks_validators import validate_mark_scheme_structure
    from paperlab.loading.validators.shared import validate_paper_structure_exists
"""
