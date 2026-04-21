You are conducting a **Quick Code Quality Check** for recently changed files in this codebase.

Think hard about code quality in the changed files - this requires focused analysis on what actually changed and its immediate impact.

## Objective

Perform fast, incremental code quality validation on files changed since the last quality check (either full code-check or quick-code-check). This enables frequent quality checks without the overhead of analyzing the entire codebase.

## Prerequisites

**CRITICAL:** Before starting:
- Context system is healthy (has CLAUDE.md and basic structure)
- `src/` directory exists (if not, report that quick-check is premature)
- This is a LIGHTWEIGHT check focused on changed files only

## Finding the Baseline Commit

**Use bash tools (grep/head) to find the latest check commit WITHOUT loading full reports:**

```bash
# Find latest commit from either code-check or quick-code-check reports
grep "^\*\*Commit:\*\*" .quality/code/*.md .quality/quick-code/*.md 2>/dev/null | \
  tail -1 | \
  sed 's/.*Commit:\*\* //' | \
  awk '{print $1}'
```

If no previous reports exist, analyze all files (same as full code-check but note this in report).

## Files to Analyze

**Step 1: Get changed files since baseline**
```bash
git diff --name-only {baseline_commit}..HEAD -- 'src/**/*.py'
```

**Step 2: Identify direct dependencies** (files that import changed files)
For each changed file, use grep to find importers:
```bash
# Example: if src/domain/question.py changed
grep -r "from.*domain.question import\|from domain import.*question" src/ --include="*.py" -l
```

**Analysis depth:**
- **Changed files:** DEEP analysis (all quality checks)
- **Dependency files:** SHALLOW analysis (check if change breaks interface/contracts only)

## Context Files to Read

**Always read (lightweight):**
- `CLAUDE.md` - Implementation principles (using head/grep for relevant sections if needed)

**Read for changed files only:**
- The actual changed Python files in src/
- Direct importers/dependencies (shallow read)

**DO NOT read:**
- All of context/ (not needed for incremental check)
- All of specs/ (not needed for incremental check)
- Unchanged source files
- Previous full reports (only extracted commit hash)

## Code Quality Standards to Check

Use the SAME standards as /code-check but apply ONLY to changed files:

### 1. Simplicity and Readability
- Clear naming, no clever code
- Functions <50 lines ideally
- No duplication

### 2. Fail Fast (Validation)
- Input validation at boundaries
- Guard clauses over nested if-else

### 3. Expand Through Data, Not Code
- No subject/board/level conditionals in code

### 4. Error Handling
- Proper error types
- Meaningful messages with context

### 5. Type Safety
- Minimal `any` usage
- Strong typing for signatures

### 6. Function Design
- Single responsibility
- Clear names (verb + noun)
- ≤3 parameters ideally

### 7. Magic Values and Constants
- No magic numbers/strings
- Extract to config.py (check if value is already there)

### 8. Security Basics
- No secrets in changed files
- Input validation
- Parameterized queries (if SQL touched)

## Dependency Impact Analysis

For files that IMPORT changed files (shallow check):

**Check only:**
- Does the change break the import?
- Are public interfaces maintained?
- Are type signatures still compatible?
- Quick scan for obvious issues (no deep analysis)

**Example:**
If `question.py` changed its `Question.__init__` signature, check files importing `Question` to see if they're now broken.

## Output Format

Generate a timestamped report and save to `.quality/quick-code/{TIMESTAMP}.md`

Use format: `YYYY-MM-DD-HHMMSS` for timestamp (e.g., `2025-10-26-143045.md`)

### Report Structure

