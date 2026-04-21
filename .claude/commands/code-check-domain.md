# Code Check - Domain Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** Domain Logic
**Files to check:** `src/paperlab/marking/**/*.py`, `src/paperlab/paper_marking/**/*.py`, `src/paperlab/submissions/**/*.py`
**Report location:** `.quality/code/domain-{TIMESTAMP}.md`

## Module Description

The domain module contains:
- Mark calculation and aggregation
- Paper marking logic
- Submission handling
- Core business rules
- Domain entities and value objects

## Special Considerations

- **Expand through data, not code** - Critical here: subject/board/level logic should be data-driven
- **Pure functions preferred** - Business logic should be testable without side effects
- **No data access** - Domain logic should call repositories, never execute SQL

Run the standard code-check method on these files only.
