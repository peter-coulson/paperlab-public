# Architecture

High-level code structure and design patterns.

---

## Layered Architecture

```
CLI Layer (cli/)
    ↓ calls
Domain Logic Layer (loading/, evaluation/, submissions/, marking/)
    ↓ uses
Shared Infrastructure (loaders/)
    ↓ calls
Repository Layer (data/repositories/)
    ↓ executes SQL
Database
```

**Dependency rule:** Each layer only depends on the layer below. Domain logic has zero SQL.

**Key modules:**
- **CLI** - Entry point, argument parsing, transaction management, user output
- **Submissions** - Submission creation pipeline (user action, immediate)
- **Marking** - Marking pipeline (computation, flexible timing)
- **Loading** - Paper/mark scheme data ingestion (JSON → database)
- **Evaluation** - Test quality validation framework
- **Loaders** - Shared infrastructure for all data loading operations
- **Markdown** - Cross-cutting markdown generation for prompts and exports

---

## Core Patterns

### Connection Management (Pattern A)

**Principle:** CLI layer owns complete transaction lifecycle.

```
CLI Layer:          Opens → Commits/Rollbacks → Closes
Orchestrators:      Receive → Execute → Return (NO transaction control)
Repositories:       Receive → Query → Return (NO transaction control)
```

**Why:**
- Clear separation of infrastructure (connections) from business logic
- Single source of truth for transaction decisions
- Explicit transaction boundaries visible at call site
- Orchestrators become pure business logic (easily testable)

**Rules:**
1. **CLI** - Opens connections, ALWAYS handles commit/rollback
2. **Orchestrators** - NEVER call commit() or rollback(), just raise exceptions
3. **Repositories** - Execute SQL only, no transaction management

**Exceptions:**
- `BatchMarker` - Creates one connection per worker thread (thread safety)
- Evaluation module - Manages transactions internally (SQLite ATTACH constraints)

### Separate Pipeline Pattern

Submission and marking are separate pipelines with independent transaction boundaries.

**Why:**
- **Different lifecycles** - Submissions immediate, marking flexible timing
- **Cost protection** - Submissions persist even if marking fails
- **Flexibility** - Mark immediately, batch, or during off-peak hours

### Repository Pattern

**Why:** Isolates all SQL in data access layer. Domain logic never executes queries.

**Structure:** One repository per table with explicit methods.

**Dependency constraints:**
- MUST import: `sqlite3`, `typing`, `dataclasses`
- MAY import: `ErrorMessages`, `fields` constants
- MUST NOT import: Business logic modules

### UUID Generation

**Principle:** Caller generates UUIDs, not repositories.

**Why:**
- Idempotent operations (retry safely with same UUID)
- Predictable R2 naming (name images before API call)
- Frontend control throughout lifecycle
- No M6 refactoring (repository signatures unchanged)

---

## Responsibility Boundaries

| Layer | Owns | Never |
|-------|------|-------|
| **CLI** | User interface, command routing, output formatting | Business logic, direct SQL |
| **Loading** | JSON parsing, validation, insertion orchestration | Domain logic, SQL |
| **Markdown** | Markdown generation for human/LLM consumption | Business logic, data access |
| **Marking** | Business rules, orchestration, validation logic | SQL, direct API calls |
| **Repositories** | SQL queries, data validation | Business logic, LLM calls |
| **Services** | LLM API integration, provider abstraction | Business logic, data access |

---

## Domain Objects vs Pydantic Models

**Domain objects (dataclasses):** Internal representation throughout application.

**Pydantic models:** External data validation at system boundaries only.
- `marking/models.py` - LLM response validation
- `loading/models/*.py` - JSON input validation

**Why separate?** Different concerns, different reasons to change.

---

## Subject-Agnostic Design

**Principle:** Core logic identical for all subjects and levels.

**How subject differences are handled:**
- Mark types stored in `mark_types` table
- Subject-to-abbreviations mapping in `config/constants.py`
- Same repositories, same marker, same data flow

**Adding new subject:** No code changes to business logic - only reference data (`mark_types`), config mapping (`SUBJECT_ABBREVIATIONS`), and abbreviations template.

---

## LLM Provider Abstraction

**Principle:** Support multiple providers without changing business logic.

**Implementation:** Protocol-based interface + factory pattern + provider-agnostic request model.

### Architecture

**Three-layer separation:**
```
PromptBuilder (domain)
    ↓ builds
MarkingRequest (value object - provider-agnostic)
    ↓ passed to
LLM Client (service) - resizes images, encodes, formats for API
    ↓ calls
Provider API (Claude, OpenAI, etc.)
```

**Key insight:** Separate WHAT to mark (data) from HOW to format it (API-specific).

