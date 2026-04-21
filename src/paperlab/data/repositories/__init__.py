"""Repository layer for data access.

Organized by database:
- marking.*      → marking.db (main marking database)
- evaluation.*   → evaluation_results.db (test ground truth)
- practice       → marking.db (practice question attempts)

Usage:
    from paperlab.data.repositories.marking import papers, questions
    from paperlab.data.repositories.evaluation import test_cases
    from paperlab.data.repositories import practice
"""

from paperlab.data.repositories import evaluation, marking, practice

__all__ = [
    "marking",
    "evaluation",
    "practice",
]
