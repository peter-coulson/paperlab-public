# Data Models

Flutter model structure and API parsing patterns.

---

## Model Principles

**Immutability:** All fields are `final`. Updates via `copyWith()` or provider state.

**Type safety:** Enums for states, DateTime for timestamps, explicit nullability.

**Subject-agnostic:** Models work for all subjects without changes.

---

## fromJson Factory Pattern

**Purpose:** Parse API JSON responses into typed models.

```dart
class PaperAttempt {
  final int id;
  final String attemptUuid;
  final String paperName;
  final PaperAttemptState state;
  final DateTime createdAt;

  factory PaperAttempt.fromJson(Map<String, dynamic> json) {
    return PaperAttempt(
      id: json['id'],
      attemptUuid: json['attempt_uuid'],
      paperName: json['paper_name'],
      state: _deriveState(json),
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
```

**Why factories:**
- Single source of truth for API mapping
- Type-safe parsing (compile-time errors)
- Encapsulates transformation logic

**Where:** All models that come from API have `fromJson`. See `lib/models/`

---

## State Derivation Pattern

**Principle:** Derive state from timestamps (don't store state directly).

**Backend sends timestamps, frontend computes state:**

```dart
static PaperAttemptState _deriveState(Map<String, dynamic> json) {
  final submittedAt = json['submitted_at'] != null
      ? DateTime.parse(json['submitted_at'])
      : null;
  final completedAt = json['completed_at'] != null
      ? DateTime.parse(json['completed_at'])
      : null;

  if (completedAt != null) return PaperAttemptState.complete;
  if (submittedAt != null) return PaperAttemptState.marking;
  return PaperAttemptState.draft;
}
```

**Why:**
- Single source of truth (timestamps in database)
- No synchronization bugs (state always matches reality)
- Matches backend derivation logic

**See:** `api/WORKFLOWS.md` for backend status derivation.

---

## API Field Mapping

**Convention:** Backend uses snake_case, Flutter uses camelCase.

| API Field | Model Field | Transformation |
|-----------|-------------|----------------|
| `id` | `id` | Direct |
| `attempt_uuid` | `attemptUuid` | snake_case → camelCase |
| `paper_name` | `paperName` | snake_case → camelCase |
| `created_at` | `createdAt` | Parse ISO 8601 to DateTime |
| `submitted_at` | - | Used in state derivation |
| `completed_at` | - | Used in state derivation |

**Nullable fields:** Fields marked `DateTime?` or `String?` map to potentially null API fields.

---

## Model State Enums

**Paper attempts:**

```dart
enum PaperAttemptState {
  draft,    // Not yet submitted
  marking,  // Submitted, marking in progress
  complete, // Marking complete
}
```

**Question attempts (practice):**

```dart
enum QuestionAttemptState {
  marking,  // Submitted, marking in progress
  complete, // Marking complete
}
```

**Why no draft for questions:** Practice questions submit immediately on creation.

**Score parsing:** QuestionAttempt includes optional `Score` (awarded/available) parsed from `marks_awarded` and `marks_available` API fields. Only populated for completed attempts.

---

## Discovery Models

**Purpose:** Parse discovery API responses for selection screens.

### PaperMetadata

**From:** `GET /api/papers`

**Fields:**
- `paperId` - Database ID
- `examBoard`, `examLevel`, `subject` - Exam taxonomy
- `paperCode`, `displayName` - Paper identification
- `year`, `month` - Exam date
- `totalMarks`, `questionCount` - Paper stats

**Usage:** Populate paper selection dropdown, create draft paper attempt.

### QuestionMetadata

**From:** `GET /api/questions`

**Fields:**
- `questionId`, `paperId` - Database IDs
- `paperDisplayName` - Human-readable paper name (e.g., "Paper 1 (Non-Calculator)")
- `questionNumber`, `totalMarks` - Question identification

**Usage:** Populate question selection dropdown, submit practice attempt.

**Where:** See `lib/models/paper_metadata.dart`, `question_metadata.dart`

---

## copyWith Pattern

**For immutable updates:**

```dart
class PaperAttempt {
  // Fields...

  PaperAttempt copyWith({
    PaperAttemptState? state,
    String? grade,
  }) {
    return PaperAttempt(
      id: id,
      attemptUuid: attemptUuid,
      paperName: paperName,
      state: state ?? this.state,
      grade: grade ?? this.grade,
      createdAt: createdAt,
    );
  }
}
```

**Used by providers for local state updates** (e.g., optimistic UI updates).

---

## const Constructors

**Widgets use const where possible:**

```dart
class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.message});

  final String message;
}
```

**Why:** Flutter optimization (widget caching at compile time).

**Rule:** Use `const` constructor when all fields are final and immutable.

---

## Related Documentation

- `API-INTEGRATION.md` → How repositories call APIs and parse JSON
- `STATE-MANAGEMENT.md` → How providers use models
- `api/WORKFLOWS.md` → Backend timestamp and status derivation
- `shared/JSON-FORMATS.md` → API response formats
