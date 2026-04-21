You are conducting a **Flutter Patterns & Best Practices Quality Check** for the Flutter/Dart codebase.

Think hard about Flutter-specific patterns, type safety, performance optimizations, and theming - this requires deep analysis of how Flutter idioms and best practices are applied throughout the code.

## Objective

Assess Flutter/Dart patterns, type safety, null safety, performance optimizations, theme usage, and linter compliance across the entire Flutter codebase.

## Scope

**All Flutter/Dart files:** `lib/**/*.dart` (excluding generated files)
**Report location:** `.quality/flutter/patterns-{TIMESTAMP}.md`

## What to Read

**Required:**
- `CLAUDE.md` - Flutter-Specific Principles and Implementation sections
- All Dart files in `lib/` directory
- `analysis_options.yaml` - For linter rules
- Previous patterns reports (if exist) for trend analysis

**DO NOT read:**
- Backend Python code (not relevant)
- context/ or specs/ (not needed for code quality)

## Quality Standards to Check

### 1. Flutter Performance & Optimization

**Assess:**
- Const constructors used wherever possible (enforced by linter)
- No expensive operations in build() methods
- ListView.builder() for long lists (not ListView with children)
- Proper widget splitting to avoid unnecessary rebuilds
- No synchronous I/O or heavy computation in build
- StatelessWidget preferred when no state needed

**Look for violations:**
- Missing `const` on static widgets → Add const (linter: prefer_const_constructors)
- Expensive calculations in build() → Cache or compute once outside build
- ListView(children: ...) for long lists → Use ListView.builder()
- Large widgets not split → Extract to reduce rebuild scope
- File I/O, network calls in build() → Move to lifecycle methods or state management
- StatefulWidget with no mutable state → Convert to StatelessWidget

**Example violation:**
```dart
// BAD: Expensive operation in build, no const
Widget build(BuildContext context) {
  final processedItems = items.map((item) =>
    expensiveTransform(item)).toList(); // Runs every rebuild!

  return Container(  // Should be const Container
    child: ListView(  // Should be ListView.builder for long lists
      children: processedItems.map((item) => ItemWidget(item)).toList(),
    ),
  );
}
```

**Example fix:**
```dart
// GOOD: Cached computation, const, builder
class MyWidget extends StatelessWidget {
  const MyWidget({super.key, required this.items});
  final List<Item> items;

  @override
  Widget build(BuildContext context) {
    return const SizedBox(  // const for static widget
      child: _ItemList(items: items),
    );
  }
}

class _ItemList extends StatelessWidget {
  // Computation done once when items change, not every build
  late final processedItems = items.map(expensiveTransform).toList();

  Widget build(BuildContext context) {
    return ListView.builder(  // Builder for performance
      itemCount: processedItems.length,
      itemBuilder: (context, index) => ItemWidget(processedItems[index]),
    );
  }
}
```

### 2. Type Safety & Null Safety

**Assess:**
- Proper use of nullable types (`Type?`)
- Minimal force unwrapping (!) - only with justification
- Null checks before accessing nullable values
- Named parameters with `required` where appropriate
- Generic types specified (`List<String>`, not `List`)
- Proper use of `late` keyword (only when necessary)
- No `dynamic` types where specific types exist

**Look for violations:**
- Unnecessary ! force unwrap → Use null checks or proper nullability
- Missing `required` on critical parameters → Add required keyword
- Unspecified generics (`List` not `List<User>`) → Add type parameter
- Overuse of `late` → Initialize properly in constructor
- `dynamic` instead of specific types → Use proper types
- Optional parameters that should be required

**Example violation:**
```dart
// BAD: Force unwrap, missing required, loose types
class UserWidget extends StatelessWidget {
  final String? name;
  final List items;  // No type parameter!

  UserWidget({this.name, this.items});  // Should be required

  Widget build(BuildContext context) {
    return Text(name!);  // Force unwrap!
  }
}
```

**Example fix:**
```dart
// GOOD: Proper nullability, required params, strict types
class UserWidget extends StatelessWidget {
  const UserWidget({
    super.key,
    required this.name,  // Required
    required this.items,
  });

  final String name;  // Non-nullable
  final List<Item> items;  // Specific type

  @override
  Widget build(BuildContext context) {
    return Text(name);  // No unwrap needed
  }
}
```

### 3. Flutter-Specific Patterns & Idioms

