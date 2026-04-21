You are conducting a **Context System Audit** for this codebase.

This is a comprehensive analysis covering integrity validation AND quality assessment.

## Objective

Validate integrity and assess health of the documentation system through complete content analysis.

**Scope:** Documentation only (`context/`, `CLAUDE.md`, `CURRENT.md`, `specs/`, `analysis/`). Does NOT examine `src/`.

**Expected time:** 5-10 minutes

---

## Phase 1: Build File Checklist

**Objective:** Determine exactly which files to read.

**Steps:**
1. Read `context/README.md` - extract all files from "When to Use This" section
2. Add core files: `CLAUDE.md`, `CURRENT.md`
3. Glob `context/**/*.md` for all context files
4. Read `specs/README.md` - extract active specs
5. Read `analysis/README.md` - extract listed files

**Track as:**
```
Core: CLAUDE.md, CURRENT.md, context/README.md
Context files: [list from glob]
Specs: [list from specs/README.md]
Analysis: [list from analysis/README.md]
Expected total: X files
```

---

## Phase 2: Load All Content

**Objective:** Read every file completely into context.

**Rules:**
- ✅ Read EVERY file completely (no limit/offset parameters)
- ✅ Track each file: `✓ filename (X lines)`
- ❌ NEVER skip files or use partial reads

**Output:**
```
✓ CLAUDE.md (X lines)
✓ CURRENT.md (X lines)
... all files ...
Total: X files, ~Y lines
```

---

## Phase 3: Verification Gate

**Objective:** Ensure no files missed.

Compare: Expected (Phase 1) vs Actual (Phase 2)

- ✅ If match: Proceed to Phase 4
- ❌ If mismatch: STOP, read missing files, re-verify

**Do not proceed until this passes.**

---

## Phase 4: Integrity Analysis

### 4.1 Reference Integrity
- Extract all file paths mentioned across docs
- Verify each exists (use `test -f` or `ls`)
- Check directory structure matches CLAUDE.md navigation

### 4.2 Documentation Completeness
- CLAUDE.md has: Current Scope, Software Principles, Documentation, Navigation
- CURRENT.md has: Milestone definition, task list, no orphaned references
- Context structure matches context/README.md

### 4.3 CURRENT.md Consistency
- Milestone matches CLAUDE.md
- Task status valid (pending/in progress/completed)
- All file references exist
- No stale tasks (in progress >7 days)

### 4.4 Schema Consistency
- Tables in context docs have schema files
- Schema structure matches documentation

### 4.5 Security Scan
- Check `.env` not tracked: `git ls-files | grep "\.env$"`
- Grep for secrets in docs (distinguish real secrets vs benign mentions)

### 4.6 Cross-File Consistency
- Same concepts use same terms everywhere
- Module references in ARCHITECTURE.md documented elsewhere
- No mentions of deprecated/deleted systems

---

## Phase 5: Quality Analysis

### 5.1 Redundancy Detection

**CLI Documentation:**
- Read `context/backend/CLI.md` (if exists)
- Run `uv run paperlab --help` for comparison
- Flag if >50% duplicates `--help` output

**Schema Documentation:**
- Find schema docs and corresponding Pydantic models (`src/**/models*.py`)
- Flag if docs duplicate model Field() descriptions

**Example Content:**
- Flag complete JSON/SQL examples that exist as actual files in `data/`

### 5.2 File Size Evaluation

**Thresholds:**
- 🟢 <350 lines: Healthy
- 🟡 350-400 lines: Monitor
- 🟠 400-450 lines: Review for trimming
- 🔴 >450 lines: Action required

**Content density:** Calculate code block % vs prose for large files (>350 lines)

### 5.3 Purpose Alignment

**Reference:** `context/GOVERNANCE.md` → Content Principles

**Golden Rule:** Document WHY and WHERE, not WHAT and HOW

