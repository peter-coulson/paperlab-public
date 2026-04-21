# Code Check - Evaluation Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** Evaluation/Testing Layer
**Files to check:** `src/paperlab/evaluation/**/*.py`
**Report location:** `.quality/code/evaluation-{TIMESTAMP}.md`

## Module Description

The evaluation module contains:
- Test case definitions and loaders
- Test suite execution
- Result comparison logic
- Evaluation metrics
- Test case validation

## Special Considerations

- **Deterministic behavior** - Test evaluation must be consistent and reproducible
- **Clear failure messages** - Failed test output needs to be actionable
- **No side effects** - Tests should not modify system state

Run the standard code-check method on these files only.