**Assess:**
- Named constructors for variants (`.fromJson()`, `.paper()`, `.question()`)
- Factory constructors for complex creation logic
- Extension methods for type-specific utilities
- Cascade notation (`..`) for fluent APIs
- Collection if/for in widget lists
- Spread operators (`...`) for conditional widgets
- Proper enum usage (not magic strings)
- Private class prefix (`_`) for internal widgets

**Look for violations:**
- Static methods instead of extensions → Create extension methods
- Long constructors without factory pattern → Use factory constructors
- Manual list building instead of collection if/for → Use modern syntax
- Magic strings instead of enums → Create enums
- Public widgets that are internal → Prefix with `_`
- No use of modern Dart features (cascade, spread)

**Example violation:**
```dart
// BAD: Manual list building, no enums, static utility methods
class MyWidget extends StatelessWidget {
  static String formatDate(DateTime date) { /* ... */ }  // Should be extension

  Widget build(BuildContext context) {
    final items = <Widget>[];
    items.add(Header());
    if (showContent) {  // Should use collection if
      items.add(Content());
    }
    items.add(Footer());

    return Column(
      children: items,
      status: 'active',  // Magic string - should be enum
    );
  }
}
```

**Example fix:**
```dart
// GOOD: Collection if, enum, extension
enum Status { active, inactive, pending }

extension DateTimeExtensions on DateTime {
  String format() { /* ... */ }
}

class MyWidget extends StatelessWidget {
  const MyWidget({super.key, required this.status});
  final Status status;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Header(),
        if (showContent) const Content(),  // Collection if
        const Footer(),
      ],
    );
  }
}
```

### 4. Magic Values & Theme Usage

**Assess:**
- No hardcoded colors (use theme constants)
- No hardcoded sizes/spacing (use spacing constants)
- No hardcoded text styles (use typography constants)
- Consistent use of theme system (AppColors, AppTypography, AppSpacing)
- No repeated string/number literals
- Theme defined in centralized location
- Responsive design (no arbitrary pixel values)

**Look for violations:**
- `Color(0xFF...)` hardcoded → Use AppColors.primary, etc.
- Hardcoded padding values (8, 12, 16) → Use AppSpacing.sm, md, lg
- Inline `TextStyle(...)` → Use AppTypography.h1, body, etc.
- Repeated color/size values → Extract to theme constants
- Fixed sizes without justification → Use responsive values or constants

**Example violation:**
```dart
// BAD: All hardcoded values
Widget build(BuildContext context) {
  return Container(
    padding: EdgeInsets.all(16),  // Magic number
    margin: EdgeInsets.only(top: 24),  // Magic number
    color: Color(0xFF2196F3),  // Hardcoded color
    child: Text(
      'Hello',
      style: TextStyle(  // Inline style
        fontSize: 18,
        fontWeight: FontWeight.w600,
        color: Color(0xFF212121),
      ),
    ),
  );
}
```

**Example fix:**
```dart
// GOOD: All values from theme
Widget build(BuildContext context) {
  return Container(
    padding: const EdgeInsets.all(AppSpacing.md),
    margin: const EdgeInsets.only(top: AppSpacing.lg),
    color: AppColors.primary,
    child: Text(
      'Hello',
      style: AppTypography.h3.copyWith(color: AppColors.textPrimary),
    ),
  );
}
```

### 5. Immutability & Data Models

**Assess:**
- Model classes use `final` fields
- copyWith() methods for state updates
- Proper immutability patterns
- No mutable collections exposed
- Value equality if needed (Equatable or override ==)

**Look for violations:**
- Non-final fields in model classes → Make final
- Missing copyWith() for models → Add copyWith()
- Mutable List/Map exposed → Return unmodifiable or copy
- Missing equality overrides when needed

**Example violation:**
```dart
// BAD: Mutable fields, no copyWith
class User {
  String name;  // Mutable!
  int age;      // Mutable!
  List<String> tags;  // Mutable collection!

  User({required this.name, required this.age, required this.tags});
}
```

**Example fix:**
```dart
// GOOD: Immutable, copyWith
class User {
  const User({
    required this.name,
    required this.age,
    required this.tags,
  });

  final String name;
  final int age;
  final List<String> tags;  // Treat as immutable

  User copyWith({String? name, int? age, List<String>? tags}) {
    return User(
      name: name ?? this.name,
      age: age ?? this.age,
      tags: tags ?? this.tags,
    );
  }
}
```

### 6. Linter Compliance

**Check critical lint rules from analysis_options.yaml:**

