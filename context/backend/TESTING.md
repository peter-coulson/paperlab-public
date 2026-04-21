# Testing Strategy

Code testing for validation gates during agentic development.

**Note:** For marking quality validation with real LLM calls, see `EVALUATION.md`.

---

## Purpose

Tests serve two goals in agentic development:

1. **Validation gates** - Fast feedback during AI-assisted coding ("did I break anything?")
2. **Regression prevention** - Catch unintended changes before they reach production

Tests are NOT for comprehensive coverage. They're guardrails that let AI agents work autonomously.

---

## Two-Layer Strategy

### Layer 1: Fast Validation Gate
**When:** Every change (pre-commit)
**Runtime:** <30 seconds
**Purpose:** Immediate feedback

| Check | What | Why |
|-------|------|-----|
| Type checking | Mypy strict | Catch type errors |
| Linting | Ruff | Code quality |
| Import smoke | All modules import | Catch broken imports |
| Schema validation | DB schema matches | Catch migration issues |

### Layer 2: Integration Tests
**When:** Before commit / on PR
**Runtime:** <2 minutes
**Purpose:** Verify system behavior

| Component | Tests | Stability |
|-----------|-------|-----------|
| Repositories | Public interface contracts | HIGH |
| API endpoints | Request/response shapes | HIGH |
| CLI commands | Commands execute without crash | MEDIUM |
| Loading | JSON parsing, validation | HIGH |

---

## Test Philosophy

### Test Behavior, Not Implementation

```python
# BAD: Breaks if method renamed or signature changes
def test_internal_method():
    result = parser._parse_criterion_text(...)

# GOOD: Only breaks if behavior changes
def test_mark_scheme_loads_correctly():
    result = load_mark_scheme("path/to/test.json", conn)
    assert result["total_marks"] == 10
```

### Test at Public Boundaries Only

| Layer | Test | Don't Test |
|-------|------|------------|
| Repository | `create_paper()`, `get_question_structure()` | Internal SQL building |
| API | Endpoint responses, error codes | Internal service calls |
| CLI | Command exits successfully | Output formatting |

### Real Database, Minimal Mocking

Use real SQLite in-memory connections, not mocks. See `tests/conftest.py` for fixture patterns.

### Let AI Maintain Tests

When refactoring, include tests in scope:
> "Refactor the marking module. Update any tests that break."

With AI assistance, test maintenance is no longer a human burden.

---

## What to Test

### WILL Test

- Repository public methods (contracts, not internals)
- API endpoints (shapes, error handling)
- JSON loading (parsing, validation)
- Complex business logic with edge cases
- CLI command execution (smoke tests)

### WON'T Test

- Private methods or internal helpers
- Simple pass-through functions
- Orchestration layers (minimal logic)
- String formatting or concatenation
- Dataclass field access

**Target: ~30% coverage** focused on stable, critical paths.

---

## File Structure

```
tests/
├── conftest.py                 # Shared fixtures (test DB, connections)
├── test_imports.py             # Import smoke test (Layer 1)
├── repositories/               # Repository contract tests
│   ├── test_papers.py
│   ├── test_questions.py
│   └── test_mark_criteria.py
├── api/                        # API integration tests
│   ├── conftest.py             # TestClient fixture
│   └── test_papers_api.py
├── loading/                    # Data loading validation
│   └── test_paper_loader.py
└── cli/                        # Smoke tests only
    └── test_commands.py
```

---

## CI/CD Integration

| Stage | Tests | Target |
|-------|-------|--------|
| Pre-commit | Linting, type checking, import smoke | <30 seconds |
| On PR | Repository, API, CLI integration | <2 minutes |
| Weekly | Evaluation suite (real LLM) | Regression detection |

---

## Adding New Tests

**When to add:**
- After finding bugs in production
- When refactoring complex code
- For new public API boundaries
- When AI agents need validation feedback

**When NOT to add:**
- For code that rarely changes
- For simple, obvious functions
- When test is longer than the code
- For implementation details that may change

---

## Relationship to Evaluation Framework

| Aspect | Code Tests (This) | Evaluation Tests |
|--------|-------------------|------------------|
| Purpose | Validate code behavior | Validate marking accuracy |
| Speed | Fast (<2 min) | Slow (real LLM calls) |
| Cost | Free | API costs |
| When | Every change | Pre-deployment/weekly |
| Database | In-memory test DB | 3-database architecture |

Both systems complement each other:
- Code tests catch **code bugs** fast
- Evaluation tests catch **marking quality** regressions
