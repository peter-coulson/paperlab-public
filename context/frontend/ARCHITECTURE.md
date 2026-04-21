# Flutter Architecture

High-level code structure for PaperLab mobile app.

---

## Layered Architecture

```
Screens (screens/)
    ↓ uses
State Management (providers/ - M6)
    ↓ uses
API Client (services/api/ - M6)
    ↓ calls
Backend API

Widgets (widgets/)
    ↑ used by Screens

Theme (theme/) + Models (models/) + Utils (utils/)
    ↑ used by all layers
```

**Dependency rule:** Each layer only depends on the layer below.

---

## Module Responsibilities

| Module | Owns | Never |
|--------|------|-------|
| **Screens** | Full-screen views, navigation, state orchestration | Widget code, inline calculations |
| **Widgets** | Reusable UI components, presentation logic | Business logic, API calls, navigation |
| **Models** | Data structures, type definitions | Business logic, UI code |
| **Theme** | Design system constants (colors, typography, spacing) | Business logic, UI code |
| **Utils** | Data transformation, formatting, validation (returns models/primitives) | UI code (returns Widget), state management |
| **Services** | API client, auth, storage (M6) | UI code, direct state mutation |

---

## Core Patterns

### Widget Composition

See `WIDGETS.md` for widget organization patterns.

**Principle:** Build complex UIs from small, focused widgets. Composition over inheritance.

### State Management

See `STATE-MANAGEMENT.md` for state patterns.

**M5:** StatefulWidget + setState (screens contain business logic)
**M6:** Riverpod (business logic in providers)

### Navigation

See `NAVIGATION.md` for screen flow and routing.

**Pattern:** Imperative navigation with MaterialPageRoute.

---

## Key Decisions

### Immutable State

**Principle:** Models use final fields. Updates via state management.

**Why:**
- Predictable behavior (no hidden mutations)
- Flutter optimization (const constructors)
- Works seamlessly with Riverpod

### Subject-Agnostic Design

**Principle:** Architecture supports all subjects without changes.

**How:**
- Generic question/paper structures
- Content differences in text fields, not structure
- No subject-specific widgets or colors

**Adding new subject:**
1. Backend adds prompts and mark types (config only)
2. Frontend requires NO changes

### FVM Required

**Command:** Always use `fvm flutter` (not `flutter`)

**Why:** Locks Flutter version per project.

### Analysis Required

**Command:** `mcp__dart__analyze_files` after editing Dart code

**Why:** Catches issues immediately (missing consts, BuildContext after async).

### Async Linter Rules

**Rule:** `unawaited_futures: true` enforced in `analysis_options.yaml`

**Why:** Prevents regression to blocking async patterns. Requires explicit `unawaited()` for fire-and-forget operations.

**What it catches:** Missing `unawaited()` wrapper on Futures that are intentionally not awaited.

**See:** `PERFORMANCE.md` → Non-Blocking Async Patterns for usage.

### Driver Logging (Agentic Testing)

**Purpose:** Enable automated UI testing via MCP flutter_driver with reliable state queries.

**Key patterns:**
- **Auto-interception** - Navigation and snackbars captured without screen changes
- **ScaffoldMessenger subclass** - `LoggingScaffoldMessenger` intercepts ALL snackbar calls
- **kDebugMode guards** - All code tree-shaken in release builds
- **Opacity(0) not Visibility** - Keeps widget in semantics tree for flutter_driver

**Why:**
- Enables state-based validation (10x faster than screenshot analysis)
- Zero manual instrumentation for navigation/snackbars
- Production-safe (no overhead in release builds)

**Where:** `lib/driver/`, `lib/driver_main.dart`

**See:** `AGENTIC_UI_TESTING.md` for usage guide

### HTTP Client: Dio

**Decision:** Use Dio package (not dart:http) for all HTTP operations.

**Why Dio:**
- **Global interceptors** - Catch and convert all errors automatically in one place
- **Better timeout handling** - Per-operation timeouts with clear timeout exceptions
- **Type-safe responses** - Structured error types for pattern matching
- **Industry standard** - 130k+ pub.dev likes, used by major apps
- **Better developer experience** - Cleaner API, better error messages

**Migration rationale (http → Dio):**
- Old approach: Manual error checking in every repository method
- New approach: Global error interceptor converts all failures to NetworkException types
- Result: Repositories have no error handling code, exceptions propagate cleanly

**Architecture:**
```
DioClient (global interceptor) → ApiClient (thin wrapper) → Repositories
```

**Where:** See `lib/services/dio_client.dart`

**See `API-INTEGRATION.md` for exception hierarchy and error flow.**

### Image Viewer: easy_image_viewer

**Decision:** Use `easy_image_viewer` package for fullscreen image viewing (not `photo_view` or custom implementation).

**Why easy_image_viewer:**
- **Built-in swipe-dismiss** - Native gesture support without custom implementation
- **Battle-tested** - 35k+ downloads, verified publisher, active maintenance
- **Zero dependencies** - Simpler dependency graph vs `photo_view` chain
- **Purpose-built** - Designed specifically for image viewing with gestures
- **Aligns with simplicity** - Use proven tools vs building/maintaining custom gesture detection

**Configuration:**
- Close button visible with `closeButtonColor: Colors.white` for discoverability
- Swipe-down-to-dismiss remains primary gesture

**Where:** See `WIDGETS.md` → Fullscreen Image Viewing for usage pattern

### Input Validation at Boundaries

**Principle:** Utilities validate inputs at boundaries and throw typed exceptions (fail-fast).

**How:**
- Validate inputs in utility methods (not at call sites)
- Use type-specific exceptions (ArgumentError, RangeError, FormatException)
- Let exceptions propagate to UI layer for error handling

**Why:**
- Fail-fast principle (catch errors early)
- Single source of validation logic
- Clear contract for utility consumers

**Where:** See `lib/utils/exam_date_utils.dart` for validation examples

---

## Design Benefits

- **Simple layered architecture** - Clear separation of concerns
- **Widget composition** - Small, focused, reusable widgets
- **Type safety** - Models provide clear contracts
- **Subject-agnostic** - Works for all subjects without changes
- **Const optimization** - Compile-time widget caching
- **Immutable state** - Predictable behavior