**Flag misaligned content:**
- Command-by-command docs (duplicates `--help`)
- Field-by-field schemas (duplicates Pydantic models)
- Complete examples (duplicates actual files)
- Step-by-step tutorials (duplicates code)

### 5.4 Maintenance Metrics

Calculate and report:

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total files | X | 10-30 | ✅/⚠️/❌ |
| Total lines | X | 7,500-13,000 | ✅/⚠️/❌ |
| Avg file size | X | 150-300 | ✅/⚠️/❌ |
| Max file size | X | <450 | ✅/⚠️/❌ |
| Files >400 lines | X | 0-2 | ✅/⚠️/❌ |
| Files >450 lines | X | 0 | ✅/⚠️/❌ |

### 5.5 Structure Evaluation

- Current structure (flat/nested)
- Navigation efficiency
- Recommendation: Keep flat until 20+ files

---

## Phase 6: Generate Report

Save to: `.quality/context/{YYYY-MM-DD-HHMMSS}.md`

```markdown
# Context System Audit
**Run:** {TIMESTAMP}
**Commit:** {git log -1 --format='%H %ci'}
**Status:** {✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues}

## Summary
- Files analyzed: {count}
- Lines read: {count}
- Issues: Critical {X}, Warning {Y}, Info {Z}

## Verification
Expected files: {X} | Read: {Y} | Status: {✅/❌}

## 🔴 Critical Issues
{List with location and fix}

## 🟡 Warnings
{List with location and fix}

## 🔵 Info
{Suggestions}

## Integrity Analysis

### Reference Integrity: {✅/⚠️/❌}
{Broken references if any}

### Documentation Completeness: {✅/⚠️/❌}
{Missing sections if any}

### CURRENT.md Consistency: {✅/⚠️/❌}
{Issues if any}

### Schema Consistency: {✅/⚠️/❌}
{Issues if any}

### Security: {✅/⚠️/❌}
{Findings if any}

### Cross-File Consistency: {✅/⚠️/❌}
{Inconsistencies if any}

## Quality Analysis

### Redundancy: {✅/⚠️/❌}
- Redundant lines identified: {count}
- Files with redundancy: {list}

### File Sizes: {✅/⚠️/❌}
- 🔴 >450 lines: {list}
- 🟠 400-450 lines: {list}
- 🟡 350-400 lines: {list}

### Purpose Alignment: {✅/⚠️/❌}
{Misaligned files if any}

### Maintenance Metrics
{Table from 5.4}

### Structure: {✅/⚠️/❌}
{Assessment}

## Auto-Fixable Issues

{If any exist, list with risk level: LOW/MEDIUM/HIGH}

## Recommendations
1. {Priority 1}
2. {Priority 2}
3. {Priority 3}

---
*Next: Fix critical issues, then proceed with /arch-check*
```

---

## Phase 7: Auto-Fix Prompt

If auto-fixable issues exist, ask:

"Found {X} auto-fixable issues. Apply fixes?
- 'all' - All fixes
- 'critical' - Critical only
- 'safe' - LOW risk only
- 'no' - Skip"

**Risk levels:**
- LOW: Update broken references, fix milestone mismatch, update dates
- MEDIUM: Reorder tasks, update status, remove outdated references
- HIGH: Delete files, move files (always show diff, require explicit "yes")

---

## Phase 8: Chat Summary

```
{✅/⚠️/❌} Context Audit Complete

📄 Report: .quality/context/{TIMESTAMP}.md

{If issues:}
🔴 Critical: {count}
🟡 Warnings: {count}
🔵 Info: {count}

{If critical:}
⚠️ Fix critical issues before /arch-check

{If clear:}
✅ Context system healthy. Safe to run /arch-check
```

---

## Critical Rules

1. **NEVER skip Phase 3** - Always verify file count
2. **NEVER use limit/offset** - Read complete files
3. **NEVER hardcode file lists** - Derive from READMEs
4. **Do NOT examine src/** - Documentation only