```markdown
# Quick Code Quality Check
**Run:** {TIMESTAMP}
**Commit:** {current git hash}
**Baseline:** {baseline commit hash from last check}
**Mode:** Incremental (changed files only)
**Status:** {✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues}

## Summary
- Files changed: {count}
- Dependencies checked: {count}
- Total analyzed: {count} of {total src files} files
- Issues found: {Critical: X, Warning: Y, Info: Z}
- Code quality score: {percentage}%

## Changed Files Analyzed

{List of files changed since baseline with line count changes}

1. `src/domain/question.py` (+45, -12 lines)
2. `src/data/repository.py` (+8, -3 lines)
3. `src/cli/commands.py` (+120, -0 lines) - NEW FILE

## Dependencies Checked (Shallow)

{List of files that import changed files}

1. `src/domain/paper.py` (imports question.py) - ✅ No issues
2. `src/services/marker.py` (imports question.py) - ✅ No issues

## 🔴 Critical Issues [MUST FIX BEFORE PROCEEDING]

{Same format as code-check, but only for changed files}

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

### Changed Files (Deep Analysis)

#### `src/domain/question.py` {✅|⚠️|❌}

**Changes made:**
- Added new validation method
- Modified __init__ signature
- Extracted constants

**Quality assessment:**
- ✅ Simplicity and Readability
- ✅ Fail Fast
- ✅ Type Safety
- ⚠️ Magic Values (found 1 hardcoded string)

**Issues:**
{Specific issues if any}

#### `src/data/repository.py` {✅|⚠️|❌}

{Same format for each changed file}

### Dependency Impact (Shallow Check)

#### Files importing changed modules: ✅ No breaks detected

- `src/domain/paper.py` - Interface compatible
- `src/services/marker.py` - Interface compatible

## Metrics

- Files changed: {count}
- Lines added: {count}
- Lines removed: {count}
- Dependencies checked: {count}
- Issues per changed file: {average}
- Quality score (changed files): {percentage}%

## Comparison to Baseline

**Baseline commit:** {hash} ({date of last check})
**Commits since baseline:** {count}

{If previous report exists, compare}
- Quality score: {old}% → {new}% ({change})
- Issues: {old count} → {new count} ({change})

## Recommendations

{Prioritized, actionable fixes for changed files only}

### High Priority
1. **{file:line}** - {issue} - {fix}

### Medium Priority
1. **{file:line}** - {issue} - {fix}

### Low Priority
1. **{file:line}** - {issue} - {fix}

## Next Steps

{If critical issues:}
⚠️ Fix critical issues in changed files before committing.

{If warnings only:}
✅ No blocking issues. Consider addressing {Y} warnings.

{If all clear:}
✅ All changed files meet quality standards.

---
*For comprehensive analysis of all files, run /code-check*
*Next quick check will use this commit as baseline: {current hash}*
```

## Chat Output

After writing the report, display in chat:

```
{✅ | ⚠️ | ❌} Quick Code Check Complete

📄 Report: .quality/quick-code/{TIMESTAMP}.md
Analyzed: {X} changed files + {Y} dependencies (of {Z} total files)
Quality Score: {percentage}%
Issues: {Critical: X, Warning: Y, Info: Z}

Changed files:
- src/domain/question.py (+45, -12 lines)
- src/data/repository.py (+8, -3 lines)

{If critical issues:}
🔴 Critical Issues:
1. {Category} - {file:line} - {brief description}

{If warnings:}
🟡 {Y} warnings found in changed files.

{If all clear:}
✅ All changed files meet quality standards.

Baseline: {baseline_commit} → Current: {current_commit}
Commits analyzed: {count}
```

## Important Notes

- **Speed is key** - This should be 5-10x faster than full code-check
- **Use grep/head for baseline** - Don't load full report files
- **Focus on changed files** - No analysis of unchanged code
- **Shallow dependency checks** - Just interface compatibility, not deep analysis
- **Clear scope transparency** - Always show "X of Y files analyzed"
- **Complement, don't replace** - This augments /code-check, doesn't replace it

## When to Use Each Check

**Use /quick-code-check:**
- After each commit or work session
- Before pushing to remote
- During active development
- When you want fast feedback

**Use /code-check:**
- Weekly comprehensive review
- Before releases/milestones
- After major refactors
- When baseline truth is needed

## Efficiency Guidelines

**DO:**
- Use `git diff --stat` to get line change counts efficiently
- Use `grep` to find dependencies without full file reads
- Read only changed files deeply
- Extract commit hash with `grep`/`head`, not full report reads

**DON'T:**
- Read entire context/ directory
- Analyze unchanged files
- Load previous full reports (just extract hash)
- Perform deep analysis on dependency files (just check interfaces)

## Auto-Fix Support

After writing the report, if auto-fixable issues exist in changed files:

"I found {X} auto-fixable issues in changed files. Apply fixes?

Options:
- 'all' - Apply all {X} fixes
- 'critical' - Only critical ({count})
- 'safe' - Only LOW risk fixes ({count})
- 'no' - Skip auto-fix

Your choice: "

Same auto-fix flow as /code-check, but only for changed files.
