# Code Quality Check Method

This document defines the standard method for checking code quality across all modules. Module-specific commands reference this method and specify which files to analyze.

## Overview

This is a **pure code quality check** focused on implementation standards, not business logic correctness or architecture. For architecture validation, use `/arch-check`.

## What to Read

**Required:**
- **CLAUDE.md** - Only the "Software Principles > Implementation" section
- **Target files** - Specified by the calling module command
- **Previous reports** - For the same module (if exist) to track trends

**DO NOT read:**
- CURRENT.md (not needed for code quality)
- specs/ (not needed for code quality)
- context/ (not needed for code quality)
- Other modules (only analyze specified files)

## Code Quality Standards

### 1. Simplicity and Readability

**Check:**
- Code is self-documenting (clear naming)
- Functions are small and focused (<50 lines ideally)
- No "clever" code (obscure one-liners, complex regex without explanation)
- Appropriate comments (why, not what)
- Consistent code style
- No code duplication (DRY)
- Meaningful variable/function names (no single letters except iterators)

**Violations:**
- Nested ternaries
- Deeply nested logic (>3 levels)
- Unclear variable names (`data`, `temp`, `x`)
- Clever tricks that require explanation
- Wall of code functions (>100 lines)
- Copy-pasted code blocks

### 2. Fail Fast (Validation)

**Check:**
- Input validation at module boundaries
- Early returns for invalid states
- Guard clauses instead of nested if-else
- Validation before expensive operations
- Clear error messages

**Violations:**
- Processing invalid data deep in call stack
- Late validation after expensive operations
- Silent failure modes
- Nested if-else instead of guard clauses
- Generic error messages ("Error occurred")

### 3. Expand Through Data, Not Code

**Check:**
- Subject/board/level differences in config, not conditionals
- Strategy pattern or lookup tables instead of switch statements
- Data-driven behavior
- No hard-coded business rules

**Violations:**
- `if board == 'edexcel'` in implementation code
- Switch statements on subject/level
- Hard-coded mark values
- Business logic in code instead of data

### 4. Error Handling

**Check:**
- Proper error types (custom errors for domain errors)
- Errors thrown at failure point, handled at boundary
- Meaningful error messages with context
- No silent failures (`except: pass` with no handling)
- Error messages helpful for debugging
- Stack traces preserved

**Violations:**
- Catching and ignoring errors
- Generic error types for all failures
- Error messages without context
- Swallowing errors in async code
- Using errors for control flow

### 5. Type Safety (Python)

**Check:**
- Minimal use of `Any` (none in new code)
- Strong typing for function signatures
- Type hints for public interfaces
- Proper use of Union types
- No unchecked casts without justification

**Violations:**
- `Any` types in business logic
- Unchecked type assertions
- Missing return type hints
- Optional params that should be required
- Loose `object` or `dict` types where specific types exist

### 6. Function Design

**Check:**
- Single responsibility per function
- Clear function names (verb + noun)
- Minimal parameters (≤3 ideally, use objects for more)
- Pure functions where possible
- No side effects in utility functions
- Consistent abstraction level

**Violations:**
- Functions doing multiple things
- Boolean parameters (flag arguments)
- Functions with >5 parameters
- Unclear function names
- Mixed abstraction levels
- Hidden side effects

### 7. Magic Values and Constants

**Check:**
- No magic numbers/strings
- Constants extracted and named
- **All config centralized in `config.py`** (not scattered across modules)
- Clear constant names

**Extract to config.py:**
- Duplicated strings/numbers
- DB schema constraints (field lengths, SQL fragments)
- Security rules (forbidden commands, validation regex)
- Error message templates

**Keep inline:**
- Display text that doesn't repeat
- Single-use literals ("yes", "utf-8")
- Well-known constants (standard values)

**Violations:**
- Hard-coded numbers without explanation
- String literals repeated across files
- Config constants scattered in multiple modules (not centralized)
- Over-extracted constants (simple display text as config)
- Unexplained constants
- Magic numbers in calculations

### 8. Code Organization

**Check:**
- Related code grouped together
- Clear module boundaries
- Exports are intentional (not everything exported)
- Dependencies at top of file
- Logical file structure

**Violations:**
- Unrelated code in same file
- Circular dependencies
- Wildcard imports
- Scattered imports
- God files (>500 lines without good reason)

### 9. Testability

**Check:**
- Critical business logic is pure/testable
- Dependencies can be mocked
- No hard-coded external dependencies
- Clear inputs/outputs
- Deterministic behavior

**Violations:**
- Direct `datetime.now()` calls in business logic
- Hard-coded file paths
- Business logic mixed with I/O
- Global state mutations
- Non-deterministic functions

### 10. Security Basics

**Check:**
- **No secrets in code/docs**:
  - API keys, passwords, tokens
  - Database credentials
  - Private keys
  - Search in code, config files, and documentation
- **Input validation**:
  - User input sanitized before use
  - File uploads validated (if applicable)
  - Path traversal prevention
- **SQL injection prevention**:
  - Parameterized queries used
  - No string concatenation for SQL
  - ORM used safely
- **No sensitive data in logs/errors**:
  - Error messages don't leak system info
  - Logs don't contain passwords/tokens

**Violations:**
- Hardcoded API keys, passwords, database URLs
- String concatenation in SQL queries
- Unsanitized user input used directly
- Detailed error messages exposing system info
- Secrets in comments or env.example files
- Print statements with sensitive data

