# Backend Context

Strategic context for Python backend architecture, CLI, database, and domain logic.

## When to Use This

- **Understanding backend architecture** → `ARCHITECTURE.md`
- **Using the command-line interface** → `CLI.md`
- **Working with data ingestion** → `DATA-LOADING.md`
- **Working with markdown generation** → `FORMATTING.md`
- **Working with submission creation** → `SUBMISSIONS.md`
- **Working with storage (R2, staging, presigned URLs)** → `STORAGE.md`
- **Working with question marking** → `MARKING.md`
- **Working with paper marking** → `PAPER-MARKING.md` (full paper workflow, grading, retries)
- **Marking quality validation** → `EVALUATION.md` (ground truth loading, test execution, metrics)
- **Code testing strategy** → `TESTING.md`
- **Database connection management** → `DATABASE.md`
- **Database schema reference** → `schema/`
- **Repository patterns** → `REPOSITORIES.md` (soft delete, restore, error handling)
- **Path configuration** → `PATH-CONFIGURATION.md`
- **Rate limits and API management** → `RATE_LIMITS.md`

## Cross-Cutting Concerns

For shared information across backend and frontend:
- **JSON format specification** → `../shared/JSON-FORMATS.md`
- **Domain concepts (mark schemes)** → `../shared/DESIGN.md`
- **Product vision and roadmap** → `../shared/MISSION.md` and `../shared/ROADMAP.md`

## Principles (CRITICAL - Must Follow)

- **DRY** - One source of truth per piece of information
- **Separation of concerns** - Each file has distinct purpose
- **Assume intelligence** - Self-documenting structure over verbose explanation
- **Minimum required context** - Provide orientation, not exhaustive detail
- **Top-level only** - High-level guidance, not deep detail

## Structure

- **ARCHITECTURE.md** - Directory structure, layered architecture, core patterns, responsibility boundaries
- **CLI.md** - Command-line interface structure, commands, usage patterns
- **DATA-LOADING.md** - JSON→SQL ingestion, validation strategy, transaction management
- **FORMATTING.md** - Output format conventions, presentation patterns, markdown standards
- **SUBMISSIONS.md** - Submission creation pipeline, attempt lifecycle, draft/retry/soft-delete patterns
- **STORAGE.md** - R2 storage architecture, two-bucket pattern, presigned URLs, copy-on-edit strategy
- **MARKING.md** - Question marking pipeline, validation layers, prompt assembly, parsing strategies
- **PAPER-MARKING.md** - Full paper marking workflow, grading scale, retry logic, orchestration
- **EVALUATION.md** - Marking quality validation, test execution, ground truth loading, metrics
- **TESTING.md** - Code testing strategy (unit/integration tests)
- **DATABASE.md** - SQLite strategy, connection management, transaction lifecycle, db init command
- **REPOSITORIES.md** - Repository patterns (soft delete, restore, ValueError handling, filtering)
- **PATH-CONFIGURATION.md** - Directory paths, config properties, environment overrides
- **RATE_LIMITS.md** - API rate limiting, provider management, retry strategies
- **schema/** - Database schema reference (production + evaluation databases)

## Implementation Guidance

**Looking for detailed specs?** See `specs/` folder at project root.

**This folder is for strategic context only.** Implementation details (class structures, method signatures, validation rules) live in:
- `specs/` - Pre-implementation guidance (delete after code exists)
- `src/` - Post-implementation (code is truth)

## Maintaining This System

**Before modifying documentation:**
1. Verify you're updating the single source of truth (check for duplicates)
2. Keep content high-level - detailed specs belong in `specs/` or code
3. Each file should have one clear purpose
4. Assume the reader is intelligent - minimal explanation, maximum clarity

**Adding new documentation:**
- Strategic content goes in `../shared/VISION.md` (rarely changes)
- Technical patterns go in relevant file here
- Data model context goes in `schema/`
- Implementation specs go in `specs/` at project root (not here)
