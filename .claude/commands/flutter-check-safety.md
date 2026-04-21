You are conducting a **Flutter Safety & Robustness Quality Check** for the Flutter/Dart codebase.

Think hard about async safety, resource management, error handling, UI/logic separation, and layout robustness - this requires deep analysis of how the Flutter code handles edge cases, manages resources, and separates concerns.

## Objective

Assess BuildContext safety, resource lifecycle management, error handling, UI/business logic separation, responsive layout practices, and overall code robustness across the entire Flutter codebase.

## Scope

**All Flutter/Dart files:** `lib/**/*.dart` (excluding generated files)
**Report location:** `.quality/flutter/safety-{TIMESTAMP}.md`

## What to Read

**Required:**
- `CLAUDE.md` - Flutter-Specific Principles and Implementation sections
- All Dart files in `lib/` directory
- Previous safety reports (if exist) for trend analysis

**DO NOT read:**
- Backend Python code (not relevant)
- context/ or specs/ (not needed for code quality)

## Quality Standards to Check

### 1. BuildContext Safety & Async Operations

**Assess:**
- No BuildContext usage after async gaps without `mounted` check
- Context not stored in State class fields
- Proper context usage for Theme, MediaQuery, Navigator
- No context access in initState (use didChangeDependencies)
- Async operations check widget is still mounted before using context
- No context usage in background callbacks without guards

**Look for violations:**
- Using context after `await` without `mounted` check → Add if (!mounted) return;
- Storing context in State fields → Use context only in build or pass explicitly
- Navigator.of(context) after async → Check mounted first
- Theme.of(context) in initState → Move to didChangeDependencies
- Context used in Timer/Future callbacks → Add mounted checks

**Example violation:**
```dart
// BAD: Context after async without mounted check
class MyWidget extends StatefulWidget {
  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  void _saveData() async {
    await api.saveData(data);
    Navigator.pop(context); // UNSAFE! Context might be invalid
    ScaffoldMessenger.of(context).showSnackBar(snackBar); // UNSAFE!
  }

  @override
  void initState() {
    super.initState();
    final theme = Theme.of(context); // WRONG! Can't use context here
  }
}
```

**Example fix:**
```dart
// GOOD: Mounted checks and proper context usage
class _MyWidgetState extends State<MyWidget> {
  void _saveData() async {
    await api.saveData(data);
    if (!mounted) return; // Check before using context
    Navigator.pop(context);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(snackBar);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final theme = Theme.of(context); // Correct place for context access
  }
}
```

### 2. Resource Management & Lifecycle

**Assess:**
- Controllers disposed properly (TextEditingController, AnimationController, etc.)
- Stream subscriptions cancelled
- Listeners removed
- Timers cancelled
- dispose() implemented when resources allocated
- No memory leaks from unclosed resources
- initState properly paired with dispose

**Look for violations:**
- TextEditingController created but never disposed → Add dispose()
- AnimationController without dispose → Add dispose()
- StreamSubscription not cancelled → Cancel in dispose()
- addListener() without removeListener() → Remove in dispose()
- Timer started but not cancelled → Cancel in dispose()

**Example violation:**
```dart
// BAD: Resources never disposed
class MyForm extends StatefulWidget {
  @override
  State<MyForm> createState() => _MyFormState();
}

class _MyFormState extends State<MyForm> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  late AnimationController _animController;
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(vsync: this);
    _subscription = stream.listen((data) { /* ... */ });
  }

  // Missing dispose()! Memory leak!

  @override
  Widget build(BuildContext context) {
    return TextField(controller: _nameController);
  }
}
```

**Example fix:**
```dart
// GOOD: All resources disposed
class _MyFormState extends State<MyForm> with SingleTickerProviderStateMixin {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  late AnimationController _animController;
  late StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(vsync: this);
    _subscription = stream.listen((data) { /* ... */ });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _animController.dispose();
    _subscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TextField(controller: _nameController);
  }
}
```

### 3. Error Handling & Edge Cases

