# Path Configuration

**Single source of truth:** All data paths are configured in `src/paperlab/config/settings.py`

## Architecture

### Production System (`marking.db`)

**Configuration:**
- `settings.config_path` → `data/config/`
  - Exam configs: `{board}/{level}/{subject}.json` (papers + mark types)
  - LLM models: `llm_models.json` (shared with evaluation)

**Educational Content:**
- `settings.papers_sources_path` → `data/papers/sources/` (PDF originals)
- `settings.papers_structured_path` → `data/papers/structured/` (paper + mark scheme JSONs)
- `settings.papers_diagrams_path` → `data/papers/diagrams/` (extracted diagrams)

**User Data:**
- `settings.students_work_path` → `data/students/work/` (student work images)

### Evaluation System (`evaluation_results.db`)

**Configuration:**
- `settings.evaluation_config_path` → `data/evaluation/config/`
  - Validation types: `validation_types.json` (eval-only)

**Ground Truth:**
- `settings.evaluation_test_cases_path` → `data/evaluation/test_cases/` (test case JSONs)
- `settings.evaluation_test_suites_path` → `data/evaluation/test_suites/` (test suite JSONs)

### Shared Systems

**Database:**
- `settings.db_path` → `data/db/marking.db`
- `settings.schema_path` → `data/db/schema.sql`
- `settings.evaluation_db_path` → `data/db/evaluation_results.db`
- `settings.evaluation_schema_path` → `data/db/evaluation_results_schema.sql`

**Exports:**
- `settings.exports_markdown_path` → `data/exports/markdown/`
- `settings.exports_reports_path` → `data/exports/reports/`

**Prompts:**
- `settings.system_prompt_path` → `prompts/marking/system.md`
- `settings.get_subject_prompt_path(subject)` → `prompts/marking/{subject}.md`

## Usage

```python
from paperlab.config import settings

# All paths are pathlib.Path objects
config_dir = settings.config_path
papers = settings.papers_structured_path
test_cases = settings.evaluation_test_cases_path

# Build file paths
exam_config = settings.config_path / "pearson-edexcel/gcse/mathematics.json"
validation_types = settings.evaluation_config_path / "validation_types.json"
```

## Environment Overrides

All paths support environment variable overrides with `PAPERLAB_` prefix:

```bash
export PAPERLAB_CONFIG_DIR="config/production"
export PAPERLAB_EVALUATION_TEST_CASES_DIR="test_cases/staging"
export PAPERLAB_EXPORTS_MARKDOWN_DIR="output/markdown"
```

## Deployment Environments

### Railway Production

**Volume mount:** `/app/databases` (persistent storage for database files only)

**Environment variables:**
```bash
PAPERLAB_DATABASE_PATH=/app/databases/marking.db  # Override for persistent volume
```

**Architecture:**
- **Git-versioned content** (schemas, configs, JSONs) → `/app/data/` (from git, updates with deployments)
  - Schema files: `/app/data/db/schema.sql`
  - Config files: `/app/data/config/`
  - Paper JSONs: `/app/data/papers/structured/`
  - Evaluation configs: `/app/data/evaluation/config/`

- **Persistent runtime data** (database files) → `/app/databases/` (volume, survives deployments)
  - Database: `/app/databases/marking.db`

**Why separate?** Version-controlled config/schemas must update with git deployments. Database must persist across deployments. Volume mounted at `/app/databases` (not `/app/data`) ensures git content remains accessible while database persists.

**Database initialization:**
```bash
# Via Railway SSH (one-time setup)
railway ssh
PYTHONPATH=/app/src /opt/venv/bin/python -c 'from paperlab.cli.main import main; import sys; sys.argv = ["paperlab", "db", "init"]; main()'
```

### Local Development

**Default paths:** All paths relative to project root (`data/`, `prompts/`, etc.)

**Database location:** `data/db/marking.db` (local development database)

## Key Principles

1. **Zero hardcoded paths** - All paths come from config
2. **Type-safe access** - Properties return `Path` objects
3. **Clear boundaries** - Production vs evaluation clearly separated
4. **Environment configurable** - Override any path via env vars
5. **Self-documenting** - Property names describe purpose
6. **Deployment separation** - Git-versioned content separate from persistent data
