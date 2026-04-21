# Code Check - Services Module

Follow the code quality checking method defined in `code-check-method.md`.

## Scope

**Module:** Application Services
**Files to check:** `src/paperlab/services/**/*.py`
**Report location:** `.quality/code/services-{TIMESTAMP}.md`

## Module Description

The services module contains:
- Application workflow orchestration
- Service layer implementations
- Cross-cutting concerns
- Integration between modules
- External service interactions

## Special Considerations

- **Layered architecture** - Services coordinate between CLI, domain, and data layers
- **Error handling** - Services are key error boundaries
- **Testability** - Services should have mockable dependencies

Run the standard code-check method on these files only.