**Assess:**
- FutureBuilder/StreamBuilder handle all states (loading, error, data)
- Null checks before accessing nullable values
- Empty collection states handled
- Image loading errors handled
- Proper error widgets/messages shown to user
- No silent failures in async operations
- Try-catch in appropriate places

**Look for violations:**
- FutureBuilder without error handling → Add error builder
- No loading states shown → Add loading indicator
- No empty list handling → Add empty state widget
- Null access without checks → Add null checks
- Silent try-catch (empty catch block) → Log or show error
- Image.network without errorBuilder → Add error handling

**Example violation:**
```dart
// BAD: No error/loading/empty handling
Widget build(BuildContext context) {
  return FutureBuilder<List<User>>(
    future: fetchUsers(),
    builder: (context, snapshot) {
      return ListView(  // What if loading? Error? Empty?
        children: snapshot.data!.map((user) =>  // Crash if null!
          UserTile(user: user),
        ).toList(),
      );
    },
  );
}
```

**Example fix:**
```dart
// GOOD: All states handled
Widget build(BuildContext context) {
  return FutureBuilder<List<User>>(
    future: fetchUsers(),
    builder: (context, snapshot) {
      // Loading state
      if (snapshot.connectionState == ConnectionState.waiting) {
        return const Center(child: CircularProgressIndicator());
      }

      // Error state
      if (snapshot.hasError) {
        return Center(
          child: Text('Error: ${snapshot.error}'),
        );
      }

      // Empty state
      final users = snapshot.data ?? [];
      if (users.isEmpty) {
        return const EmptyState(message: 'No users found');
      }

      // Success state
      return ListView.builder(
        itemCount: users.length,
        itemBuilder: (context, index) => UserTile(user: users[index]),
      );
    },
  );
}
```

### 4. UI & Business Logic Separation

**Assess:**
- No business logic in build() methods
- No API calls directly in widgets
- No complex data processing in widgets
- Logic extracted to ViewModels/BLoCs/Controllers/Services
- Widgets are "thin" - only UI composition
- Data transformations done outside widgets
- Clear separation of concerns

**Look for violations:**
- API calls in widgets → Move to repository/service
- Complex calculations in build() → Extract to ViewModel/method
- Data validation in widgets → Move to model/service
- Business rules in widget event handlers → Extract to business logic layer
- Tight coupling to data sources → Use repositories

**Example violation:**
```dart
// BAD: Business logic, API calls, validation in widget
class UserProfile extends StatefulWidget {
  @override
  State<UserProfile> createState() => _UserProfileState();
}

class _UserProfileState extends State<UserProfile> {
  @override
  Widget build(BuildContext context) {
    // API call in widget!
    final userData = http.get('https://api.example.com/user');

    // Business logic in widget!
    final isValid = userData.email.contains('@') &&
                    userData.age >= 18 &&
                    userData.name.length > 2;

    // Complex transformation in widget!
    final displayData = userData.purchases
        .where((p) => p.date.isAfter(DateTime.now().subtract(Duration(days: 30))))
        .map((p) => PurchaseDisplay(
          title: p.item.toUpperCase(),
          price: '\$${(p.amount / 100).toStringAsFixed(2)}',
        ))
        .toList();

    return ListView(children: displayData.map((d) => Text(d.title)).toList());
  }
}
```

**Example fix:**
```dart
// GOOD: Logic in ViewModel, widget is thin
class UserProfileViewModel {
  final UserRepository _repo;

  Future<UserData> getUserData() => _repo.fetchUser();

  bool isValidUser(UserData user) {
    return user.email.contains('@') &&
           user.age >= 18 &&
           user.name.length > 2;
  }

  List<PurchaseDisplay> getRecentPurchases(UserData user) {
    return user.purchases
        .where((p) => p.date.isAfter(DateTime.now().subtract(Duration(days: 30))))
        .map((p) => PurchaseDisplay(
          title: p.item.toUpperCase(),
          price: '\$${(p.amount / 100).toStringAsFixed(2)}',
        ))
        .toList();
  }
}

class UserProfile extends StatelessWidget {
  const UserProfile({super.key, required this.viewModel});
  final UserProfileViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    // Widget only handles UI
    return FutureBuilder<UserData>(
      future: viewModel.getUserData(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const LoadingWidget();
        final purchases = viewModel.getRecentPurchases(snapshot.data!);
        return ListView.builder(
          itemCount: purchases.length,
          itemBuilder: (context, index) => PurchaseTile(purchases[index]),
        );
      },
    );
  }
}
```

