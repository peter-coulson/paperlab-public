# Performance Optimization

Performance patterns and decisions for Flutter app optimization.

---

## Core Principles

- **Non-blocking UI** - Never block the UI thread (verified via Timeline profiling)
- **Prefetch common data** - Warm cache on app start for instant navigation
- **Skeleton screens** - Show layout preview during loading (better perceived performance than spinners)
- **Real-world testing** - Verify performance under production conditions (Railway cold starts, slow networks)

---

## Non-Blocking Async Patterns

### Fire-and-Forget Operations

**Problem:** Background operations (prefetch, analytics, logging) that should never block UI.

**Solution:** Use explicit async primitives to signal intent and ensure parallel execution.

**Required primitives:**
1. `unawaited()` from `dart:async` - Signals fire-and-forget intent
2. `Future.wait()` - Parallel execution (NOT cascade operator)
3. `.catchError()` - Mandatory error handling for background operations

**Why these primitives:**
- **`unawaited()`** - Makes fire-and-forget explicit (enables linter enforcement)
- **`Future.wait()`** - True parallel execution (cascade operator is sequential)
- **`.catchError()`** - Prevents unhandled exceptions in background work

**Example pattern:**

```dart
void _prefetchData() {
  unawaited(
    Future.wait([
      ref.read(provider1.future),
      ref.read(provider2.future),
      ref.read(provider3.future),
    ]).catchError((error) => debugPrint('Prefetch failed: $error')),
  );
}
```

**Where:** See `lib/screens/home_screen.dart:_prefetchData()` for full implementation

**Common mistake:** Using cascade operator for "parallel" execution

```dart
// ❌ DON'T: Cascade is sequential, blocks during each request
ref
  ..read(provider1.future)  // Waits for this to complete
  ..read(provider2.future)  // Then waits for this
  ..read(provider3.future); // Then waits for this
```

**Linter enforcement:** `unawaited_futures` rule catches missing `unawaited()` (see ARCHITECTURE.md)

---

## Data Prefetching Strategy

**Goal:** Reduce skeleton screen duration from 200ms to 0-50ms (75-100% improvement).

**Implementation:** Warm Riverpod cache on HomeScreen initialization with commonly-needed data.

**Timing:** After first frame (`addPostFrameCallback`) to avoid blocking initial render.

