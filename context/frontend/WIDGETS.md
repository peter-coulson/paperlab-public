# Widget Composition

Widget organization patterns for PaperLab mobile app.

---

## Core Principle

**Composition over inheritance.** Build complex UIs from small, focused widgets.

**Benefits:**
- DRY: Styling defined once, used everywhere
- Testability: Test small widgets independently
- Maintainability: Change styling in one place
- Readability: Widget tree reflects UI structure

---

## When to Extract Widgets

### The 2+ Uses Rule

**Start inline. Extract to `widgets/` when code repeats 2+ times.**

**Why wait:**
- First use clarifies requirements
- Second use confirms pattern
- Premature abstraction creates wrong boundaries

### Extract Immediately When

- Design system specifies reusable component
- Component is obvious candidate for reuse (dialog, empty state)
- Component enforces consistency (list item container, header)

---

## When to Extract Utilities

**Screens should orchestrate, not transform.** Extract transformation logic to `utils/` when screens grow large.

### Extract When

- **Screen exceeds 250 lines** - Extract transformation/formatting logic to utils/, extract UI builders to widgets/
- **Data → Model transformation** - Building SelectionField lists, converting metadata to UI models
- **Formatting logic** - Date formatting, string manipulation, sorting
- **Validation logic** - Input validation with typed exceptions
- **Multiple UI states** - Loading, error, failed, success states → extract to state UI widgets

### Utils vs Widgets

**Utils:** Return data structures (models, primitives, collections)
**Widgets:** Return Widget tree

**Example:**
- `ExamDateUtils.formatExamDate()` returns `String` → utils/
- `PaperSelectionBuilder.buildFields()` returns `List<SelectionField>` → utils/
- `PaperListItem()` returns `Widget` → widgets/

**Where:** See `lib/screens/home_screen.dart` (560 lines) + `lib/utils/*_builder.dart` for refactoring example

---

## Widget Categories

| Category | Purpose | Widgets |
|----------|---------|---------|
| **Buttons** | Interactive actions (network-aware) | `PrimaryButton`, `SecondaryButton`, `AddButton` |
| **Form Inputs** | User input | `TextInput`, `Dropdown` |
| **List Items** | Scrollable lists (network-aware) | `ListItemContainer`, `PaperListItem`, `QuestionListItem` |
| **Feedback** | Status communication | `EmptyState`, `InfoBanner`, `DismissibleInfoBanner`, `InlineError`, `Dialog` |
| **State UI** | Marking flow states | `marking/*` (progress, error, failed states) |
| **Global** | App-wide overlays | `OfflineBanner` |
| **Layout** | Screen structure | `ScreenHeader`, `AppLogo`, `PhotoThumbnail`, `PhotoThumbnailGrid` |
| **Content** | Rich content display | `LatexText`, `MarkCriterionCard` |
| **Wrappers** | Composition helpers | `NetworkAwareInteractive`, `InteractiveEffect` |
| **Specialized** | Screen-specific | `question_results/*` (three-section architecture) |

---

## Organization Patterns

### Flat Structure

**Use for:** General-purpose widgets with no variants

**Location:** `lib/widgets/*.dart`

**Rationale:** Easy to find, clear scope, alphabetical organization

### Grouped Structure (Subdirectories)

**When to use:** 3+ related widgets, clear shared context, or name collision risk.

**Examples:** `lib/widgets/list_items/` (variants), `lib/widgets/question_results/` (related components), `lib/widgets/marking/` (state UI)

---

## Key Decisions

### ListItemContainer Pattern

**Why:** Single source of truth for list item styling. List item variants compose from `ListItemContainer`.

**Benefit:** Change list item styling in one place.

**Exception:** `PhotoListItem` (student work images) uses `InteractiveEffect` + `ClipRRect` instead of `ListItemContainer`. Student work images are content to review (not interactive list items), so visual chrome (border/shadow/background) would mislead users. Preserves tap feedback without full list item styling.

### List Item Indicator Typography

**Pattern:** Right-side indicators (grades, scores) use different typography based on data type.

| Indicator Type | Typography | Rationale |
|---------------|------------|-----------|
| **Grades** (single value: "8") | `h2` + `textSecondary` | Needs visual weight to stand alone |
| **Scores** (ratios: "3/5") | `body` + `textSecondary` | Fraction format is self-explanatory, secondary to title |

**Why the distinction:** A lone number ("8") at body size looks orphaned. The ratio format ("3/5") already has visual structure and reads well at smaller size.

**Where:** `PaperListItem` (grades), `QuestionListItem` (scores), `ResultListItem` (scores)

### NetworkAwareInteractive Pattern

**Why:** Single source of truth for connectivity-based interaction control. All interactive elements (buttons, list items) compose with `NetworkAwareInteractive` wrapper to enforce network requirements.