**Note:** This is basic security hygiene only. For comprehensive security review, engage security specialist.

## Output Format

Generate a timestamped report and save to the location specified by the calling module command.

Use format: `YYYY-MM-DD-HHMMSS` for timestamp (e.g., `2025-11-06-143045.md`)

### Report Structure

```markdown
# Code Quality Check - {MODULE_NAME}
**Run:** {TIMESTAMP}
**Commit:** {git hash}
**Module:** {module name}
**Files:** {count} files, {count} lines
**Status:** {✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues}

## Summary
- Files analyzed: {count}
- Functions checked: {count}
- Lines of code: {count}
- Issues found: {Critical: X, Warning: Y, Info: Z}
- Code quality score: {percentage}%

## 🔴 Critical Issues [MUST FIX BEFORE PROCEEDING]

1. **[Category]** Description
   Location: `{file:line-line}`
   Issue: {what's wrong}
   Code:
   ```python
   {violating code snippet}
   ```
   Fix:
   ```python
   {suggested fix}
   ```
   Why critical: {explanation}

## 🟡 Warnings [SHOULD FIX SOON]

{Same format}

## 🔵 Info [CONSIDER]

{Same format}

## Detailed Analysis

### ✅/⚠️/❌ Simplicity and Readability
{Brief assessment with key metrics}

### ✅/⚠️/❌ Fail Fast (Validation)
{Brief assessment with key metrics}

### ✅/⚠️/❌ Expand Through Data, Not Code
- Subject/board conditionals found: {count}
- Config-driven behavior: {percentage}%

{Specific violations with file:line}

### ✅/⚠️/❌ Error Handling
{Brief assessment with key metrics}

### ✅/⚠️/❌ Type Safety
- `Any` usage: {count instances}
- Type assertions: {count}
- Missing return types: {count}
- Type safety score: {percentage}%

{Specific issues}

### ✅/⚠️/❌ Function Design
- Functions >50 lines: {count}
- Functions with >3 params: {count}
- Boolean params: {count}
- Pure functions: {percentage}%

{Specific issues}

### ✅/⚠️/❌ Magic Values and Constants
{Brief assessment}

### ✅/⚠️/❌ Code Organization
- Average file length: {lines}
- Files >500 lines: {count}
- Circular dependencies: {count}

{Specific issues}

### ✅/⚠️/❌ Testability
- Testable functions: {percentage}%
- Hard dependencies: {count}
- Side effects in business logic: {count}

{Specific issues}

### ✅/⚠️/❌ Security Basics
- Secrets in code/docs: {count found}
- SQL injection risks: {count}
- Input validation: {✅ Proper | ⚠️ Missing in places}
- Sensitive data in logs: {count instances}

{Specific security issues}

**Note:** Basic hygiene only. Consider security specialist for comprehensive review.

## Metrics

- Total files: {count}
- Total lines: {count}
- Code duplication: {percentage}%
- Type safety: {percentage}%
- Average function length: {number} lines
- Average file length: {number} lines
- Code quality score: {percentage}%

## Top Files by Issue Count

1. `{file}` - {count} issues
2. `{file}` - {count} issues
3. `{file}` - {count} issues

## Refactoring Recommendations

{Prioritized, actionable refactoring tasks}

### High Priority
1. **{file:line}** - {issue} - {fix}

### Medium Priority
1. **{file:line}** - {issue} - {fix}

### Low Priority (Tech Debt)
1. **{file:line}** - {issue} - {fix}

## Quality Trend

{If previous reports exist for this module, show improvement/regression}
- Last check: {date}
- Quality score: {old}% → {new}% ({change})
- Issues: {old count} → {new count} ({change})

---
*Next Steps: Address critical issues, then warnings. Run module check regularly during development.*
```

## Chat Output

After writing the report, display in chat:

```
{✅ | ⚠️ | ❌} Code Quality Check - {MODULE_NAME}

📄 Report: {report_path}
Quality Score: {percentage}%
Issues: {Critical: X, Warning: Y, Info: Z}

{If critical issues:}
🔴 Critical Issues:
1. {Category} - {file:line} - {brief description}
2. {Category} - {file:line} - {brief description}

{Top 3 refactoring recommendations}

{If warnings:}
🟡 {Y} warnings found. Consider addressing for code quality.

{If all clear:}
✅ Code quality excellent. No issues found.

Files analyzed: {count}
Lines of code: {count}
```

## Important Notes

- **Be thorough** - Check every file in the specified scope
- **Provide code snippets** - Show the problem AND the fix
- **Prioritize ruthlessly** - Not all issues are equal
- **Be constructive** - Suggest fixes, don't just criticize
- **Calculate metrics** - Quantify quality where possible
- **Track trends** - Compare to previous reports for this module if they exist
- **Focus on impact** - A critical issue in core logic > 10 naming issues
- **Stay in scope** - Only analyze the files specified by the calling command

## What NOT to Check

- **Architecture** - That's `/arch-check`'s job
- **Functional correctness** - Not running code, just reviewing it
- **Test results** - Just testability, not actual tests
- **Performance benchmarks** - Just obvious issues, not profiling
- **Business logic correctness** - Focus on code quality, not domain correctness
- **Files outside the specified scope** - Stay focused on the target module
