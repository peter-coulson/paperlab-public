# Code Check - Loading Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** Loading/Parsing Layer
**Files to check:** `src/paperlab/loading/**/*.py`
**Report location:** `.quality/code/loading-{TIMESTAMP}.md`

## Module Description

The loading module contains:
- Data file parsers (YAML, JSON, PDF, etc.)
- Validation logic
- Diff calculators
- Data transformation pipelines
- Exam configuration loaders

## Special Considerations

- **Input validation is critical** - This is the boundary where external data enters
- **Error messages** - Should be helpful for users debugging config files
- **No business logic** - This layer should only load/validate, not make decisions

Run the standard code-check method on these files only.
