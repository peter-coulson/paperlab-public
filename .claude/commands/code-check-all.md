# Code Check - All Modules

Run code quality checks on all modules in parallel for maximum speed.

## Overview

This command launches 9 parallel code quality checks using the Task tool:
1. `code-check-data` - Data/repository layer
2. `code-check-loading` - Loading/parsing layer
3. `code-check-evaluation` - Evaluation/testing layer
4. `code-check-cli` - CLI interface
5. `code-check-domain` - Domain logic
6. `code-check-services` - Application services
7. `code-check-config` - Configuration
8. `code-check-utils` - Utilities
9. `code-check-api` - API layer (FastAPI)

Each check follows the method defined in `code-check-method.md`.

## Execution Strategy

**IMPORTANT:** Before running all checks, consider using `/code-check-recommend` to see if a full check is necessary. If only 1-2 modules need checking, run those individually instead.

**Parallel Execution:**
1. Launch all 9 module checks as parallel Task agents in a **single message**
2. Each agent independently:
   - Reads `code-check-method.md`
   - Analyzes its assigned module files
   - Generates report at `.quality/code/{module}-{TIMESTAMP}.md`
   - Returns summary with: status, score, critical count, warning count
3. Wait for all agents to complete
4. Aggregate results and display final summary

**Task prompts should be:**
```
You are running a code quality check on the {MODULE} module.

Follow the code quality checking method defined in `.claude/commands/code-check-method.md`.

**Scope:**
- Module: {MODULE_NAME}
- Files to check: {FILE_PATTERN}
- Report location: `.quality/code/{module}-{TIMESTAMP}.md`

**Module description:** {BRIEF_DESCRIPTION}

**Special considerations:** {MODULE_SPECIFIC_NOTES}

Execute the standard code-check method on these files only. Return a summary with:
1. Status (✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues)
2. Quality score (percentage)
3. Critical issues count
4. Warnings count
5. Top 3 issues (if any)
6. Report file path
```

## Module Specifications

Use these specs for each Task agent:

### 1. Data Module
- Files: `src/paperlab/data/**/*.py`
- Description: Database schema, repositories, data access layer, SQL queries
- Special: Extra emphasis on SQL injection prevention, magic strings in SQL

### 2. Loading Module
- Files: `src/paperlab/loading/**/*.py`
- Description: Data file parsers, validation logic, diff calculators, transformations
- Special: Input validation critical (boundary), helpful error messages

### 3. Evaluation Module
- Files: `src/paperlab/evaluation/**/*.py`
- Description: Test cases, test suite execution, result comparison, metrics
- Special: Deterministic behavior, clear failure messages, no side effects

### 4. CLI Module
- Files: `src/paperlab/cli/**/*.py`
- Description: Command definitions, input parsing, output formatting, prompts
- Special: User-facing error messages, input validation, delegate to services

### 5. Domain Module
- Files: `src/paperlab/marking/**/*.py`, `src/paperlab/paper_marking/**/*.py`, `src/paperlab/submissions/**/*.py`
- Description: Mark calculation, paper marking logic, submission handling, business rules
- Special: Expand through data not code (critical), pure functions, no data access

### 6. Services Module
- Files: `src/paperlab/services/**/*.py`
- Description: Application workflows, service layer, cross-cutting concerns, integrations
- Special: Layered architecture, error boundaries, mockable dependencies

### 7. Config Module
- Files: `src/paperlab/config/**/*.py`
- Description: Application configuration, environment settings, constants, validation
- Special: Central source of truth, type safety, fail fast validation

### 8. Utils Module
- Files: `src/paperlab/markdown/**/*.py`, `src/paperlab/loaders/**/*.py`, `src/paperlab/utils/**/*.py`, `src/paperlab/constants/**/*.py`
- Description: Markdown processing, generic file loaders, utilities, shared constants
- Special: No side effects, reusability, no business logic

### 9. API Module
- Files: `src/paperlab/api/**/*.py`
- Description: FastAPI application, Pydantic models, authentication, routers, status derivation
- Special: Transport only (no business logic), `from_domain()` pattern required, two-layer validation, transaction management (Pattern A), resource-oriented endpoints

## Final Summary

After all parallel checks complete, display:

```
✅/⚠️/❌ Code Check - All Modules Complete

Execution: 9 modules checked in parallel
Duration: {time taken}

Overall Results:
┌─────────────┬────────┬──────────┬──────────┬──────────┐
│ Module      │ Status │ Score    │ Critical │ Warnings │
├─────────────┼────────┼──────────┼──────────┼──────────┤
│ data        │ {icon} │ {score}% │ {count}  │ {count}  │
│ loading     │ {icon} │ {score}% │ {count}  │ {count}  │
│ evaluation  │ {icon} │ {score}% │ {count}  │ {count}  │
│ cli         │ {icon} │ {score}% │ {count}  │ {count}  │
│ domain      │ {icon} │ {score}% │ {count}  │ {count}  │
│ services    │ {icon} │ {score}% │ {count}  │ {count}  │
│ config      │ {icon} │ {score}% │ {count}  │ {count}  │
│ utils       │ {icon} │ {score}% │ {count}  │ {count}  │
│ api         │ {icon} │ {score}% │ {count}  │ {count}  │
└─────────────┴────────┴──────────┴──────────┴──────────┘

Total Critical Issues: {count}
Total Warnings: {count}
Average Quality Score: {percentage}%

{If any critical issues:}
🔴 Modules with critical issues: {list}

Top Critical Issues Across All Modules:
1. {module} - {category} - {file:line} - {brief description}
2. {module} - {category} - {file:line} - {brief description}
3. {module} - {category} - {file:line} - {brief description}

Address critical issues before proceeding.

{If only warnings:}
🟡 All modules pass, but {Y} warnings found across {X} modules.

{If all clear:}
✅ All modules meet quality standards. Excellent work!

Reports saved to: .quality/code/{module}-{TIMESTAMP}.md
```

## Error Handling

If any Task agent fails:
- Report which module check failed
- Continue with remaining checks
- Mark failed module as ❌ in summary
- Suggest running failed module check individually for debugging

## Notes

- **Parallel execution** - All 9 checks run simultaneously for speed
- **Resource intensive** - Uses 9 concurrent agents
- **Comprehensive** - Checks entire codebase
- **Use cases:**
  - Pre-release/milestone validation
  - Weekly comprehensive review
  - After major refactors
  - When baseline truth is needed
- **Consider alternatives:**
  - Run `/code-check-recommend` first to see if full check is needed
  - Use individual module checks during active development
  - Use `/quick-code-check` for incremental checking
