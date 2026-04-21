# Submission Pipeline

Submission creation patterns for storing student work.

---

## Overview

The submission pipeline creates submission records and stores student work images. Separate from marking pipeline.

**Key characteristics:**
- Storage-focused (no computation)
- Atomic per submission
- Validation at boundaries
- Context-specific (practice OR paper)

**API workflows:** See `../api/WORKFLOWS.md` for client-server interaction patterns.

---

## Key Decisions

### Separate Pipelines

**Submission and marking are independent pipelines.**

**Why:**
- Submissions persist even if marking fails
- Enables retry without recreating submissions
- Different lifecycles (immediate storage vs flexible marking timing)

### UUID Generation

**Caller generates UUIDs, not repository.**

**Why:**
- Idempotent operations (retry safely with same UUID)
- Predictable R2 naming (name images before upload)
- Frontend control throughout lifecycle
- Repository signatures unchanged M4→M6

### Dual-Path Storage

**Production:** R2 paths (e.g., `submissions/{uuid}_page01.jpg`)
**Evaluation:** Local paths (converted to logical paths)

**Enforcement:**
- Production database rejects local paths
- Eval database accepts both

---

## Submission Contexts

**New in M4:** Submissions belong to exactly ONE context.

### Practice Questions

**Purpose:** Individual question practice with immediate feedback

**Table:** `practice_question_attempts`

**Characteristics:**
- No paper container
- No grading (raw marks only)
- Student controls deletion
- Multiple attempts allowed
- Only `created_at` timestamp (instant workflow)

### Paper Questions

**Purpose:** Full paper submissions with batch marking and grading

**Tables:** `paper_attempts`, `question_attempts`

**Characteristics:**
- Paper attempt groups all questions
- Indicative grade calculated
- Immutable after `completed_at` set
- Retry via inheritance

### Cross-Context Validation

**Rule:** Each submission belongs to exactly ONE context.

**Enforcement:** `submission_contexts.validate_submission_unlinked()` checks both `practice_question_attempts` and `question_attempts` before linking.

**Why:** Different lifecycle rules require clear ownership.

---

## Pipeline Flow

```
Input: SubmissionRequest (uuid, student_id, question_id, image_paths)
    ↓
Validation (student exists, question exists, images accessible)
    ↓
Creation (insert submission, insert images with sequences)
    ↓
Verification (record exists, image count correct, sequences sequential)
    ↓
Commit Transaction
    ↓
Output: submission_id
```

---

## Multi-Image Support

**Use case:** Questions spanning multiple pages

**Storage:** 1-based sequential integers in `submission_images.image_sequence`

**Enforcement:** UNIQUE constraint + sequential validation

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `question_submissions` | Submission records with UUID, student, question, timestamp |
| `submission_images` | Image paths with sequence numbers |
| `practice_question_attempts` | Links submissions to practice context |
| `question_attempts` | Links submissions to paper context |

---

## Module Location

**Location:** `src/paperlab/submissions/`

**Entry point:** `SubmissionCreator.create_submission()`

**See also:** `PAPER-MARKING.md` for full paper workflow.
