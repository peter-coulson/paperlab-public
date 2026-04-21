"""Loading models package.

Provides Pydantic models for validating JSON input across all loading pipelines.

Structure:
- models.config - LLM models, validation types, exam config models
- models.marks - Mark scheme models
- models.papers - Paper structure models
- models.shared - Shared base models

Usage:
    from paperlab.loading.models.config import LLMModelsInput, ExamConfigInput
    from paperlab.loading.models.marks import MarkSchemeInput
    from paperlab.loading.models.papers import PaperStructureInput
    from paperlab.loading.models.shared import PaperInstanceBase
"""
