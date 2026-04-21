# Frontend Testing Strategy

Testing approach for the Flutter frontend.

---

## Decision: Minimal Unit Tests Only

**Date:** January 2026

**Decision:** No widget or golden testing. Unit tests only for utility functions with edge cases.

---

## Rationale

### Frontend Architecture Reality

The frontend is a **thin presentation layer** (~14K lines):
- Zero business logic (backend owns marking, evaluation, calculations)
- ~600 lines of actual logic (utilities + cascading dropdown builders)
- Standard Riverpod state management patterns
- Widgets are pure composition/presentation

### Analysis Against Testing Goals

| Goal | Traditional Tests | Hot Reload + AI Visual | Winner |
|------|------------------|----------------------|--------|
| Fast feedback during development | Moderate | Instant | Hot Reload |
| Regression prevention | Good for logic | Good for visual | Depends |
| Low maintenance burden | Poor for widgets | Good | AI Visual |

### Why NOT Widget/Golden Tests

1. **Hot reload provides instant visual feedback** - faster than any test cycle
2. **AI visual iteration** - screenshot → feedback → iterate replaces widget assertions
3. **Widget tests break on refactoring** - high maintenance for thin UI layer
4. **Golden tests have cross-platform issues** - CI flakiness requires setup effort
5. **Backend tests catch data regressions** - API shape, response formats

### Why Unit Tests for Utilities

The ~600 lines of actual logic have edge cases that fail silently:
- Date parsing (invalid formats, boundary months)
- String extraction (regex edge cases)
- Cascading filter logic (empty lists, null selections)

These are **pure functions** - high ROI, low maintenance.

---

## What to Test

| File | Functions | Edge Cases |
|------|-----------|------------|
| `exam_date_utils.dart` | `formatExamDate`, `compareExamDatesDescending`, `examDateOptionsFromKeys` | Invalid months, malformed date keys, empty sets |
| `string_utils.dart` | `capitalizeFirst`, `extractPaperType` | Empty strings, non-letter starts, no regex match |
| `paper_selection_builder.dart` | `buildPaperSelectionFields` | Empty papers, single date (no field 2), null selection |
| `question_selection_builder.dart` | `buildQuestionSelectionFields` | Empty lists, partial selections, invalid date format |

**Target:** ~15 unit tests covering edge cases.

---

## What NOT to Test

| Category | Reason |
|----------|--------|
| Widgets | Hot reload provides instant feedback |
| Screens | Thin orchestration, no logic |
| Repositories | Thin API wrappers (backend tests catch API issues) |
| Providers | Riverpod patterns are proven framework code |
| Models | Generated Freezed code |

---

## Test Location

```
test/
└── utils/
    ├── exam_date_utils_test.dart
    ├── string_utils_test.dart
    ├── paper_selection_builder_test.dart
    └── question_selection_builder_test.dart
```

---

## Running Tests

```bash
fvm flutter test test/utils/
```

---

## When to Add More Tests

Add tests when:
- Finding bugs in utility functions
- Adding new pure functions with edge cases
- Complex conditional logic that isn't visually obvious

Do NOT add tests for:
- New widgets (use hot reload)
- Screen layouts (use visual verification)
- Simple pass-through functions
