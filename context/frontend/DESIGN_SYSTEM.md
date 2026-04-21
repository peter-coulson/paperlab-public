# UI Design System

Visual design decisions for PaperLab mobile app.

**See [`BRANDING.md`](../shared/BRANDING.md) for brand values and UX principles.**

---

## Design Philosophy

**Balance:**
- **Calm focus** - Reduce exam-related stress
- **Professional approachability** - Serious without intimidating
- **Trust** - Dependable through consistent execution
- **Analytical precision** - Complex feedback must be instantly scannable
- **Intelligence** - Sophisticated without overwhelming
- **Modern clarity** - Visual language students recognize

**Mobile UX Conventions:**
- **Follow platform patterns** - Use gestures students already know (swipe-down to dismiss fullscreen views)
- **Why:** Students expect mobile apps to behave like Instagram/Photos.app/WhatsApp. Diverging creates friction and feels dated.
- **Example:** Fullscreen image viewer uses swipe-down-to-dismiss as primary gesture (see `WIDGETS.md`)

---

## Color Palette

**Decision:** Soft Indigo

**Why Indigo:**
- **Trust (blue foundation)** - Universally associated with dependability
- **Calm (muted saturation)** - Reduces stress, recedes for content
- **Intelligence (sophisticated neutrality)** - Doesn't compete with math expressions
- **Approachability** - Students recognize from tools they respect (Notion, Discord)
- **Clear hierarchy** - Indigo primary + Amber error = instant distinction

**Implementation:** `lib/theme/app_colors.dart`

| Role | Color | Use |
|------|-------|-----|
| Primary | Soft Indigo #667EEA | Buttons, logo, active states |
| Success | Emerald #10B981 | Correct answers, positive feedback |
| Error | Amber #F59E0B | Incorrect answers, attention needed |
| Destructive | Red #EF4444 | Delete, remove (permanent actions only) |
| Background | White #FFFFFF | Main background |
| Text Primary | Near-black #111827 | Body text, headings |

---

## Typography

**Decision:** IBM Plex Serif (headers) + Inter (body/UI)

**Why this pairing:**
- **IBM Plex Serif** - Professional authority without corporate coldness, excellent screen readability
- **Inter** - Maximum clarity for dense content, optimized for math expressions and feedback
- **Both open-source** (SIL OFL 1.1)
- **Screen optimized** - Clear letterforms at mobile sizes

**Implementation:** `lib/theme/app_typography.dart`

### Typography Scale (9 styles)

**Simplification principle:** Minimal, purposeful hierarchy. Each size has exactly one clear purpose. No duplicate sizes.

**Why simplified (15→9 styles):**
- Eliminates confusion (bodyLarge 18px duplicated h3 18px)
- Clear hierarchy without gaps (h1→h2, not h1→h3)
- Semantic naming (pillBadgeText more descriptive than badgeText)
- Follows industry standards (1.3-1.6x scaling ratio for headings, 16px minimum body)

| Style | Font | Size | Weight | Use |
|-------|------|------|--------|-----|
| **Headers** |
| logo | Plex Serif | 46px | 600 | Brand only |
| h1 | Plex Serif | 28px | 600 | Screen titles (ScreenHeader) |
| h2 | Plex Serif | 20px | 500 | List/card/dialog titles |
| **Body** |
| body | Inter | 16px | 400 | Mark schemes, feedback, UI text |
| bodySmall | Inter | 14px | 400 | Secondary text (not ScreenHeader) |
| headerSubtitle | Inter | 16px | 400 | ScreenHeader subtitle only |
| **UI** |
| sectionTitleStyle | Inter | 16px | 500 | Section headers (uppercase) |
| label | Inter | 14px | 500 | Form labels, metadata |
| caption | Inter | 12px | 400 | Hints, small metadata |
| pillBadgeText | Inter | 12px | 500 | Pill badges (status indicators) |
| scoreBadgeText | Inter | 14px | 500 | Score badges (header badges) |

**Base size:** 16px for optimal mobile readability of dense educational content.

**Scaling:** H1 (28px) is 1.75× body (16px). H2 (20px) is 1.25× body. Both within industry standard 1.3-1.6× ratio for clear hierarchy.

**Usage pattern:**
- **H1** - One per screen (ScreenHeader title only)
- **H2** - Multiple per screen (list items, card titles, dialog titles)
- **body** - Default for all content text
- **bodySmall** - Secondary/supporting text (subtitles, metadata)

---

## Spacing System

**Foundation tokens:**

| Token | Value | Use |
|-------|-------|-----|
| xs | 4px | Tight spacing within components |
| sm | 8px | Related elements |
| md | 16px | Default between elements |
| lg | 24px | Sections within screen |
| xl | 32px | Major sections |
| xxl | 48px | Screen padding |

**Semantic tokens:**

| Token | Value | Use |
|-------|-------|-----|
| screenHorizontalMargin | 24px | Standard left/right screen margin (ScreenHeader, ListView padding, content wrappers) |

