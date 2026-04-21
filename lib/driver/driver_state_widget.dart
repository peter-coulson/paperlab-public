import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:paperlab/driver/driver_logger.dart';

/// Hidden widget that exposes log state for flutter_driver queries.
///
/// This widget renders an invisible [Text] widget containing JSON state
/// that can be queried via `driver.getText(find.byValueKey('driver_state'))`.
///
/// The state is refreshed every 500ms to ensure timely updates.
///
/// **Important:** This widget should only be included in [driver_main.dart],
/// never in the production [main.dart] entrypoint.
///
/// Usage in driver_main.dart:
/// ```dart
/// runApp(
///   Stack(
///     children: [
///       const PaperLabApp(),
///       const DriverStateWidget(),
///     ],
///   ),
/// );
/// ```
///
/// Query in flutter_driver:
/// ```dart
/// String json = await driver.getText(find.byValueKey('driver_state'));
/// Map<String, dynamic> state = jsonDecode(json);
/// print(state['currentState']['lastFeedback']);
/// ```
class DriverStateWidget extends StatefulWidget {
  /// Creates a driver state widget.
  const DriverStateWidget({super.key});

  @override
  State<DriverStateWidget> createState() => _DriverStateWidgetState();
}

class _DriverStateWidgetState extends State<DriverStateWidget> {
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();

    if (!kDebugMode) return;

    // Refresh state every 500ms for near real-time updates
    _refreshTimer = Timer.periodic(const Duration(milliseconds: 500), (_) {
      if (mounted) {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _refreshTimer = null;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // No-op in release mode
    if (!kDebugMode) {
      return const SizedBox.shrink();
    }

    // Hidden widget that exposes state for driver queries.
    // Uses Opacity(0) because flutter_driver can find transparent widgets
    // (they remain in the semantics tree), whereas Visibility and Offstage
    // remove widgets from the semantics tree that flutter_driver uses.
    //
    // IgnorePointer is CRITICAL: Without it, the invisible Text widget
    // still receives hit tests and blocks touches in the upper portion
    // of the screen as the JSON content grows with logged events.
    return IgnorePointer(
      child: Opacity(
        opacity: 0,
        child: Text(
          DriverLogger.getStateJson(),
          key: const ValueKey('driver_state'),
        ),
      ),
    );
  }
}
