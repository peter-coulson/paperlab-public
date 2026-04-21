"""Presentation layer - formats data structures for human/LLM consumption.

This module transforms data from repositories into human-readable or LLM-ready
formats (markdown, natural language, structured text).

Formatters are used by:
- Marking pipeline (prompt assembly)
- UI/API (display to users, future)
- CLI scripts (export/verification)

Each formatter handles one data type and contains no business logic - only
presentation transformations.

Modules:
    question_formatter: Questions and mark schemes → markdown
    mark_types_formatter: Mark type definitions → natural language
    _helpers: Shared formatting utilities (internal)
"""