### 5. Responsiveness & Layout Constraints

**Assess:**
- No fixed widths without justification
- MediaQuery used for responsive sizing when needed
- LayoutBuilder for adaptive layouts
- Flexible/Expanded used appropriately
- SafeArea for device notches/insets
- Text overflow handled (ellipsis, wrapping)
- Constraints properly understood and handled
- No RenderBox overflow errors

**Look for violations:**
- Fixed width that breaks on small screens → Use flexible width or MediaQuery
- No SafeArea for edge content → Add SafeArea
- Text without maxLines or overflow handling → Add ellipsis or wrap
- Unconstrained box errors → Add constraints
- No responsive design for different screen sizes
- Hardcoded sizes that don't scale

**Example violation:**
```dart
// BAD: Fixed sizes, no SafeArea, text overflow
Widget build(BuildContext context) {
  return Column(
    children: [
      // Fixed width - breaks on small screens!
      Container(
        width: 500,
        child: Text(
          'Very long text that will definitely overflow...',
          // No overflow handling!
        ),
      ),
      // Content at screen edge - no SafeArea
      Positioned(top: 0, child: AppBar()),
    ],
  );
}
```

**Example fix:**
```dart
// GOOD: Responsive, SafeArea, overflow handled
Widget build(BuildContext context) {
  final screenWidth = MediaQuery.of(context).size.width;

  return SafeArea(  // Handle notches/insets
    child: Column(
      children: [
        Container(
          width: screenWidth * 0.9,  // Responsive width
          constraints: const BoxConstraints(maxWidth: 500),  // Max width for large screens
          child: Text(
            'Very long text that will definitely overflow...',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,  // Handle overflow
          ),
        ),
      ],
    ),
  );
}
```

### 6. Navigation Safety

**Assess:**
- Navigation calls properly handle async gaps
- No navigation during build
- Proper error handling for navigation
- Named routes used consistently (if applicable)
- Navigation stack managed correctly
- Back button handling where needed

**Look for violations:**
- Navigator.push during build → Move to callback
- Navigation after async without mounted check
- No error handling for failed navigation

## Analysis Process

1. **Read all Dart files** in `lib/` directory
2. **Analyze each file** against all quality standards above
3. **Identify issues** by severity:
   - 🔴 **Critical**: Crash risks, memory leaks, data loss risks
   - 🟡 **Warning**: Missing error handling, poor separation, layout issues
   - 🔵 **Info**: Minor improvements, edge case handling
4. **Calculate metrics** (see below)
5. **Generate report** with specific examples and fixes

## Metrics to Calculate

- Context usage after async without mounted: {count}
- Resources without dispose: {count}
- FutureBuilder without error handling: {count}
- Business logic in widgets: {count}
- Fixed widths/heights: {count}
- Missing SafeArea: {count}
- Null access risks: {count}
- BuildContext safety score
- Resource management score
- Error handling score
- Logic separation score
- Layout robustness score

## Output Format

Generate report at `.quality/flutter/safety-{TIMESTAMP}.md`

Use format: `YYYY-MM-DD-HHMMSS` for timestamp

### Report Structure

