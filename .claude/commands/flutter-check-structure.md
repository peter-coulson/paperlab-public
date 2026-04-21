You are conducting a **Flutter Structure & Quality Assessment** for the Flutter/Dart codebase.

Focus on genuine maintainability issues, not mechanical rule-following. Recognize idiomatic Flutter patterns.

## Objective

Assess code quality by identifying actual problems: hard-to-understand code, mixed concerns, genuine duplication, and excessive complexity. Metrics inform review but don't dictate action.

## Core Philosophy

**Start with comprehension, not metrics:**
1. Is this code hard to understand or maintain?
2. Does it mix multiple unrelated concerns?
3. Is there genuine duplication (not just similarity)?
4. Would extraction actually improve comprehension?

**Only flag as issue if genuine problem exists.**

---

## Quality Assessment Framework

### Primary Questions (Answer FIRST)

For each file >250 lines or method >50 lines:

**Cohesion:** Does all code relate to one clear purpose?
- ✅ High cohesion = File is fine regardless of size
- ❌ Mixed concerns = Review for extraction

**Organization:** Is code logically grouped with clear sections?
- ✅ Well-organized = Easy to navigate despite size
- ❌ Hard to navigate = Consider restructuring

**Complexity:** Are individual parts simple or complex?
- ✅ Simple, declarative = Verbose but acceptable
- ❌ Complex logic, nested conditionals = Extract

**Reusability:** Would extracted code actually be reused?
- ✅ Used 2+ places = Extract
- ❌ Screen-specific = Leave together

---

## Flutter Pattern Recognition

### Idiomatic Patterns (DO NOT FLAG)

**1. Progressive Widget Wrapping**
```dart
Widget build(BuildContext context) {
  Widget child = BaseWidget();
  if (condition1) child = Wrapper1(child: child);
  if (condition2) child = Wrapper2(child: child);
  return child;
}
```
✅ **This is Flutter best practice.** Clear transformation pipeline.

**2. Declarative UI Configuration**
```dart
InputDecoration(
  // 40+ lines of property configuration
  border: ..., focusedBorder: ..., errorBorder: ...
)
```
✅ **Flutter is verbose by design.** Don't flag single-use configuration.

**3. Efficient Single-Pass Algorithms**
```dart
List<InlineSpan> _parseMarkup(String text) {
  final spans = <InlineSpan>[];
  for (final match in regex.allMatches(text)) {
    // Process each match
  }
  return spans;
}
```
✅ **Efficient and clear.** Don't suggest multi-pass "stages".

### Anti-Patterns (DO FLAG)

❌ **Actual Duplication** - Same code repeated 3+ times with minor variations
❌ **Mixed Concerns** - Business logic + data access + UI in one method
❌ **Complex Nested Logic** - Deep conditionals, calculations in build methods
❌ **God Classes** - Screen doing navigation + data + selection + validation

---

## What to Check

### 1. File Size & Organization

**Metrics:** Files >250 lines trigger review (not automatic refactoring)

**Assess:**
- Is file cohesive (all code relates to one purpose)?
- Is code well-organized (clear sections, good naming)?
- Would extraction improve or just shuffle code?

**Action:**
- High cohesion + good organization = ✅ NO ACTION
- Mixed concerns + hard to navigate = 🔴 REFACTOR

### 2. Method Size & Complexity

**Metrics:** Methods >50 lines trigger review

**Assess:**
- Is it complex logic or just verbose structure?
- Does it do multiple unrelated things?
- Is it declarative UI or imperative logic?

**Action:**
- Declarative, clear structure = ✅ NO ACTION
- Complex logic, multiple responsibilities = 🔴 SPLIT

### 3. DRY Violations

**Look for:** Nearly identical code repeated 3+ times

**Real Duplication (EXTRACT):**
```dart
// 5 identical border configs, only color differs
OutlineInputBorder(borderRadius: ..., borderSide: BorderSide(color: COLOR))
```
→ Extract: `_buildBorder(Color color)`

**Natural Similarity (LEAVE):**
```dart
ListItem.paper(title: paperTitle, state: paperState)
ListItem.question(title: questionTitle, state: questionState)
```
→ Different constructors, different data - not duplication

### 4. Class Complexity

**Metrics:** Classes >15 methods trigger review

**Assess:**
- Does class have one clear responsibility?
- Are builder methods related (screen UI composition)?
- Would extraction reduce or just scatter code?

**Action:**
- Focused responsibility = ✅ NO ACTION (even if 20+ methods for complex UI)
- Multiple unrelated concerns = 🔴 EXTRACT

### 5. State Management

**Check:**
- State classes use `final` fields (immutability)
- No setState() during build
- Proper lifecycle (initState for setup, not build)
- No BuildContext in initState

### 6. Widget Composition

**Check:**
- Private `_buildX()` methods for complex widgets
- Named constructors for variants (not boolean flags)
- Widgets extracted at 2+ uses (not prematurely)

---

## Extraction Decision Framework

Before recommending extraction:

### Will This Be Reused?
- ✅ Used 2+ places → Extract
- ❌ Screen-specific → Don't extract

### Will This Improve Comprehension?
- ✅ Separates distinct concerns → Extract
- ❌ Just moves related code → Don't extract

