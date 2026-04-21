# Paper Marking

Full paper marking workflow with batch processing, grading, and retry capabilities.

---

## Overview

Paper marking enables students to submit complete exam papers, receive batch marking, and get an indicative grade.

**Core characteristics:**
- Paper attempt is the container (groups all question submissions)
- Immutable after completion (frozen record)
- Status derived from timestamps (no fragile flags)
- Five independent pipelines (composable)
- Inheritance enables cost-effective retries

**See also:** `SUBMISSIONS.md` for submission contexts (practice vs paper).

---

## Five Pipeline Architecture

| Pipeline | Purpose | Output |
|----------|---------|--------|
| **1. Submission** | Create submission, store images | submission_id |
| **2. Linking** | Link submission to paper attempt | question_attempt_id |
| **3. Paper Submit** | Validate completeness, set submitted_at | timestamp |
| **4. Marking** | Mark all submissions (batch) | BatchMarkingResult |
| **5. Grading** | Calculate grade, set completed_at | PaperResult |

**Why five pipelines?** Composable, testable, clear failure boundaries.

---

## Status Derivation

**Status computed from timestamps, not stored:**

| Condition | Status |
|-----------|--------|
| `completed_at` set | complete |
| `submitted_at` set | submitted (marking in progress) |
| Neither set | draft (uploading) |

**Two immutability boundaries:**
- **Photo Lock** (`submitted_at`): Photos cannot be changed
- **Grade Lock** (`completed_at`): Attempt fully frozen

---

## Paper Attempt Lifecycle

### Phase 0: Create Attempt
Creates `paper_attempts` record with NULL timestamps.

### Phase 1: Submit Questions
For each question: Pipeline 1 (submission) + Pipeline 2 (linking).

### Phase 2: Submit Paper
Three-phase commit:
1. Set `submitted_at` (immediate user feedback)
2. Batch mark (parallel, own connections)
3. Calculate grade if all succeeded

### Phase 3: View Results
Query `paper_results` for grade and marks.

---

## Retry Workflow (Inheritance)

**Purpose:** Cost-effective retries without re-marking successful questions.

**Process:**
1. Create new attempt with `--inherit-from <previous_id>`
2. System copies latest submissions from source
3. Student overrides specific questions with new photos
4. Marking skips inherited questions with existing marks
5. On completion, source attempt soft-deleted

**Why:** Only new/overridden questions cost API calls.

---

## Validation Rules

### Pre-Submission (Pipeline 3)
1. All questions have latest submissions
2. Paper not already complete
3. At least one non-inherited submission (no "zero-effort retry")

### Pre-Grading (Pipeline 5)
1. All questions marked successfully
2. Paper not already graded

---

## Three-Phase Commit Pattern

**Why three separate transactions?**

| Phase | What | Why Separate |
|-------|------|--------------|
| **1** | Set submitted_at | User sees "marking in progress" even if marking fails |
| **2** | Batch mark | Don't lose expensive marking results if grading fails |
| **3** | Grade + complete | Can retry grading without re-marking |

**Retry scenarios:**
- Marking fails → Retry skips successful questions
- Grading fails → Retry without re-marking
- All succeeded → Attempt immutable

---

## Edge Cases

| Scenario | Solution |
|----------|----------|
| Re-upload before submit (draft) | Allowed - new submission, latest by timestamp |
| Re-upload after submit | Blocked - create retry with inheritance |
| Retry after marking failure | Same attempt - idempotent marking |
| Fix photos after completion | New attempt with inheritance |

---

## Grade Boundaries

Loaded from paper JSON into `grade_boundaries` table.

**Calculation:** Find highest grade where `raw_marks >= min_raw_marks`.

**Auto-add:** System appends "U" grade with `min_raw_marks = 0`.

---

## Related Docs

- `MARKING.md` - Marking pipeline details
- `SUBMISSIONS.md` - Submission creation and contexts
- `ARCHITECTURE.md` - System architecture
