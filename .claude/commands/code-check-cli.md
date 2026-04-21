# Code Check - CLI Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** Command Line Interface
**Files to check:** `src/paperlab/cli/**/*.py`
**Report location:** `.quality/code/cli-{TIMESTAMP}.md`

## Module Description

The CLI module contains:
- Command definitions and handlers
- User input parsing
- Output formatting
- Interactive prompts
- CLI workflow orchestration

## Special Considerations

- **User-facing error messages** - Must be clear and actionable for end users
- **Input validation** - CLI is a security boundary
- **Separation of concerns** - CLI should delegate to services, not contain business logic

Run the standard code-check method on these files only.