**Image preprocessing:** Base client resizes images to 512px before encoding (99% accuracy, 87% smaller payloads). See `MARKING.md` for rationale.

### MarkingRequest Domain Object

**Immutable value object** containing all data needed for marking:
- `system_instructions` - Role, principles, constraints (from `system_base.md`)
- `abbreviations` - Mark scheme codes (from `maths_abbreviations.md`)
- `question_content` - Question and mark scheme (interleaved format)
- `expected_structure` - Criterion IDs and marks for validation

**Why domain object:**
- Provider-agnostic - no Claude/OpenAI knowledge
- Immutable - value semantics prevent accidental mutation
- Single source of data - passed through entire pipeline
- Testability - pure data, no behavior

**Location:** `marking/models.py`

### Prompt Management

**Single source of truth:** Base templates shared across all providers in `prompts/marking/`.

**No provider-specific templates.** Each client adds its format requirements programmatically.

**Why single source:**
- DRY - no duplication of instructions
- Consistency - all providers mark the same way
- Maintainability - update once, applies everywhere
- Extensibility - new subjects add one abbreviations file

### Client-Side Formatting

**Principle:** Each LLM client owns its formatting strategy.

**Current providers:**

| Provider | Format Strategy | Implementation |
|----------|----------------|----------------|
| **Claude** | Embeds JSON example in user prompt | `ClaudeClient._format_user_prompt()` adds structure |
| **OpenAI** | Uses `response_format` param with JSON Schema | `OpenAIClient._generate_json_schema()` builds schema |
| **Google Gemini** | OpenAI-compatible API via `base_url` param | Reuses `OpenAIClient` with custom base URL |

**OpenAI-compatible providers:** Some providers (e.g., Gemini) offer OpenAI-compatible APIs. These reuse `OpenAIClient` with a custom `base_url` parameter, avoiding code duplication while maintaining correct `provider_name` for logging.

**Why client-side:**
- Separation of concerns - PromptBuilder assembles data, clients format
- Provider flexibility - each optimizes for its API
- No conditionals - client knows its own requirements
- Maintainability - provider changes stay in provider code

### OpenAI Structured Outputs

**Feature:** JSON Schema passed via `response_format` parameter guarantees valid JSON.

**Benefits:**
- 100% schema compliance (constrained decoding)
- No markdown wrappers (pure JSON)
- 400-600 token reduction per request (no JSON example needed in prompt)
- Forces JSON even on edge cases (returns 0 marks with explanation)

**Implementation:**
- Schema generated from `expected_structure` (no duplicate data fetching)
- Schema cached by OpenAI per question (efficient for repeated marking)
- Falls back to `json_object` mode if schema generation fails

### Adding New Provider

**Requires:** Implement client class with `mark_question()` method, add to factory dict, add API key to Settings, add models to database.

**No changes needed:** PromptBuilder, Marker orchestrator, business logic (provider abstraction maintained).

**See:** `services/openai_client.py` or `services/claude_client.py` for implementation pattern.

---

## Cloud Storage Architecture

**Dual-path storage:** Local filesystem (eval) and R2 cloud storage (production).

| Context | Storage | Path Format |
|---------|---------|-------------|
| Production | Cloudflare R2 | `submissions/{uuid}_page{NN}.{ext}` |
| Evaluation | Local filesystem | `data/evaluation/test_cases/...` |

**Key decisions:**
- Production database rejects local paths (prevents data leakage)
- Eval database accepts both (testing flexibility)
- Presigned URLs enable direct R2→LLM fetching (no backend bandwidth)
- 24-hour URL expiry handles batch marking + retries

---

## Error Handling Strategy

- **Fail fast:** Validate at boundaries
- **Specific exceptions:** Each layer raises appropriate type
- **Context in messages:** Include IDs, expected vs actual
- **Preserve raw data:** Store LLM responses even on validation failure

---

## Configuration

**Location:** `src/paperlab/config/`

**What belongs in config:**
- Environment settings (database paths, API keys)
- Database constraints (field length limits)
- Security rules (validation patterns)
- Error templates (standardized messages)
- Subject mappings (extensibility)

**What stays inline:**
- Display text, single-use literals, visual elements

**Principle:** Extract when duplicated, configurable, or matches external constraints.

---

## Principles Summary

- **Layered architecture** - Clear separation of concerns
- **Repository pattern** - All SQL isolated in data layer
- **Dependency injection** - Testability by design
- **Single responsibility** - Each module has one reason to change
- **Immutable flow** - Side effects only at boundaries
- **Type safety** - Domain objects throughout, Pydantic at boundaries
- **Subject-agnostic** - Core logic identical for all subjects
- **Caller-generated UUIDs** - Enables idempotent operations
