# Database Setup

Database strategy and approach.

---

## Strategy

**SQLite for MVP:**
- Zero setup overhead
- Fast iteration (delete file to reset)
- Easy to migrate to Postgres later (SQLAlchemy abstracts differences)

**Structure:**
```
paperlab/
├── data/
│   └── db/
│       ├── marking.db                      # Gitignored, production runtime data
│       ├── evaluation_results.db           # Gitignored, test ground truth
│       ├── schema.sql                      # Committed, production table definitions
│       └── evaluation_results_schema.sql   # Committed, evaluation table definitions
└── src/paperlab/data/
    └── repositories/
        ├── marking/                        # marking.db repositories
        └── evaluation/                     # evaluation_results.db repositories
```

---

## Database Files

### Production Database (`marking.db`)
**schema.sql** - Production table definitions and indexes
**marking.db** - Runtime production data (papers, questions, marking results) - gitignored

### Evaluation Database (`evaluation_results.db`)
**evaluation_results_schema.sql** - Test framework table definitions
**evaluation_results.db** - Test cases, suites, and execution results - gitignored

### Execution Database (`test_execution.db`)
**Ephemeral** - Created fresh per test run, deleted after artifact extraction
**Schema** - Uses production schema.sql (identical to marking.db)

---

## Initialize Database

**Command:** `PYTHONPATH=src uv run paperlab db init`

**What it does:** Creates database from schema, loads config data (exam types, mark types, LLM models), creates test students (IDs 1-50), loads sample papers. Supports `--backup` flag.

**See:** `src/paperlab/cli/commands/db.py` and `paperlab db init --help` for full options.

---

## Connection Management

**Pattern:** Context manager for guaranteed cleanup.

**Key principles:**
- **One connection per transaction** - Entire operation uses single connection
- **Context manager required** - Prevents connection leaks
- **CLI owns complete transaction lifecycle** - Only CLI layer commits/rollbacks, never orchestrators or repositories
- **Connection passed as parameter** - Repositories receive connection, never create it
- **Batch operation exception** - Parallel thread pools require per-thread connections (see below)

**Transaction Lifecycle Responsibility:**
```
CLI Layer:          Opens → Commits/Rollbacks → Closes
Orchestrators:      Receive → Execute → Return (NO transaction control)
Repositories:       Receive → Query → Return (NO transaction control)
Batch Orchestrators: May receive conn for query phase, then delegate to
                    BatchMarker which creates per-thread connections for writes
```

**Batch Operation Exception:**

Thread pools (like `BatchMarker`) **must** create per-thread connections due to SQLite threading constraints. Query phase uses CLI-provided connection; marking phase creates per-thread connections.

**See:** `src/paperlab/paper_marking/marking.py` for implementation.

**Why this exception is safe:**
- Query phase uses CLI-provided connection (consistent with single-transaction pattern)
- Marking phase requires parallelism (SQLite cannot share connections across threads)
- BatchMarker creates independent per-thread connections for writes
- No cross-transaction consistency issues (each marking is independent)

**Why this matters:**
- Prevents abandoned connections holding locks
- Ensures transactions are atomic (all-or-nothing)
- Enables validation of staged changes before commit
- Predictable cleanup via `finally` block
- CLI controls transaction boundaries (enables composition)
- Single source of truth for transaction decisions
- Orchestrators become pure business logic (easily testable)
- Batch operations can leverage parallelism without compromising safety

See `src/paperlab/data/database.py` for implementation.

---

## ATTACH/DETACH Protocol (SQLite)

**When merging databases for bulk operations:**

**Protocol:**
1. **Close existing connections** to database being attached (SQLite restriction)
2. **ATTACH** database with alias
3. **Execute queries** spanning both databases
4. **COMMIT before DETACH** (critical - uncommitted transactions prevent DETACH)
5. **DETACH** to release locks

**See:** `src/paperlab/evaluation/execution/artifact_extractor.py` for implementation.

**Common errors:**
- "database is locked" → Connection still open to attached DB
- "database test_exec is locked" → Uncommitted transaction during DETACH

---

## Transaction Lifecycle

**Repositories:** Execute SQL, never commit. Return results, no transaction control.

**Orchestrators (Loaders, Markers):** Coordinate operations, never commit. No try/except, just raise on error.

**CLI Commands:** Control transaction boundaries
- Standard pattern: commit on success, rollback on error
- Special case: MarkingError commits for observability (preserves diagnostic data)

**See:** `src/paperlab/cli/commands/` for CLI transaction patterns, `src/paperlab/data/repositories/` for repository implementations.

## Repository Organization

Repositories are organized by database to clarify which database each repository targets:

**Marking repositories** (`src/paperlab/data/repositories/marking/`):
- Target: `marking.db`
- Modules: `papers`, `questions`, `mark_criteria`, `exam_types`, `mark_types`, `llm_models`, `question_submissions`, `submission_images`, `marking_attempts`, `question_marking_results`, etc.

**Evaluation repositories** (`src/paperlab/data/repositories/evaluation/`):
- Target: `evaluation_results.db`
- Modules: `test_cases`, `test_case_marks`, `test_suites` (future), `test_suite_cases` (future)

**Import pattern:**
```python
# Explicit imports (recommended)
from paperlab.data.repositories.marking import papers, questions
from paperlab.data.repositories.evaluation import test_cases
```

**Staged changes are queryable:**
- Your connection sees uncommitted changes immediately
- Other connections see only committed data
- Enables validation before commit
- SQLite manages isolation automatically via WAL

---

## Migration to Postgres

When deploying or hitting scale limits:

1. Change connection string: `sqlite:///marking.db` → `postgresql://...`
2. Update 2-3 SQL syntax differences (AUTOINCREMENT → SERIAL)
3. Update context manager to use connection pooling
4. Transaction patterns remain identical

**Timeline:** When deploying or >100k records
