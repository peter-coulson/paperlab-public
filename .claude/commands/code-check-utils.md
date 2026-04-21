# Code Check - Utils Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** Utilities and Helpers
**Files to check:** `src/paperlab/markdown/**/*.py`, `src/paperlab/loaders/**/*.py`, `src/paperlab/utils/**/*.py`, `src/paperlab/constants/**/*.py`
**Report location:** `.quality/code/utils-{TIMESTAMP}.md`

## Module Description

The utils module contains:
- Markdown processing and formatting
- Generic file loaders
- Utility functions
- Shared constants
- Helper classes

## Special Considerations

- **No side effects** - Utility functions should be pure where possible
- **Reusability** - Code here should be generic and not tied to specific business logic
- **No business logic** - Utils should be dumb helpers, not domain logic

Run the standard code-check method on these files only.