### What's the Ceremony Cost?
- ✅ Clean: `const SkeletonWidget()` → Extract
- ❌ Ugly: `Utils.method(ref: ref, context: context, data: data)` → Don't extract

### Discoverability Impact?
- ✅ Reduces cognitive load → Extract
- ❌ Spreads related code → Don't extract

**Decision Matrix:**

| Reuse? | Clarity? | Clean? | → Action        |
|--------|----------|--------|-----------------|
| Yes    | Yes      | Yes    | ✅ EXTRACT      |
| Yes    | Yes      | No     | ⚠️ CONSIDER     |
| No     | Yes      | Yes    | ⚠️ WIDGET ONLY  |
| No     | No       | -      | ❌ DON'T EXTRACT|

---

## Report Structure

Generate: `.quality/flutter/structure-{YYYY-MM-DD-HHMMSS}.md`

### Format

```markdown
# Flutter Structure & Quality Assessment
**Run:** {TIMESTAMP}
**Commit:** {git hash}
**Files:** {count} Dart files, {total} lines
**Status:** {✅ Healthy | ⚠️ Issues Found | ❌ Critical}

## Summary
- Average file: {lines} lines
- Files >250 lines: {count} ({percentage}%)
- Methods >50 lines: {count}
- Overall Quality: {score}%

## 🔴 Genuine Problems [NEEDS ATTENTION]

(Only include if fails quality assessment AND metrics)

**1. [File] home_screen.dart (654 lines)**

**Assessment:**
- Cohesion: ❌ LOW (mixes UI + navigation + data + selection)
- Organization: ⚠️ FAIR (sections exist but scattered)
- Complexity: ❌ HIGH (43 methods, multiple responsibilities)

**Why this is a problem:**
- Navigation logic mixed with UI rendering
- Selection handling mixed with data operations
- Hard to find specific logic (must search 600+ lines)

**Why extraction helps:**
- Separate navigation from UI (clear boundaries)
- Extract reusable skeleton widgets (used in multiple tabs)
- Data operations in dedicated manager (single responsibility)

**Recommended:** Extract to 3 files (navigation mixin, data manager, skeleton widgets)

**2. [DRY] text_input.dart - Border Config Duplication**

**Evidence:**
```dart
// Repeated 5 times, only color differs:
OutlineInputBorder(borderRadius: ..., borderSide: BorderSide(color: X))
```

**Why extraction helps:** Changing border requires 5 edits → 1 edit

**Solution:** `OutlineInputBorder _buildBorder(Color color) { ... }`

## ✅ Pattern-Compliant Code (No Action Needed)

**1. latex_text.dart - Single-Pass Parsing (86 lines)**

**Assessment:**
- Efficient single-pass algorithm
- Clear structure: setup → process → return
- Easy to understand: match type → handle → add span

**Why no refactoring:** Current code is optimal. Splitting into "stages" would:
- Require two passes (worse performance)
- Add intermediate data structures (more complexity)
- Provide no comprehension benefit

**2. photo_thumbnail.dart - Progressive Wrapping (81 lines)**

**Assessment:**
- Uses Flutter best practice for conditional composition
- Clear transformation pipeline (top to bottom)
- Each transformation visible in sequence

**Why no refactoring:** This IS the idiomatic pattern. Extracting each wrapper to separate method adds noise without benefit.

## Detailed Analysis

### Widget Composition: {score}%
- Private builder methods: Widespread ✅
- Widget composition: Good extraction patterns ✅
- Named constructors: Proper variant handling ✅

### State Management: {score}%
- Immutable state: All final fields ✅
- Lifecycle usage: Proper initState/build separation ✅
- No violations found ✅

### Code Organization: {score}%
- Directory structure: Clean separation ✅
- File naming: Consistent snake_case ✅
- Files needing attention: {count}

### DRY Compliance: {score}%
- Genuine duplications found: {count}
- Generic list builder: Good pattern ✅

## Top Priorities

1. **home_screen.dart** - Extract navigation and data logic
   - Effort: 2-4 hours
   - Impact: HIGH (improves maintainability significantly)

2. **text_input.dart** - Extract border builder
   - Effort: 10 minutes
   - Impact: MEDIUM (eliminates real duplication)

## Quality Trend
{If previous reports exist}
- Last: {date} - Score: {old}% → {new}% ({change})

## Next Steps

{Contextual based on findings}
```

---

## Chat Output

After report:

```
{✅ | ⚠️ | ❌} Flutter Quality Assessment Complete

📄 Report: .quality/flutter/structure-{TIMESTAMP}.md
Files: {X} Dart files, {Y} lines
Quality Score: {percentage}%

🔴 Genuine Problems: {count}
✅ Pattern-Compliant: {count} (no action needed)

{Top 1-2 recommendations with effort estimates}
```

---

## Important Notes

- **Quality over metrics:** Files can be large if well-organized and cohesive
- **Recognize patterns:** Don't flag idiomatic Flutter (progressive wrapping, declarative UI)
- **Real duplication only:** Identical code repeated 3+times, not natural similarity
- **Context matters:** Screen with 20 builder methods for complex UI = OK
- **When to stop:** High cohesion + good organization = don't extract just for size
- **Extraction value:** Only extract if reusable OR clearly separates distinct concerns

**Principle:** Maintainable code, not small files.
