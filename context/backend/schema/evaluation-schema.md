# Evaluation Results Schema

Database schema for `evaluation_results.db` - permanent storage of test results and ground truth.

**Schema file:** `data/db/evaluation_results_schema.sql`

---

## Design Principles

1. **Store raw artifacts, not database structure** - Prompts and responses as text, not full DB mirror
2. **Independent from production schema** - No foreign keys to `marking.db`, connection via Python
3. **Natural keys for stability** - `paper_identifier + question_number + criterion_index` are stable
4. **Criterion-level granularity** - Store marks, feedback, confidence per criterion for detailed analysis
5. **No aggregated metrics** - All calculated on-demand from raw data

---

## Ground Truth Tables

**Complete DDL:** See `data/db/evaluation_results_schema.sql`

### validation_types

Categorize test cases by validation goal (e.g., `mark_scheme_sanity`, `nuanced_marking`).

### test_cases

Individual student answers with ground truth marks.

**Natural key:** `test_case_json_path` (unique, stable across refactors)

**Multiple test cases per question:** Different student work with different expected marks and validation purposes.

### test_case_images

Multi-image support for questions spanning multiple pages.

**Design decisions:**
- `image_sequence`: Ordering (1, 2, 3...) for page progression
- Unique constraint on `image_path`: First image path identifies test case during correlation
- Enables questions requiring multiple pages without breaking conventions

### test_suites

Named collections of test cases for regression testing.

### test_suite_cases

Many-to-many junction: test cases can belong to multiple suites.

### test_case_marks

Ground truth marks for each criterion.

**criterion_index:** Logical position (0, 1, 2...) matching production `mark_criteria.criterion_index`. Stable across runs.

---

## Test Results Tables

**Complete DDL:** See `data/db/evaluation_results_schema.sql`

### test_runs

Metadata for each test execution.

**Model tracking:**
- `model_identifier`: Stored as text (not FK) for standalone queryability
- Evaluation DB remains self-contained archive even if production schema changes
- Text storage (~25 bytes) negligible vs benefits (no ATTACH needed, long-term readability)

**Enables:** Reproducibility, comparison over time, model drift detection

### test_question_executions

Raw artifacts per test case execution.

**Why store prompts + raw response:**
- Debug failures months later
- Re-parse with improved logic (no re-running API calls)
- Analyze prompt changes over time

**Why tokens not cost:**
- Pricing changes over time
- Calculate cost on-demand with current pricing

### test_criterion_results

Predicted marks per criterion with LLM reasoning.

**Mirrors production schema:** Same fields as `question_marking_results` for consistent analysis patterns.

**Enables:**
- Direct SQL queries on feedback and confidence (no JSON parsing)
- Pattern detection (grep feedback for common LLM mistakes)
- Confidence calibration analysis (high-confidence more accurate?)

---

## Indexes

**Complete index definitions:** See `data/db/evaluation_results_schema.sql`

**Index patterns:**
- All foreign keys indexed for JOIN performance
- Composite indexes on natural keys (paper_identifier, question_number)
- Temporal indexes on run_timestamp for time-based queries
- Model and git commit indexes for filtering test runs

---

## Natural Keys & Cross-Database Queries

### No SQL Foreign Keys to Production

Connection via Python joins using natural keys:
- `paper_identifier` (TEXT)
- `question_number` (INTEGER)
- `criterion_index` (INTEGER)

### Analysis Pattern

1. Query `evaluation_results.db` for raw results
2. Query `marking.db` for metadata (mark types, diagrams, descriptions)
3. Join in Python using natural keys
4. Calculate and display metrics

**Example:** Per-mark-type accuracy
```python
# Query evaluation results
results = eval_db.query("SELECT criterion_index, marks_awarded_predicted FROM test_criterion_results...")

# Query production DB for mark types
criteria = prod_db.query("SELECT criterion_index, mark_type FROM mark_criteria WHERE paper_identifier = ? AND question_number = ?", ...)

# Join in Python
joined = merge(results, criteria, on='criterion_index')

# Calculate accuracy by mark type
accuracy_by_type = joined.groupby('mark_type').apply(...)
```

---

## Migration Strategy

### When Production Schema Changes

**Problem:** Production evolves. How do test results remain queryable?

**Solution:** Python query layer adapts. No database migrations needed.

**Why this works:**
- Natural keys are stable (paper identifiers, question numbers, criterion indices don't change)
- Test results store only text and references
- Schema knowledge lives in Python queries, not database structure
- Test results schema never changes (just stores text and simple fields)

**Process:**
1. Change production schema (e.g., add new fields to `mark_criteria`)
2. Update Python query logic to match new schema
3. Old test results remain queryable with new Python code
4. Re-run test suite creates new results with current schema
