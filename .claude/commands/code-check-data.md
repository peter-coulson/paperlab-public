# Code Check - Data Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** Data Layer
**Files to check:** `src/paperlab/data/**/*.py`
**Report location:** `.quality/code/data-{TIMESTAMP}.md`

## Module Description

The data module contains:
- Database schema and migrations
- Repository pattern implementations
- Data access layer
- SQL queries and database operations
- Data models and entities

## Special Considerations

- **Extra emphasis on Security Basics** - SQL injection prevention is critical
- **Watch for magic strings** - SQL fragments, table/column names should be in config
- **Repository pattern compliance** - All SQL should stay in repositories

Run the standard code-check method on these files only.
