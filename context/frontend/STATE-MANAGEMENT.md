# State Management

State management strategy for PaperLab mobile app.

---

## Current Approach (M6)

**Choice:** Riverpod

**Why Riverpod over alternatives:**
- Compile-time safety (errors at compile time, not runtime)
- No BuildContext dependency (providers usable anywhere)
- Better testability than Provider
- AsyncValue pattern handles loading/error/data cleanly

---

## Key Patterns

### Timestamp-Based State

**Principle:** Derive state from immutable timestamps (don't store state directly).

**Implementation:** Frontend receives derived status from API.
- Backend derives status from timestamps (submitted_at, completed_at, etc.)
- Frontend displays what API returns
- Single source of truth (no synchronization bugs)

**See:** `api/WORKFLOWS.md` → Status Polling Flow for status values.

### Immutability Boundaries

**Photo Lock (Submission Boundary):**
- Trigger: User submits (submitted_at set)
- Effect: Photos become immutable
- Navigation: Can't return to upload screen

**Grade Lock (Completion Boundary):**
- Trigger: Marking completes (completed_at set)
- Effect: Grade becomes immutable
- Navigation: Can't return to marking screen

**Rationale:** Immutability boundaries enforce data integrity (matches backend constraints).

### Async State Pattern

**Use AsyncValue for all API operations:**
- loading: Show skeleton screen (not generic spinner)
- data: Show content
- error: Show retry option

**Benefits:** Consistent loading/error handling across all screens.

**Skeleton loading states:**
- **Pattern:** Use `skeletonizer` package to show layout preview during loading
- **Why:** Research shows 20-30% improvement in perceived speed vs spinners for <500ms waits
- **Implementation:** Wrap layout structure in `Skeletonizer()` widget with `Bone.text()` placeholders
- **Where:** See `lib/screens/home_screen.dart:_buildPapersSkeleton()`

### Navigation with Async Data (Updated M7)

**Two patterns for different use cases:**

#### Pattern 1: Navigate Then Load (User-Facing Navigation)

**Use when:** User-initiated navigation where blocking feels slow (>100ms API calls)

**Examples:**
- Paper selection (loads papers metadata)
- Question selection (loads questions + papers)
- Results screen (loads marking results)

**Implementation:**
1. Create domain-specific screen (e.g., `PaperSelectionScreen`)
2. Screen extends `ConsumerWidget`
3. Watch provider with `ref.watch(provider)`
4. Use `AsyncValue.when()` for loading/error/data states
5. Navigate immediately from source screen (0ms blocking)

**Code example:** `lib/screens/paper_selection_screen.dart`

**Loading state:** Show skeleton screen with Skeletonizer (mimics actual layout)

**Error handling:** Show error screen with "Retry" and "Go Back" buttons

**Benefits:**
- ✅ Instant navigation (0ms perceived latency)
- ✅ Professional skeleton UI (aligns with iOS/Android guidelines)
- ✅ User has agency (can press back during loading)
- ✅ Error state shows full context (not just SnackBar)

**Trade-offs:**
- ⚠️ Screen has async concerns (loading + error states)
- ⚠️ Error requires explicit back navigation (not prevented)

#### Pattern 2: Load Before Action (Background Operations)

**Use when:** Background operation where error should prevent action (mutations, submissions)

**Examples:**
- Resuming draft papers (load draft data before navigating to upload screen)
- API mutations (delete, update)
- Operations where partial state is dangerous

**Implementation:**
1. `await ref.read(provider.future)` before taking action
2. Catch errors, show SnackBar, stay on current screen
3. Only proceed if operation succeeds

**Code example:** `lib/screens/home_screen.dart:_onPaperTapped()`

**Benefits:**
- ✅ Clean error UX (stay on current screen)
- ✅ Simple retry (tap button again)
- ✅ Prevents invalid state (action only happens on success)

**Trade-offs:**
- ⚠️ Blocks UI during operation (can show non-modal progress indicator)
- ⚠️ Feels slow if operation >100ms

**Decision criteria:**
- User tapping navigation button → **Pattern 1** (navigate then load)
- User submitting form/mutation → **Pattern 2** (load before action)
- Unsure? Default to **Pattern 1** for better perceived performance

**Why Pattern 1 is preferred:** Mobile UX guidelines (iOS HIG, Material Design) emphasize instant feedback. Blocking navigation feels unresponsive even at 100-200ms.

**Cross-reference:** See `api/WORKFLOWS.md` → Resuming Draft Papers for API-side flow.

### Data Prefetching

**Pattern:** Warm Riverpod cache on HomeScreen initialization for commonly-needed data.

**Implementation:** Use `addPostFrameCallback` in `HomeScreen.initState()` to read providers without blocking first frame.

**What to prefetch:**
- ✅ Parameterless providers always shown (paperAttemptsProvider, questionAttemptsProvider, availablePapersProvider)
- ❌ Parameterized providers (can't prefetch without selection)
- ❌ User-specific/polling data (may change)

**Timing:** Prefetch fires in HomeScreen (authenticated users only), NOT in PaperLabApp (before authentication).

**Why HomeScreen:** Ensures user is authenticated before API calls. Avoids wasting requests on login screen.

**Error handling:** Graceful - first screen to watch provider sees error state and shows retry.

**Performance:** Use `unawaited()` + `Future.wait()` for non-blocking parallel execution. See `PERFORMANCE.md` for async patterns.

**Where:** See `lib/screens/home_screen.dart:_prefetchData()`

---

## Architecture

### Layer Responsibilities

| Layer | Owns | Location |
|-------|------|----------|
| **Providers** | State, business logic, API orchestration | `lib/providers/` |
| **Repositories** | API calls, data transformation | `lib/repositories/` |
| **Screens** | UI rendering, consume providers | `lib/screens/` |
| **Widgets** | Pure presentation | `lib/widgets/` |

### Data Flow

```
Screen (watches provider)
    ↓ triggers action
Provider (orchestrates)
    ↓ calls
Repository (API request)
    ↓ returns
Provider (updates state)
    ↓ notifies
Screen (rebuilds)
```

---

## Screen State Ownership

| Screen | State Needs |
|--------|-------------|
| **HomeScreen** | Paper list, question list, selected tab |
| **SelectionScreen** | Multi-level dropdown cascade |
| **Upload screens** | Image list, validation |
| **MarkingInProgressScreen** | Polling status |
| **Results screens** | Static (data from navigation) |

---

## Polling Pattern

**Use case:** MarkingInProgressScreen polls status API while marking runs.

**Pattern:** Use `dart:async` Timer in Riverpod provider for periodic API polling.

**Key decisions:**
- Poll interval: 3 seconds (balance between responsiveness and API load)
- Initial fetch before timer starts (no wait on screen load)
- Timer auto-cancels on terminal states (completed/failed)
- Timer continues on errors (network issues are often transient)
- `ref.onDispose()` ensures cleanup when screen closes
- Auto-navigation uses `WidgetsBinding.instance.addPostFrameCallback` to prevent "setState during build" errors

**Where:** See `lib/providers/status_provider.dart`, `lib/screens/marking_in_progress_screen.dart`

**See:** `api/WORKFLOWS.md` → Status Polling Flow for API endpoints and status values.

---

## Optimistic Updates with Undo

**Use case:** Delete operations with immediate UI feedback and undo support.

**Pattern:** Remove item from local state immediately, call API in background, rollback on failure.

**Why optimistic:**
- Immediate UI feedback (feels fast)
- No spinner during delete
- Undo support without extra state

**Where:** See `lib/providers/attempts_provider.dart`

---

## Error Handling in Screens

**Critical rules for async operations (uploads, API calls):**

- ❌ **No navigation on error** - User stays on current screen
- ❌ **No optimistic UI updates** - Only show success after confirmation
- ✅ **Reset loading indicators** - setState() to clear loading state
- ✅ **Preserve form state** - User can fix and retry
- ✅ **User-friendly messages** - Use `ErrorMessages.getUserMessage(e)`

**Why these rules:**
- **No navigation** → User needs to see error and retry
- **No optimistic updates** → Don't show green checkmarks on failure
- **Reset loading** → User knows operation completed (even if failed)
- **Preserve state** → Photos, form data remain for retry
- **Friendly messages** → No technical jargon (SocketException, etc.)

**Where:** See `lib/screens/question_upload_screen.dart`, `paper_upload_screen.dart`

**See `DESIGN_SYSTEM.md` for error messaging UX standards.**

### Race Condition Prevention

**Problem:** Rapid button taps can trigger multiple concurrent async operations.

**Solution:** Defense-in-depth with guards at both UI and provider levels.

**Why defense-in-depth:** UI guard prevents most cases, provider guard catches edge cases where provider state is stale.

**Where:** See `lib/screens/question_upload_screen.dart:_handleConfirm()`, `lib/providers/upload_provider.dart:submit()`

---

## Provider Patterns

### keepAlive for Multi-Screen Flows

**Problem:** Riverpod auto-disposes providers when no longer watched, losing state during navigation.

**Solution:** Use `@Riverpod(keepAlive: true)` for providers that manage multi-screen workflows.

**When to use:**
- Upload flows (navigate between screens while preserving state)
- Draft workflows (leave and return without losing progress)
- Any workflow spanning multiple screens

**Where:** See `lib/providers/upload_provider.dart` - PaperUploadFlow, PracticeUploadFlow

### Cache Retention for Prefetch

**Problem:** Riverpod autoDispose clears prefetched data ~1s after loading, making prefetch ineffective.

**Solution:** Use `cacheFor()` extension to keep providers alive for specified duration (typically 5 minutes to balance memory vs cache effectiveness).

**When to use:**
- Prefetched providers (prevent autoDispose from clearing cache)
- Expensive-to-load data that's frequently accessed

**Where:** See `lib/utils/cache_extensions.dart` for implementation, `lib/providers/attempts_provider.dart` and `lib/providers/discovery_provider.dart` for usage

### Upload Flow Orchestration

**Pattern:** State machine providers manage multi-step upload workflows.

**Paper Flow (Multi-Step):** initial → creating → draft → submitting → submitted

**Practice Flow (Single-Step):** initial → uploading → submitting → submitted

**Error handling:** On failure, throw exception (UI catches and shows error). For practice flow, also reset state to allow retry.

**Where:** See `lib/providers/upload_provider.dart`, `lib/models/upload_state.dart`

### Data Refresh Patterns

**Provider invalidation after mutations:**
- **Pattern:** Call `ref.invalidate(dependentProvider)` after mutations affecting other screens
- **Why:** Ensures dependent UI auto-refreshes with new data (no tab switch or restart needed)
- **Where:** See `lib/providers/upload_provider.dart:createDraft()`, `finalize()`, `submit()`

**Pull-to-refresh:**
- **Pattern:** RefreshIndicator + AlwaysScrollableScrollPhysics + await ref.read(provider.future)
- **Why:** Users can manually refresh stale data (standard mobile UX)
- **AlwaysScrollableScrollPhysics:** Required for empty lists to enable pull gesture
- **Where:** See `lib/screens/home_screen.dart:_handleRefresh()`, `paper_upload_screen.dart:_handleRefresh()`

**Refresh error handling:**
- **Pattern:** Try-catch with `ErrorMessages.showRefreshError(context, e)`
- **Why:** Refresh failures show friendly error instead of crash
- **Where:** See `lib/utils/error_messages.dart:showRefreshError()`

---

## Selection State Pattern

### Cascading Dropdowns with Field Builder

**Problem:** Multi-level dropdowns where later fields depend on earlier selections (e.g., Paper Type → Exam Date → Question).

**Solution:** Use builder function that receives current selections and returns updated fields.

**Why this pattern:**
- SelectionScreen stays generic (no domain knowledge)
- Parent screen owns data transformation
- Cascading happens via setState (no navigation)
- Single-screen experience (UX best practice)

**Where:** See `lib/screens/selection_screen.dart`, `home_screen.dart`

---

## Principles

- **Riverpod for M6** - Compile-time safety, clean async handling
- **Timestamp-based state** - Backend derives, frontend displays
- **Immutability boundaries** - Photo Lock and Grade Lock
- **AsyncValue everywhere** - Consistent loading/error/data pattern
- **Providers own logic** - Screens are thin consumers
- **Optimistic updates** - Immediate UI response with rollback support
- **Widgets unchanged** - Pure presentation, no state awareness
