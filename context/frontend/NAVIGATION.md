# Navigation

Screen flow and navigation patterns for PaperLab mobile app.

---

## Navigation Pattern

**Approach:** Imperative navigation with `Navigator.push()` and `MaterialPageRoute`.

**Why:** Simple screen-to-screen navigation. No deep linking needed for mobile-only app.

**Future:** Add `go_router` if deep linking or web support needed.

---

## Hub-and-Spoke Flow

```
                        ┌──────────────┐
                        │ LoginScreen  │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  HomeScreen  │◄────────┐
                        │    (Hub)     │         │
                        └──┬───────┬───┘         │
                           │       │             │
              ┌────────────┤       └──────┐      │
              ▼            │              ▼      │
    ┌─────────────┐  ┌─────────┐  ┌──────────────┐
    │  Selection  │  │Settings │  │Results Screen│
    └──────┬──────┘  └─────────┘  └──────────────┘
           │
           ▼
    ┌─────────────┐
    │   Upload    │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │  Marking    │
    │  Progress   │
    └──────┬──────┘
           │
           └─────────────────────────────────────┘
```

**Hub:** HomeScreen is central navigation point (all flows return here)

**Spokes:** Selection → Upload → Marking → Results (one-way flow for new attempts)

---

## State-Aware Navigation

| Attempt State | Tapping Item Navigates To |
|---------------|---------------------------|
| Draft | Upload Screen (can edit photos) |
| Marking | MarkingInProgressScreen |
| Complete | Results Screen |

---

## Push vs PushReplacement

### Navigator.push (can go back)

- HomeScreen → SelectionScreen
- HomeScreen → SettingsScreen
- HomeScreen → Results screens
- Selection → Upload screens
- Results → QuestionResults → FullscreenImageViewer

### Navigator.pushReplacement (one-way boundaries)

| Transition | Why |
|------------|-----|
| Login → HomeScreen | Can't return to login after auth |
| Upload → MarkingProgress | **Photo Lock** - photos immutable after submit |
| MarkingProgress → Results | **Grade Lock** - grade immutable after marking |

**Rationale:** Immutability boundaries enforce data integrity.

---

## Workflow Differences

### Papers Workflow
```
HomeScreen → Selection → PaperUpload → Marking → PaperResults → QuestionResults
```

### Questions Workflow
```
HomeScreen → Selection → QuestionUpload → Marking → QuestionResults
```

**Back navigation context:**
- Papers: QuestionResults back → PaperResults
- Questions: QuestionResults back → HomeScreen

---

## Native Back Behavior

**Pattern:** Rely on system back gesture/button (iOS swipe, Android button).

**No custom back buttons:** Native gesture is familiar to users.

**Screens with no back:**
- HomeScreen (root of stack)
- Screens reached via pushReplacement (Login, Upload→Marking, Marking→Results)

---

## Screen Initialization Patterns

### ID-Based Screen Constructors

**Pattern:** Screens accept IDs (not model objects), fetch data via providers.

**Why ID-based:**
- Single source of truth (API is always current)
- No stale model data passed through navigation
- Provider caching works correctly (same ID = cached data)
- Supports deep linking (can reconstruct screen from ID alone)

**Example:**
```dart
// ✅ ID-based (M6 pattern)
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (_) => PaperResultsScreen(attemptId: 123),
  ),
);

// ❌ Model-based (M5 anti-pattern)
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (_) => PaperResultsScreen(paperResult: result),
  ),
);
```

**Screen fetches data:**
```dart
class PaperResultsScreen extends ConsumerWidget {
  final int attemptId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final resultsAsync = ref.watch(paperResultsProvider(attemptId));
    // Provider handles API call, caching, errors
  }
}
```

**Where:** All results screens, marking progress screen use ID-based constructors.

### Named Constructor Flows

**Pattern:** Use named constructors to distinguish different navigation flows to same screen.

**Use case:** QuestionResultsScreen reachable from two different flows with different data needs.

**Implementation:**
```dart
class QuestionResultsScreen extends ConsumerWidget {
  // Paper flow: Navigate from PaperResultsScreen
  const QuestionResultsScreen.fromPaper({
    required this.paperAttemptId,
    required this.questionAttemptId,
  }) : practiceAttemptId = null;

  // Practice flow: Navigate from MarkingInProgressScreen
  const QuestionResultsScreen.fromPractice({
    required this.practiceAttemptId,
  }) : paperAttemptId = null,
       questionAttemptId = null;

  final int? paperAttemptId;
  final int? questionAttemptId;
  final int? practiceAttemptId;

  bool get _isPractice => practiceAttemptId != null;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Choose provider based on constructor used
    final resultsAsync = _isPractice
        ? ref.watch(practiceResultsProvider(practiceAttemptId!))
        : ref.watch(paperQuestionResultsProvider(
            paperAttemptId: paperAttemptId!,
            questionAttemptId: questionAttemptId!,
          ));
  }
}
```

**Why named constructors:**
- Type-safe flow distinction (compile-time safety)
- Clear intent at call site (.fromPaper vs .fromPractice)
- Different required parameters per flow
- Single screen serves both use cases

**Where:** See `lib/screens/question_results_screen.dart`

---

## Principles

- **Hub-and-spoke** - HomeScreen is central point
- **State-aware** - Navigation based on attempt state
- **One-way boundaries** - Photo Lock and Grade Lock use pushReplacement
- **Native back** - System gesture/button, no custom buttons
- **Context-aware** - Back behavior depends on entry context
- **ID-based constructors** - Screens accept IDs, providers fetch data
- **Named constructors** - Distinguish flows to same screen
