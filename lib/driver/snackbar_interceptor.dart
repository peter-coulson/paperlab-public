import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:paperlab/driver/driver_logger.dart';

/// A ScaffoldMessenger that automatically logs all snackbar displays.
///
/// This widget shadows the default ScaffoldMessenger from MaterialApp,
/// intercepting all `ScaffoldMessenger.of(context).showSnackBar()` calls
/// and logging them via [DriverLogger] before displaying.
///
/// Usage in MaterialApp.builder:
/// ```dart
/// MaterialApp(
///   builder: (context, child) {
///     if (kDebugMode) {
///       return LoggingScaffoldMessenger(child: child!);
///     }
///     return child!;
///   },
/// )
/// ```
///
/// This provides automatic snackbar logging with zero changes to existing
/// screen code - any call to `ScaffoldMessenger.of(context).showSnackBar()`
/// will be captured automatically.
class LoggingScaffoldMessenger extends ScaffoldMessenger {
  /// Creates a logging scaffold messenger.
  const LoggingScaffoldMessenger({required super.child, super.key});

  @override
  ScaffoldMessengerState createState() => _LoggingScaffoldMessengerState();
}

/// State for [LoggingScaffoldMessenger] that intercepts snackbar calls.
class _LoggingScaffoldMessengerState extends ScaffoldMessengerState {
  @override
  ScaffoldFeatureController<SnackBar, SnackBarClosedReason> showSnackBar(
    SnackBar snackBar, {
    AnimationStyle? snackBarAnimationStyle,
  }) {
    if (kDebugMode) {
      final message = _extractMessage(snackBar);
      DriverLogger.feedback('snackbar', message, {
        'hasAction': snackBar.action != null,
        'duration': snackBar.duration.inMilliseconds,
      });
    }

    return super.showSnackBar(
      snackBar,
      snackBarAnimationStyle: snackBarAnimationStyle,
    );
  }

  /// Extract a readable message from the SnackBar content.
  ///
  /// Handles common cases:
  /// - [Text] widget: extracts the text data
  /// - Other widgets: returns the runtime type as fallback
  String _extractMessage(SnackBar snackBar) {
    final content = snackBar.content;

    // Handle Text widget (most common case)
    if (content is Text) {
      return content.data ?? content.textSpan?.toPlainText() ?? '[Text]';
    }

    // Fallback for other widget types
    return '[${content.runtimeType}]';
  }
}