**Pattern:** Use semantic tokens (e.g., `screenHorizontalMargin`) instead of foundation tokens (e.g., `lg`) when spacing has a consistent purpose across the app. This creates a single source of truth and prevents drift.

---

## Semantic Color Usage

**Each color has ONE meaning. Never use outside its purpose:**

| Color | Meaning | Use For | Emotion |
|-------|---------|---------|---------|
| Success (Emerald) | Correct, achievement | Correct answers, marks awarded | Encouraging |
| Error (Amber) | Incorrect, fixable | Wrong answers, validation | Gentle attention |
| Destructive (Red) | Permanent removal | Delete buttons only | Serious consequence |

**Note:** Red is ONLY for destructive actions, not errors. This avoids anxiety while maintaining clear warnings.

---

## Key Specifications

### Buttons
- Primary: Indigo background, white text, 12px/24px padding, 8px radius
- Secondary: Light indigo background or transparent with border
- Destructive: Red background (delete/remove actions only)

### Cards
- White background, 1px border, 12px radius, 24px padding

### Feedback States
- **Correct:** 4px left border success, ✓ icon
- **Incorrect:** 4px left border error, ⓘ icon
- **Partial:** 4px left border primary light

### State Badges
- **Draft:** Gray background, neutral indicator
- **Marking:** Amber background with opacity, attention indicator
- **Complete:** No badge (clean view)

### Accessibility
- Minimum touch target: 44x44px
- WCAG AA contrast
- Never rely on color alone (icons supplement colors)

---

## Subject-Agnostic Design

**Critical:** Design must work for all subjects without refactors.

**Color system scales:**
- Success/Error/Destructive work universally across subjects
- Primary (indigo) is brand-independent of content
- **No subject-specific colors**

**Typography scales:**
- Inter handles math, essays, equations, extended writing
- IBM Plex Serif provides consistent structure
- **Content differences in text, not fonts**

**Layout patterns are universal:**
- Question display, feedback cards, mark schemes, progress tracking
- Same patterns for all subjects with different content

---

## Constants Organization

**Theme constants follow DRY principle - no hardcoded values.**

### Timing Constants

**Location:** `lib/theme/app_durations.dart`

```dart
class AppDurations {
  static const Duration undoToast = Duration(seconds: 5);
  static const Duration standardToast = Duration(seconds: 3);
  static const Duration errorToast = Duration(seconds: 4);
}
```

**Why:** Consistent timing across app. Single source of truth for UX timing decisions.

### UI Text Constants

**Location:** `lib/theme/app_strings.dart`

```dart
class AppStrings {
  static const String paperDeleted = 'Paper deleted';
  static const String questionDeleted = 'Question deleted';
  static const String undo = 'Undo';
  static const String retry = 'Retry';
}
```

**Why:**
- DRY: No duplicate strings across screens
- Easy to update copy globally
- Supports future i18n

**Rule:** If string appears in UI more than once, extract to AppStrings.

---

## Error Messaging

**User-friendly error messages follow strict UX guidelines.**

### Principles

**Never show technical jargon:**
- ❌ "SocketException: Connection refused"
- ❌ "DioException: Failed to fetch"
- ✅ "No internet connection. Please check your WiFi or cellular data and try again."

**Always provide actionable guidance:**
- Every error message tells user what to do next
- Examples: "try again", "check your connection", "sign in again"

**Match severity to UI treatment:**
- Network errors → Amber background (fixable, temporary)
- Destructive actions → Red background (permanent consequence)
- Validation errors → Inline text (guidance, not alarm)

### Error Message Mapping

**Centralized mapper converts exceptions to user messages:**

```dart
final message = ErrorMessages.getUserMessage(exception);
// Returns user-friendly string for any exception type
```

**Examples:**
- `NoConnectivityException` → "No internet connection. Please check your WiFi..."
- `RequestTimeoutException` → "Request timed out. Please check your connection..."
- `ApiException(404)` → "Resource not found. Please try again."
- `ApiException(500)` → "Server error. Please try again later."

**Where:** See `lib/utils/error_messages.dart`

### Error Display Patterns

**SnackBar for network/API errors:**
```dart
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(
    content: Text(ErrorMessages.getUserMessage(e)),
    backgroundColor: AppColors.error,  // Amber
    duration: AppDurations.errorToast, // 4 seconds
  ),
);
```

**Inline validation for form errors:**
- Shown below input field
- No background color (subtle guidance)
- Examples: "Email required", "Password too short"

**Dialog for critical errors:**
- Rare (only when action required)
- Example: "Session expired. Please sign in again."

**See `API-INTEGRATION.md` for exception types.**

---

## Implementation

**Location:** `lib/theme/`
- `app_colors.dart` - Color constants
- `app_typography.dart` - Typography styles
- `app_spacing.dart` - Spacing constants
- `app_durations.dart` - Timing constants
- `app_strings.dart` - UI text constants

**Utilities:** `lib/utils/`
- `error_messages.dart` - Exception → user-friendly message mapping

**Widget library:** `lib/widgets/` - Reusable components implementing this system