**Must-fix lints:**
- `prefer_const_constructors` - Use const where possible
- `prefer_const_declarations` - Use const for compile-time constants
- `use_build_context_synchronously` - Context safety (checked in safety check, but note here)
- `prefer_single_quotes` - Single quotes for strings
- `require_trailing_commas` - Trailing commas for formatting
- `prefer_final_fields` - Use final for immutability
- `prefer_final_locals` - Use final for local variables

**Count violations** by running analyzer or manually checking patterns

## Analysis Process

1. **Read all Dart files** in `lib/` directory
2. **Run analyzer** (via `mcp__dart__analyze_files`) to get linter violations
3. **Analyze each file** against all quality standards above
4. **Identify issues** by severity:
   - 🔴 **Critical**: Performance issues, type safety violations, major pattern violations
   - 🟡 **Warning**: Missing const, magic values, minor pattern issues
   - 🔵 **Info**: Style improvements, optional optimizations
5. **Calculate metrics** (see below)
6. **Generate report** with specific examples and fixes

## Metrics to Calculate

- Total Dart files analyzed
- Missing const constructors
- Force unwrap (!) count
- Expensive operations in build()
- Magic values (colors, sizes, strings)
- Linter violations by rule
- Type safety score
- Theme compliance score
- Pattern usage score
- Immutability score

## Output Format

Generate report at `.quality/flutter/patterns-{TIMESTAMP}.md`

Use format: `YYYY-MM-DD-HHMMSS` for timestamp

### Report Structure

