# PaperLab

Automated past paper marking tool with working analysis for UK exams.

## Scope

**GCSE Maths (Pearson Edexcel)** — validated automated marking to 98% accuracy.

**Foundational Constraints:**
- **Multi-subject/multi-level architecture** - Support rapid expansion to other subjects and levels without refactors
- **Question-level foundation** - Questions are the fundamental unit of analysis
- **Subject-agnostic design** - Core logic identical for all subjects/levels. Subject differences live in data, not code
- **Expand through data, not code** - New boards/subjects/levels add config/data, never conditionals

## Data Standards

**Mathematical expressions:** Use LaTeX with `$...$` (inline) or `$$...$$` (display) in all text fields. Works with LLMs, UI renderers (KaTeX), and markdown.

Example: `"Find $\frac{dy}{dx}$ when $y = x^2 + 5x$"`

## Software Principles

### Universal Principles (apply to ALL code)
- **Simplicity over cleverness** - Obvious code. Refactor early
- **Extreme modularity** - Each module has one reason to change
- **DRY** - No duplicated strings, magic numbers, or logic. Use constants/config. If you copy-paste, extract it
- **Fail fast** - Validate at boundaries
- **Separation of concerns** - Presentation layers separate from domain logic
- **Composition over inheritance** - Build from small, focused components

### Architecture Patterns
- **Layered architecture** - Clear separation: CLI/API → Domain Logic → Repository → Database
- **Backend owns business logic** - All domain logic lives in backend. API and frontend are thin transport/UI layers
- **Repository pattern** - All data access in repository classes. Domain logic never accesses data directly
- **Immutable state** - Prefer final fields, use copyWith() for updates

## Domain-Specific Principles

**When working in these areas, consult the relevant context file:**

**Frontend (Flutter):** → `context/frontend/ARCHITECTURE.md`
- Widget composition patterns, const constructors, BuildContext handling, state management

**API (FastAPI):** → `context/api/README.md`
- API is transport, from_domain() pattern, transaction management, validation layers, resource-oriented endpoints

**Backend (Python):** → `context/backend/ARCHITECTURE.md`
- Connection management (Pattern A), transaction patterns, repository patterns, LLM provider abstraction

**Landing Page (Next.js):** → `context/landing/README.md`
- Marketing site, design system connection, section components, content source files

## Development Workflow

### Critical Workflow Rules (MUST follow every time)
- **Always use `PYTHONPATH=src uv run`** - For all Python scripts/CLI commands
- **Always use `fvm flutter`** - For all Flutter commands (not `flutter`)
- **Production by default** - App uses Railway backend. For local backend: `fvm flutter run --dart-define=ENVIRONMENT=development`
- **Always run analysis** - `fvm dart analyze` after editing Dart code
- **Always run pre-commit** - `uv run pre-commit run --all-files` after writing code
- **Never commit** - Commits are ALWAYS managed by the user (no exceptions)

### Quality Checklist (before handing back control)
1. ✓ No string literals used more than once? (extract to constants)
2. ✓ No magic numbers? (extract to named constants)
3. ✓ Each function/widget has one clear purpose?
4. ✓ Adding new subject/level would require code changes? (if yes, extract to config)
5. ✓ New/updated context docs? (follow `context/GOVERNANCE.md` - <450 lines, WHY/WHERE not WHAT/HOW)
7. ✓ Analysis passes? (Dart: `fvm dart analyze`, Python: pre-commit)

### Refactoring Guidelines
- **Delete first** - Remove, then combine, then create
- **Break fearlessly** - No backwards compatibility. Delete old interfaces

## Search Strategy

1. **Start with context** - Always search `/context` first, starting with `README.md` as entry point
2. **Read code files** - Only when context doesn't answer the question OR you need detailed implementation specifics
3. **Ask for clarification** - If less than 80% confidence in understanding, ask before searching
4. **Avoid Task/Explore** - Only use when explicitly requested by user

## Documentation

**`context/`** - Strategic decisions and architecture (planning)
  - **See `context/GOVERNANCE.md` for contribution guidelines when updating context**
  - `backend/` - Python backend context
  - `api/` - FastAPI layer context
  - `frontend/` - Flutter frontend context
  - `landing/` - Next.js marketing site context
  - `shared/` - Cross-cutting context
    - `MISSION.md` - Identity (why we exist, values, who we serve)
    - `ROADMAP.md` - Strategy (what we built, what was planned)
    - `BRANDING.md` - Expression (how we communicate)
    - Domain models, API design, etc.

## Navigation

- **Code** → `src/`
- **Data** → `data/`
- **Analysis** → `analysis/`
- **Database** → `data/db/marking.db` (init via `PYTHONPATH=src uv run paperlab db init`)
- **CLI** → `PYTHONPATH=src uv run paperlab`
- **Landing Page** → `landing/` (Next.js marketing site)

## MCP Servers

- **flutter-docs** - Flutter/Dart documentation and pub.dev packages

**When to use:** Use `flutter_docs()` or `flutter_search()` when encountering unfamiliar Flutter/Dart APIs, widgets, or pub.dev packages. Prioritize this over web search for Flutter/Dart questions. User is new to Flutter/Dart, so use liberally.

