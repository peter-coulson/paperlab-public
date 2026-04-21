"""Paper marking services package.

Orchestrates paper marking workflow (M4):
- validation: Pre-submission validation
- submission: Paper submission orchestration
- marking: Batch marking orchestration
- grading: Grade calculation and paper completion

Usage:
    from paperlab.paper_marking import validation, submission, marking, grading
"""

__all__ = ["validation", "submission", "marking", "grading"]
