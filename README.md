# PaperLab

AI-powered marking for UK GCSE past papers. Students photograph handwritten work, and the system marks against official mark schemes criterion-by-criterion, returning scores and detailed feedback.

Built as a solo project in 2025. The product reached 100 users and validated 98% marking accuracy on backtested evaluations, but was ultimately blocked by exam board IP licensing — the mark scheme content couldn't be commercially licensed. The code remains a complete, production-grade system.

## Architecture

**Monorepo:** Python backend (FastAPI) + Flutter frontend (iOS/Android/Web) + Next.js landing page.

### Backend (`src/paperlab/`)

```
src/paperlab/
├── api/            # FastAPI transport layer (thin — no business logic)
├── marking/        # Core marking pipeline
│   ├── prompt_builder.py   # Assembles MarkingRequest (frozen dataclass)
│   ├── marker.py           # Orchestrates: validate → load images → build request → call LLM → parse → store
│   └── exceptions.py       # Typed error hierarchy
├── services/       # External API clients
│   ├── llm_client.py       # Protocol + base class (retry, backoff, image validation)
│   ├── claude_client.py    # Anthropic — embeds JSON examples in prompt
│   └── openai_client.py    # OpenAI — uses structured output with JSON schema
├── evaluation/     # Accuracy backtesting framework
│   ├── execution/  # Ephemeral SQLite per test run, parallel marking
│   ├── loading/    # Strategic test data loading
│   └── services/   # Bulk extraction via SQLite ATTACH, git commit tracking
├── data/           # Repository layer (functional — connection passed, no ORM)
├── loading/        # Data ingestion with diff calculators and validators
├── submissions/    # Two-phase submit → mark workflow
├── config/         # pydantic-settings with format validators
└── constants/      # Typed Finals, centralised error messages
```

### Key design decisions

**Provider-agnostic marking pipeline.** `PromptBuilder` assembles requests with zero knowledge of any LLM. `LLMClient` is a Protocol — Claude and OpenAI each own their formatting strategy (Claude embeds JSON examples in prompt text; OpenAI generates a JSON schema for structured output). Shared base class handles retry with exponential backoff and jitter, image URL validation with domain whitelisting, and response validation.

**Three-layer validation.** Pydantic models (types and constraints) → business validators (cross-validation against mark scheme) → database constraints. Failed attempts are stored with full context (raw response, prompts, timing) for debugging.

**Evaluation framework.** Each test run creates an ephemeral SQLite database, marks against ground-truth test cases with parallel execution, then bulk-extracts results into the persistent database using `ATTACH DATABASE`. Git commit hash is pinned per run for reproducibility. The ephemeral database is preserved on failure — LLM results are expensive and never discarded without confirmed extraction.

**Two-phase marking.** Submissions are created first (no API cost), then marked separately. This supports batch marking, model comparison, and re-marking with updated prompts without re-uploading images.

### Frontend (`lib/`)

Flutter app with Riverpod state management, Supabase auth (Apple/Google/Email), and a repository pattern over Dio. The frontend is functional and shipped to the App Store — it was built for speed, not as a frontend showcase.

## Setup

### Prerequisites

- **Python 3.11+** via [uv](https://github.com/astral-sh/uv)
- **Flutter 3.35+** via [fvm](https://fvm.app/) (for frontend development)

### Backend

```bash
uv sync
cp .env.example .env
# Add API keys to .env (see .env.example for required variables)
uv run paperlab db init
uv run paperlab llm test --all
```

### Frontend

```bash
dart pub global activate fvm
fvm use 3.35.7 --force
fvm flutter pub get
```

### Quality checks

```bash
uv run pre-commit run --all-files   # Linting (ruff, mypy)
uv run pytest                        # Tests
fvm dart analyze                     # Dart analysis
```

## Context files

The `context/` directory and `CLAUDE.md` contain architecture documentation used during development with Claude Code. They describe the system's design principles, patterns, and conventions in detail — useful for understanding the codebase.