**How:**
- Wraps `InteractiveEffect` with connectivity checking
- Requires explicit `requiresNetwork: bool` parameter (no default)
- Auto-disables when offline if `requiresNetwork: true`
- Uses opacity + AbsorbPointer for disabled state

**Design decision - Required parameter:**
- NO default value for `requiresNetwork`
- Forces explicit declaration at every usage site
- Prevents accidental assumptions about network needs

**Benefit:**
- No duplicate connectivity checking in buttons/list items
- Explicit network requirements (code documents intent)
- Consistent offline behavior across all interactive elements

**Where:** See `lib/widgets/network_aware_interactive.dart`

**Related:** Works with `OfflineBanner` (global status) and `ConnectivityService` (connectivity checking)

### Const Constructors

**Why:** All reusable widgets use const constructors for performance. Flutter compiles const widgets once at build time.

**Enforced by linter:** `prefer_const_constructors`

### BuildContext Safety

**Rule:** Check `mounted` before using context after async operations.

**Enforced by linter:** `use_build_context_synchronously`

### StatelessWidget Default

**Use StatefulWidget only when:** Widget has internal state (focus, open/closed, animations).

**Default:** StatelessWidget for pure presentation.

### Persistent State in Widgets

**Pattern:** Widgets can own persistent state using SharedPreferences for user preferences that survive app restarts.

**When to use:**
- Dismissible tips/hints (one-time onboarding)
- Feature announcements (show once)
- User preferences scoped to widget (collapsed/expanded state)

**Why widget owns persistence:**
- Single responsibility (widget manages its visibility and persistence)
- Reusable across screens without coordination
- No screen-level state tracking needed

**Example:** `DismissibleInfoBanner` - Shows tip on first use, hides permanently after dismissal.

**Where:** See `lib/widgets/dismissible_info_banner.dart`

**Key decisions:**
- Widget returns `SizedBox.shrink()` when hidden (no layout impact)
- Graceful fallback on SharedPreferences errors (hide banner)
- Check `mounted` before setState after async operations

### Fullscreen Image Viewing

**Pattern:** Use `showImageViewerPager()` from `easy_image_viewer` package for all fullscreen image viewing (student work, uploaded photos).

**Key decisions:**
- **Swipe-down-to-dismiss** - Primary dismissal gesture (matches platform conventions)
- **Visible close button** - Package shows X button; use `Colors.white` for visibility on black background
- **Fire-and-forget navigation** - Wrap in `unawaited()` (required by `unawaited_futures` linter)

**Where:** See `lib/screens/question_upload_screen.dart` and `lib/widgets/question_results/your_work_section.dart`

**See `DESIGN_SYSTEM.md` for mobile gesture conventions.**

### Question Results Three-Section Architecture

**Pattern:** Separate question content from evaluation feedback to reduce cognitive load.

**Structure:**
1. **Question Section** - Complete question with all parts (no criteria)
2. **Results Section** - All evaluation results grouped by part with subtotals
3. **Your Work Section** - Full-width images with tap-to-enlarge

**Why separated:** Students can review "what was asked" and "how it was marked" independently without scroll-back. Mirrors physical exam paper structure.

**Widget composition:**
- `QuestionSection` uses `QuestionPartContentWidget` to display content blocks
- `MarkingFeedbackSection` uses `PartFeedbackGroup` which wraps `QuestionResultMarkCriterionCard`
- `YourWorkSection` displays full-width images with fullscreen viewer

**Where:** See `lib/widgets/question_results/` directory

---

## Global Widgets

**Widgets that appear app-wide, not scoped to specific screens.**

### OfflineBanner

**Proactive connectivity notification that appears when device is offline.**

**Behavior:**
- Listens to `ConnectivityService` stream via Riverpod
- Two-stage connectivity verification: device connectivity + HTTP health check
- Appears automatically when offline (no manual triggering)
- Disappears automatically when connectivity restored
- Non-dismissible (not user error, system state)
- Debounced to prevent flickering during brief disconnections

**Connectivity verification:**
1. **Stage 1:** Check device connectivity (WiFi/cellular) via `connectivity_plus`
2. **Stage 2:** Verify real internet access via HTTP health check to API
3. **Why:** Device may have WiFi but no internet (captive portals, local network only)

**Why global:** Users need to know network status across all screens, not just during upload. Proactive UX (show status) vs reactive (wait for errors).

**Where:** See `lib/widgets/offline_banner.dart` and `lib/services/connectivity_service.dart`

**See `API-INTEGRATION.md` for error handling on network failures.**

---

## Design Patterns Summary

- **Composition over inheritance** - Small widgets, not heavyweight subclasses
- **Extract at 2+ uses** - Start inline, extract when duplication is clear
- **Single responsibility** - Each widget has one purpose
- **Const optimization** - Const constructors for performance
- **Explicit dependencies** - Data via constructor parameters
- **Callback communication** - Child → parent via callbacks
- **Flat vs grouped** - Flat for general-purpose, grouped for variants
- **Global widgets** - App-wide overlays added once in main.dart