```markdown
# Flutter Safety & Robustness Quality Check
**Run:** {TIMESTAMP}
**Commit:** {git hash}
**Files Analyzed:** {count} Dart files
**Total Lines:** {count}
**Status:** {✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues}

## Summary
- Dart files: {count}
- BuildContext safety: {percentage}%
- Resource management: {percentage}%
- Error handling: {percentage}%
- Logic separation: {percentage}%
- Layout robustness: {percentage}%
- **Overall Safety Score: {percentage}%**

## 🔴 Critical Issues [MUST FIX]

1. **[BuildContext Safety]** Context used after async without mounted check
   Location: `lib/screens/login_screen.dart:45-48`
   Issue: Navigator.pop(context) called after await without checking mounted
   Code:
   ```dart
   void _login() async {
     await authService.login(email, password);
     Navigator.pop(context); // CRASH RISK!
   }
   ```
   Fix:
   ```dart
   void _login() async {
     await authService.login(email, password);
     if (!mounted) return;
     Navigator.pop(context);
   }
   ```
   Risk: App crash if widget disposed during async operation

2. **[Resource Management]** TextEditingController never disposed
   Location: `lib/screens/form_screen.dart:15`
   Issue: Controllers created but dispose() not implemented
   Impact: Memory leak
   Fix: Implement dispose() method to clean up controllers

## 🟡 Warnings [SHOULD FIX SOON]

{List of warnings with file:line, issue, suggested fix}

## 🔵 Info [CONSIDER]

{List of minor issues and suggestions}

## Detailed Analysis by Category

### ✅/⚠️/❌ BuildContext Safety & Async Operations

**Metrics:**
- Context after async without mounted: {count} violations
- Context stored in State: {count} violations
- Context in initState: {count} violations
- Unsafe Navigator calls: {count}
- BuildContext safety score: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Critical violations:**
- `lib/screens/login.dart:45` - Navigator after await without mounted check
- `lib/screens/upload.dart:60` - ScaffoldMessenger after async gap

**Context usage patterns:**
- ✅ Proper mounted checks: {count} instances
- ⚠️ Missing mounted checks: {count} instances
- ⚠️ Context in wrong lifecycle: {count} instances

### ✅/⚠️/❌ Resource Management & Lifecycle

**Metrics:**
- Controllers without dispose: {count}
- Stream subscriptions not cancelled: {count}
- Listeners not removed: {count}
- Timers not cancelled: {count}
- Resource management score: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Resource leaks found:**
- `lib/screens/form.dart` - {X} controllers not disposed
- `lib/widgets/animated_widget.dart` - AnimationController leak
- `lib/screens/stream_screen.dart` - StreamSubscription not cancelled

**Good practices observed:**
- ✅ Proper dispose in {X} files
- ✅ Resource cleanup in {Y} widgets

### ✅/⚠️/❌ Error Handling & Edge Cases

**Metrics:**
- FutureBuilder without error handling: {count}
- StreamBuilder without error handling: {count}
- Missing loading states: {count}
- No empty state handling: {count}
- Null access risks: {count}
- Silent failures: {count}
- Error handling score: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Specific issues:**
- `lib/screens/users.dart:30` - FutureBuilder missing error builder
- `lib/widgets/image_card.dart:20` - Image.network without errorBuilder
- `lib/screens/list.dart:45` - No empty list handling

**State coverage:**
- Loading states: {count handled} / {count total}
- Error states: {count handled} / {count total}
- Empty states: {count handled} / {count total}

### ✅/⚠️/❌ UI & Business Logic Separation

**Metrics:**
- API calls in widgets: {count}
- Business logic in build(): {count}
- Complex calculations in widgets: {count}
- Proper separation: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Violations:**
- `lib/screens/profile.dart:50-80` - Heavy business logic in widget
- `lib/widgets/calculator.dart:30` - Complex calculations in build()
- `lib/screens/checkout.dart:40` - Direct API calls

**Good examples:**
- ✅ `lib/screens/home_screen.dart` - Clean separation with ViewModel pattern
- ✅ `lib/widgets/list_item.dart` - Pure UI widget

### ✅/⚠️/❌ Responsiveness & Layout Constraints

**Metrics:**
- Fixed widths/heights: {count}
- MediaQuery usage: {count}
- SafeArea usage: {percentage}% where needed
- Text overflow handling: {percentage}%
- Layout constraint issues: {count}
- Responsiveness score: {percentage}%

**Assessment:** {Overall assessment paragraph}

**Specific issues:**
- `lib/widgets/card.dart:25` - Fixed width 400px (breaks on mobile)
- `lib/screens/details.dart:15` - No SafeArea for top content
- `lib/widgets/title.dart:10` - Text overflow not handled

**Responsive design:**
- ✅ Proper use of Flexible/Expanded: {count} instances
- ⚠️ Fixed dimensions: {count} instances
- ✅ SafeArea used: {count} / {needed} places

### ✅/⚠️/❌ Navigation Safety

**Metrics:**
- Unsafe navigation calls: {count}
- Navigation during build: {count}
- Proper navigation handling: {percentage}%

**Assessment:** {Overall assessment paragraph}

## Top Files Needing Attention

1. `{file}` - {issue count} issues ({critical}/{warning}/{info})
   - Primary risks: {list main issues}
   - Estimated fix time: {minutes} minutes

2. `{file}` - {issue count} issues
   - Primary risks: {list main issues}

3. `{file}` - {issue count} issues
   - Primary risks: {list main issues}

## Critical Risk Summary

**Crash Risks:** {count}
- Context after async without mounted: {count}
- Null pointer risks: {count}

**Memory Leaks:** {count}
- Undisposed controllers: {count}
- Uncancelled subscriptions: {count}

**Data Loss Risks:** {count}
- Silent failures: {count}
- Missing error handling: {count}

## Refactoring Recommendations

### High Priority (Critical Issues - Crash/Leak Risks)
1. **Add mounted checks in login_screen.dart**
   - Add `if (!mounted) return;` before Navigator calls
   - Prevents crashes when widget disposed during async
   - Estimated effort: 5 minutes

2. **Implement dispose in form_screen.dart**
   - Add dispose() method to clean up {X} controllers
   - Fixes memory leak
   - Estimated effort: 10 minutes

### Medium Priority (Warnings - Robustness)
1. **Add error handling to FutureBuilders**
   - {X} FutureBuilders need error builders
   - Improves user experience
   - Estimated effort: 30 minutes

2. **Extract business logic from profile.dart**
   - Move validation and calculations to ViewModel
   - Improves testability and separation
   - Estimated effort: 45 minutes

### Low Priority (Improvements)
1. **Add SafeArea to detail screens**
   - Handles device notches properly
   - Estimated effort: 15 minutes

## Quality Trend

{If previous safety reports exist}
- Last check: {date}
- Safety score: {old}% → {new}% ({change})
- Critical issues: {old count} → {new count} ({change})
- Resource leaks: {old count} → {new count} ({change})
- Context safety: {old}% → {new}% ({change})

## Next Steps

{If critical issues:}
⚠️ **URGENT:** Fix {X} critical issues - crash risks and memory leaks detected!
Priority: {List top 3 critical issues}

{If warnings only:}
✅ No critical safety issues. Address {Y} warnings to improve robustness.

{If all clear:}
✅ Excellent safety practices! Code is robust and handles edge cases well.

---
*Companion checks: /flutter-check-structure (widget architecture), /flutter-check-patterns (Flutter patterns & style)*
```

