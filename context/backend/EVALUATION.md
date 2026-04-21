# Evaluation Framework

System for validating automated marking quality, comparing models, and detecting regressions.

---

## Purpose

Validate marking accuracy before scaling to production:
- Quality validation (is marking accurate enough?)
- Model comparison (Claude vs GPT-4o)
- Regression detection (do prompt changes help or hurt?)
- Debugging (what prompt/response caused failure?)
- Longitudinal tracking (is quality stable over time?)

---

## Three-Database Architecture

| Database | Purpose | Lifecycle |
|----------|---------|-----------|
| `marking.db` | Source of truth for test questions | Permanent, read-only during tests |
| `test_execution.db` | Receives injected connection for marking | Ephemeral, deleted after extraction |
| `evaluation_results.db` | Stores test results for analysis | Permanent, never wiped |

### Key Principle

**Tests execute production code path** - Same `QuestionMarker`, same repositories, same formatters. Only difference: which database connection is injected.

**Why:** Validates actual production behavior, not test-specific logic.

---

## Ground Truth

### Test Cases

Individual question + student work + expected marks.

**Content:**
- Paper identifier and question number
- Student work image path(s)
- Validation type (sanity, nuanced, edge case)
- Expected marks per criterion index

**Path conventions:** `data/evaluation/test_cases/{board}/{level}/{subject}/{paper_code}/q{NN}_{type}_{NNN}.json`

### Test Suites

Curated collections of test cases for regression testing.

**Features:**
- Named collections (e.g., "GCSE Maths Baseline")
- References test cases by JSON path
- Diff calculation on updates
- Interactive confirmation on removals

---

## Test Execution Flow

```
1. Setup: Create test_execution.db from current schema
2. Load: Questions and mark schemes into test DB
3. Submit: Create submission records (uses production SubmissionCreator)
4. Mark: Batch mark with production BatchMarker
5. Extract: Results to evaluation_results.db
6. Verify: All artifacts extracted
7. Cleanup: Delete test_execution.db
```

**Separate pipelines:** Submission and marking are independent (same as production).

---

## Disaster Recovery

**Cost protection:** LLM calls are expensive (~$0.10-0.50 per question).

**Recovery points:**
- Submissions created BEFORE marking (survive marking failures)
- Test DB preserved on extraction failure
- Idempotent retry reuses existing submissions
- All-or-nothing extraction with rollback

**Correlation strategy:** Maps (question_id, test_case_id, first_image_path) to correlate submissions → attempts → results.

---

## Storage Philosophy

**Store raw artifacts, not database structure:**
- Prompts and responses as text
- Metadata as simple fields
- No mirroring of production schema

**Why:** Decouples test results from schema evolution. No migration nightmare.

---

## Migration Strategy

**When production schema changes:**

1. Change production schema
2. Update Python query logic
3. Re-run test suite:
   - Creates `test_execution.db` with NEW schema
   - Marks with production code (works with new schema)
   - Extracts to `evaluation_results.db` (unchanged)
4. Old test results remain queryable

**Key:** Test results store natural keys (paper_identifier, question_number, criterion_index), not database IDs.

---

## Schema Overview

**Ground truth tables:**
- `validation_types` - Test case categories
- `test_cases` - Student answers with expected marks
- `test_case_marks` - Ground truth per criterion
- `test_suites` / `test_suite_cases` - Named collections

**Test results tables:**
- `test_runs` - Execution metadata (model, timestamp, git commit)
- `test_question_executions` - Prompts, responses, tokens, timing
- `test_criterion_results` - Predicted marks per criterion

**See:** `schema/evaluation-schema.md` for complete schema.

---

## Analysis & Metrics (Future)

**Calculated on-demand by joining databases:**

- Exact match rate (whole question correct)
- Criterion-level accuracy
- Per-mark-type breakdown
- Error analysis (false positives/negatives)
- Model comparison (side-by-side results)
- Cost and timing (tokens × pricing)
- Confidence calibration

**Re-analysis capability:** Improve parsing/metrics without re-running API calls (raw responses stored).

---

## Module Location

**Location:** `src/paperlab/evaluation/`

**Key modules:**
- `test_case_loader.py` / `test_suite_loader.py` - Ground truth loading
- `test_executor.py` - Orchestrator
- `artifact_extractor.py` - Results extraction
- `sanity_case_generator.py` - Test case generation
