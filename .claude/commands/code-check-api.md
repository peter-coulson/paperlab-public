# Code Check - API Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** API Layer (FastAPI)
**Files to check:** `src/paperlab/api/**/*.py`
**Report location:** `.quality/code/api-{TIMESTAMP}.md`

## Module Description

The API module contains:
- FastAPI application and routers
- Pydantic request/response models
- Authentication (JWT)
- Exception handlers
- Status derivation logic

## Special Considerations

- **Transport only** - Endpoints must call orchestrators/services, never contain business logic. Look for: database queries in endpoints, complex conditionals, data transformations beyond `from_domain()`
- **`from_domain()` pattern** - All response models must use `from_domain()` classmethod to convert domain objects. Missing pattern = violation
- **Two-layer validation** - Pydantic validates structure (types, formats), domain validates business rules. API should NOT duplicate business validation
- **Transaction management** - Endpoints own transaction lifecycle (Pattern A: with connection, try/commit/except rollback)
- **Resource-oriented endpoints** - URLs model resources not verbs. Bad: `/api/mark`, Good: `/api/submissions`
- **Error translation** - Repository `ValueError` → HTTP 404. Don't expose internal errors
- **Async patterns** - Proper async/await usage, no blocking calls in async endpoints
- **Status derivation** - Status computed from timestamps, never stored as enum

Run the standard code-check method on these files only.
