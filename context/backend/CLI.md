# CLI Architecture

Command-line interface structure and design patterns.

---

## Structure

```
cli/
├── main.py              # Entry point with argparse
├── loading_utils.py     # Shared utilities for loader commands
└── commands/            # Command modules
    ├── db.py           # Database operations
    ├── load.py         # Data loading (papers, marks, config)
    ├── eval.py         # Evaluation operations (test cases, suites)
    ├── eval_formatters.py  # Presentation logic for eval commands
    ├── paper.py        # Paper operations (exports)
    ├── submission.py   # Submission operations (create, mark)
    ├── storage.py      # R2 storage operations (presigned URLs, download)
    └── llm.py          # LLM operations
```

**Entry point:** `uv run paperlab <command> <subcommand> [args]`

**Help:** Use `paperlab --help` or `paperlab <command> --help` for detailed usage.

---

## Command Groups

- **`db`** - Database operations (init)
- **`load`** - Data ingestion (papers, marks, config)
- **`eval`** - Evaluation system (test cases, suites)
- **`paper`** - Paper export operations (markdown generation)
- **`storage`** - R2 storage operations (presigned URLs, download)
- **`llm`** - LLM operations (testing, model management)

**Note:** Paper marking and practice question operations are now handled via API endpoints (M6+). See `context/api/README.md` for API usage.

---

## Loader Pattern

**All data loaders follow consistent interface:**

### Flags
- `--replace` - Update existing entity (shows diff, prompts for confirmation)
- `--force` - Skip confirmation prompts (for CI/automation)

### Behavior
1. Parse JSON (Pydantic validation)
2. Check if entity exists (by natural key)
3. **Create mode** (default): Fail if exists with message "Use --replace to update"
4. **Replace mode** (`--replace`):
   - Error if doesn't exist
   - Calculate diff (show what changes)
   - Display changes to user
   - Prompt for confirmation if destructive (unless `--force`)
   - Delete existing entity
   - Create new entity from JSON
5. Verify loaded data
6. Commit transaction

### Natural Keys (identify existing records)
- LLM models: File-level (any models exist)
- Exam configs: `(exam_board, exam_level, subject)`
- Validation types: File-level (any types exist)
- Papers: `exam_identifier`
- Mark schemes: `exam_identifier` (via paper)
- Test cases: `student_work_image_path`
- Test suites: `suite name`

### Design Rationale
- **Consistent UX** - Same flags and workflow across all loaders
- **Safety** - Diffs and confirmations prevent accidental data loss
- **CI-friendly** - `--force` flag enables automation
- **Clear errors** - Guides users to correct flag usage

---

## Shared Utilities

**Location:** `src/paperlab/cli/loading_utils.py`

**Purpose:** Standard error handling and connection management for all loader commands.

**Key utilities:**
- `add_pipeline_args()` - Add standard `--replace` and `--force` arguments
- `check_db_exists()` - Database existence validation with helpful error messages
- `run_loader_command()` - Standard loader execution pattern (DB checks → connections → error handling)

**Benefits:**
- Consistent error handling across all loaders
- Standard database existence checks
- Automatic connection management
- User-friendly error messages

---

## Design Principles

### Single Entry Point
All operational tasks go through CLI. No scattered scripts.

**Rationale:**
- Discoverable (`--help` shows all commands)
- Consistent interface
- Easy to extend
- Professional structure

### Separation of Concerns
CLI commands orchestrate, don't implement.

**Commands should:**
- Parse arguments
- Call domain/data functions
- Format output for users
- Return exit codes (0=success, 1=error)

**Commands should NOT:**
- Contain business logic
- Execute SQL directly
- Duplicate functionality

### User-Friendly Output
Clear, informative messages with visual indicators.

**Conventions:**
- ✓ Success indicators
- ❌ Error indicators
- ⚠️ Warning indicators
- Print errors to stderr
- Return proper exit codes

### Professional Standards
Follow industry CLI patterns (like `git`, `docker`).

**Examples:**
- `command subcommand args` structure
- `--help` for all commands
- `--force` for dangerous operations
- Exit codes (0/1)
- stderr for errors

---

## Startup Validation

**Purpose:** Validate environment configuration before CLI commands execute. Fail-fast for misconfigured environments.

**Implementation:** `src/paperlab/startup.py`

**What gets validated:**
1. Default LLM model exists in database
2. Provider API key is configured in `.env`
3. Database connection is available

**Exception:** Validation skipped for `db` commands (avoid chicken-and-egg: `db init` creates the database that validation needs).

**Error handling:**
- Clear error messages guide user to fix (missing API keys, uninitialized database)
- Returns exit code 1

**Design rationale:**
- Fail fast: Catch config errors before expensive operations
- Clear errors: Guide users to specific fix steps
- Skip when needed: Don't block `db init`

---

## Related Documentation

- **ARCHITECTURE.md** → CLI layer in overall architecture
- **FORMATTING.md** → Output format conventions