## Chat Output

After writing the report, display concise summary in chat:

```
{✅ | ⚠️ | ❌} Flutter Safety Check Complete

📄 Report: .quality/flutter/safety-{TIMESTAMP}.md
Files: {X} Dart files
Safety Score: {percentage}%

{If critical issues:}
🔴 CRITICAL: {count} crash/leak risks!
1. {Brief description} - {file:line}
2. {Brief description} - {file:line}

Risks:
- Crash risks: {count} (context safety, null pointers)
- Memory leaks: {count} (undisposed resources)
- Data loss risks: {count} (missing error handling)

{If warnings:}
🟡 Warnings: {count}

Scores:
- BuildContext safety: {percentage}%
- Resource management: {percentage}%
- Error handling: {percentage}%
- Logic separation: {percentage}%
- Layout robustness: {percentage}%

{Top 1-2 urgent fixes if critical issues exist}
```

## Important Notes

- **Check ALL Dart files** - Comprehensive safety analysis
- **Prioritize crash risks** - Context safety and null issues are critical
- **Be specific** - Always include file:line references
- **Show risks** - Explain what could go wrong
- **Provide fixes** - Show exactly how to fix each issue
- **Track resource pairs** - Every init should have dispose
- **Test edge cases** - Think about what could fail
- **Focus on user impact** - Crashes and data loss are critical