**What to prefetch:**
- ✅ Parameterless providers shown to all users (paperAttemptsProvider, questionAttemptsProvider, availablePapersProvider)
- ❌ Parameterized providers (can't prefetch without user selection)
- ❌ User-specific data that changes frequently

**Error handling:** Silent failures with debug logging. First screen to watch provider sees error state and shows retry.

**Authentication-aware:** Prefetch only happens in HomeScreen (authenticated users only). Never prefetch before authentication.

**See:** `STATE-MANAGEMENT.md` → Data Prefetching for state management details.

---

## Cache Retention

**Problem:** Riverpod autoDispose clears prefetched data ~1s after loading, making prefetch ineffective.

**Solution:** Use `cacheFor()` extension to keep providers alive for specified duration.

**Pattern:**

```dart
@override
Future<List<Data>> build() async {
  ref.cacheFor(const Duration(minutes: 5));
  // ... fetch data
}
```

**Why 5 minutes:** Balances memory usage (keeps data fresh) vs cache effectiveness (data available during typical user session).

**Memory impact:** Prefetching three providers loads ~130-315KB total (acceptable for modern devices).

**See:** `STATE-MANAGEMENT.md` → Provider Patterns → Cache Retention for implementation details.

---

## Performance Testing

### Timeline Profiling (Mandatory)

**Goal:** Verify async operations execute in <10ms on UI thread.

**Why:** Operations >10ms can cause frame drops and perceived lag.

**Method:**
1. Open Flutter DevTools → Timeline tab
2. Record during operation (app start, navigation, etc.)
3. Find operation in timeline
4. Verify UI thread shows <10ms
5. Verify network I/O shows as async work (separate from UI thread)

**Pass criteria:**
- UI thread time: <10ms ✅
- No frame drops during operation ✅
- App remains responsive ✅

**Where to verify:**
- Prefetch operations on app start
- Navigation between screens
- Image uploads (compression happens async)
- Any background operation

### Real-World Testing

**Production conditions matter:** Local testing (50ms API) doesn't reflect production (Railway cold starts = 1-2s).

**Required tests:**
1. **Railway cold start** - Close app, wait 5+ minutes, relaunch. Verify no "hung up" errors.
2. **Network throttling** - Test on slow 3G. Verify skeleton displays (not frozen).
3. **Offline mode** - Airplane mode. Verify graceful failure (no crash).

**Why these tests:** Catches blocking behavior that only appears under poor network conditions.

**Testing tools:**
- iOS Simulator: Settings → Developer → Network Link Conditioner
- Android Emulator: Settings → Network → Slow 3G
- Chrome DevTools: Network tab → Throttling

---

## Optimization Decisions

### Skeleton Screens Over Spinners

**Decision:** Use `skeletonizer` package to show layout preview during loading.

**Why:** Research shows 20-30% improvement in perceived speed vs generic spinners for waits <500ms.

**Implementation:** Wrap layout in `Skeletonizer()` with `Bone.text()` placeholders.

**Where:** See `lib/screens/home_screen.dart:_buildPapersSkeleton()`

**See:** `STATE-MANAGEMENT.md` → Async State Pattern for skeleton usage in state management.

### Navigate Then Load Pattern

**Decision:** Navigate immediately, show skeleton while loading (0ms blocking).

**Alternative:** Load before navigation (blocks 100-200ms, feels slow).

**Why:** Mobile UX guidelines (iOS HIG, Material Design) emphasize instant feedback. Blocking navigation feels unresponsive even at 100-200ms.

**Trade-off:** Screen must handle loading/error states vs simpler error handling in source screen.

**Conclusion:** Better perceived performance outweighs implementation complexity.

**See:** `STATE-MANAGEMENT.md` → Navigation with Async Data for full pattern comparison.

---

## Performance Metrics

### Target Improvements

| Metric | Before Optimization | After Optimization | Improvement |
|--------|---------------------|-------------------|-------------|
| Skeleton duration | 200ms | 0-50ms | **75-100%** |
| Blocking time | 0ms | 0ms | Maintained |
| Cache hit rate | 0% (cold) | ~90% (warm) | Significant |
| Perceived latency | 200ms | 0-50ms | Feels instant |

### Measurement Standards

- **UI thread time** - Use Timeline profiling, <10ms for any operation
- **Skeleton duration** - Time from navigation to data display, <100ms target
- **Frame rate** - Maintain 60fps during all operations
- **Memory usage** - Prefetch should use <500KB total

---

## Common Pitfalls

### ❌ Sequential execution (cascade operator)

```dart
// Looks parallel, actually sequential
ref..read(p1.future)..read(p2.future);
```

**Fix:** Use `Future.wait([...])` for true parallelism.

### ❌ Fire-and-forget without error handling

```dart
unawaited(Future.wait([...])); // Crashes on error
```

**Fix:** Always add `.catchError()` to background operations.

### ❌ Trusting local testing alone

Production Railway cold starts (1-2s) vs local backend (50ms) = different behavior.

**Fix:** Always test with production backend and network throttling.

### ❌ Prefetching before authentication

Wastes requests on login screen, may fail if API requires auth.

**Fix:** Prefetch in HomeScreen (after auth gate), not PaperLabApp.

### ❌ Forgetting cache retention

Prefetched data gets cleared by autoDispose ~1s later.

**Fix:** Use `cacheFor()` extension in provider build methods.

---

## Related Documentation

- **STATE-MANAGEMENT.md** - Data prefetching, async state patterns, cache retention
- **ARCHITECTURE.md** - Linter enforcement, layered architecture
- **DESIGN_SYSTEM.md** - Loading states, skeleton UI timing constants

---

## Implementation Files

- `lib/screens/home_screen.dart` - Prefetch implementation (initState + _prefetchData)
- `lib/utils/cache_extensions.dart` - Cache retention extension
- `lib/providers/attempts_provider.dart` - Applies cacheFor to providers
- `lib/providers/discovery_provider.dart` - Applies cacheFor to providers
- `analysis_options.yaml` - Linter rule configuration