```markdown
# Flutter Patterns & Best Practices Quality Check
**Run:** {TIMESTAMP}
**Commit:** {git hash}
**Files Analyzed:** {count} Dart files
**Total Lines:** {count}
**Status:** {✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues}

## Summary
- Dart files: {count}
- Performance score: {percentage}%
- Type safety score: {percentage}%
- Pattern usage score: {percentage}%
- Theme compliance: {percentage}%
- Linter compliance: {percentage}%
- **Overall Patterns Score: {percentage}%**

## 🔴 Critical Issues [MUST FIX]

1. **[Performance]** Expensive operation in build method
   Location: `lib/screens/results_screen.dart:45-50`
   Issue: Heavy computation running every rebuild
   Code:
   ```dart
   final results = items.map((item) =>
     expensiveCalculation(item)).toList(); // In build()!
   ```
   Fix:
   ```dart
   // Move to late final or state initialization
   late final results = items.map(expensiveCalculation).toList();
   ```
   Impact: Performance degradation, UI lag

2. **[Type Safety]** Unnecessary force unwrap
   Location: `lib/widgets/user_card.dart:23`
   Issue: Using ! without null check
   Code:
   ```dart
   Text(user!.name) // Force unwrap
   ```
   Fix:
   ```dart
   Text(user?.name ?? 'Unknown') // Safe access
   ```

## 🟡 Warnings [SHOULD FIX SOON]

{List of warnings with file:line, issue, suggested fix}

## 🔵 Info [CONSIDER]

{List of minor issues and suggestions}

## Detailed Analysis by Category

### ✅/⚠️/❌ Flutter Performance & Optimization

**Metrics:**
- Missing const constructors: {count} instances
- Expensive operations in build: {count}
- ListView without builder: {count}
- Unnecessary StatefulWidget: {count}
- Performance score: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Specific Issues:**
- `lib/screens/home_screen.dart:50` - Missing const on Container
- `lib/widgets/item_list.dart:30` - ListView should use builder
- `lib/screens/details.dart:40` - Heavy computation in build()

### ✅/⚠️/❌ Type Safety & Null Safety

**Metrics:**
- Force unwraps (!): {count}
- Missing required parameters: {count}
- Unspecified generics: {count}
- Overuse of late: {count}
- dynamic types: {count}
- Type safety score: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Specific Issues:**
{List violations with file:line}

### ✅/⚠️/❌ Flutter-Specific Patterns & Idioms

**Metrics:**
- Named constructors: {count} used
- Extension methods: {count} defined
- Collection if/for: {count} usages
- Enums vs magic strings: {count} enums, {count} magic strings
- Cascade notation: {count} usages
- Pattern adoption: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Good examples:**
- `lib/widgets/list_item.dart` - Excellent use of named constructors
- `lib/models/score.dart` - Good enum usage

**Needs improvement:**
- `lib/widgets/status_badge.dart:15` - Magic strings instead of enum
- `lib/screens/upload.dart:45` - Manual list building

### ✅/⚠️/❌ Magic Values & Theme Usage

**Metrics:**
- Hardcoded colors: {count}
- Hardcoded sizes/spacing: {count}
- Inline text styles: {count}
- Theme compliance: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Theme usage:**
- ✅ AppColors: Used consistently in {X} files
- ✅ AppTypography: Used consistently in {Y} files
- ⚠️ AppSpacing: Not used in {Z} files

**Specific Issues:**
- `lib/widgets/card.dart:20` - Color(0xFF...) instead of AppColors
- `lib/screens/home.dart:35` - Hardcoded padding values

### ✅/⚠️/❌ Immutability & Data Models

**Metrics:**
- Model classes: {count}
- Mutable fields: {count} violations
- copyWith methods: {count} implemented
- Immutability score: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Specific Issues:**
{List violations with file:line}

### ✅/⚠️/❌ Linter Compliance

**Linter violations found:**
- prefer_const_constructors: {count}
- prefer_single_quotes: {count}
- require_trailing_commas: {count}
- prefer_final_fields: {count}
- prefer_final_locals: {count}
- Other rules: {count}

**Linter compliance: {percentage}%**

**Auto-fixable:** {count} violations
**Manual fix required:** {count} violations

Run `mcp__dart__analyze_files` to see detailed linter output.

## Top Files Needing Attention

1. `{file}` - {issue count} issues ({critical}/{warning}/{info})
   - Primary issues: {list main issues}

2. `{file}` - {issue count} issues
   - Primary issues: {list main issues}

3. `{file}` - {issue count} issues
   - Primary issues: {list main issues}

## Refactoring Recommendations

### High Priority (Critical Issues)
1. **Cache expensive computation in results_screen.dart**
   - Move expensive calculation out of build() method
   - Use late final or state initialization
   - Estimated effort: 15 minutes

2. **Fix force unwraps in user_card.dart**
   - Replace ! with null checks or default values
   - Improves crash safety
   - Estimated effort: 10 minutes

### Medium Priority (Warnings)
1. **Add const constructors throughout codebase**
   - {X} missing const - auto-fixable with IDE
   - Improves performance
   - Estimated effort: 20 minutes

2. **Replace magic strings with enums in status_badge.dart**
   - Create Status enum
   - Improves type safety
   - Estimated effort: 20 minutes

### Low Priority (Improvements)
1. {Recommendation with file and estimated effort}
2. {Recommendation with file and estimated effort}

## Quick Wins

**Auto-fixable with tools:**
- Run IDE "Add const" fix: ~{X} instances
- Run IDE "Add trailing commas": ~{Y} instances
- Run IDE "Use single quotes": ~{Z} instances

Estimated total time: {minutes} minutes

## Quality Trend

{If previous patterns reports exist}
- Last check: {date}
- Patterns score: {old}% → {new}% ({change})
- Issues: {old count} → {new count} ({change})
- Linter compliance: {old}% → {new}% ({change})
- Const usage: {old count} → {new count} constructors

## Next Steps

{If critical issues:}
⚠️ **Action Required:** Fix {X} critical performance/safety issues before proceeding.

{If warnings only:}
✅ Patterns are good. Address {Y} warnings for better code quality.
💡 Quick wins available: Run auto-fixes to resolve {Z} linter issues in ~{minutes} minutes.

{If all clear:}
✅ Excellent Flutter patterns! Code follows best practices consistently.

---
*Companion checks: /flutter-check-structure (widget architecture), /flutter-check-safety (safety & robustness)*
*Run `mcp__dart__analyze_files` to see detailed linter violations*
```

## Chat Output

After writing the report, display concise summary in chat:

```
{✅ | ⚠️ | ❌} Flutter Patterns Check Complete

📄 Report: .quality/flutter/patterns-{TIMESTAMP}.md
Files: {X} Dart files
Patterns Score: {percentage}%

{If critical issues:}
🔴 Critical Issues: {count}
1. {Brief description} - {file:line}
2. {Brief description} - {file:line}

{If warnings:}
🟡 Warnings: {count}

Scores:
- Performance: {percentage}%
- Type safety: {percentage}%
- Theme compliance: {percentage}%
- Linter compliance: {percentage}%

Quick Wins Available:
- {X} auto-fixable linter issues (~{minutes} min)

{Top 1-2 recommendations}

Run `mcp__dart__analyze_files` for detailed linter output.
```

## Important Notes

- **Check ALL Dart files** - Comprehensive analysis
- **Run analyzer** - Use MCP tool for linter violations
- **Be specific** - Always include file:line references
- **Show code** - Include violations AND fixes
- **Prioritize performance** - Performance issues are critical
- **Calculate real metrics** - Count actual occurrences
- **Identify quick wins** - Auto-fixable issues save time
- **Be constructive** - Focus on improvements, not criticism
