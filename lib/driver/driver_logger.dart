import 'dart:convert';

import 'package:flutter/foundation.dart';

/// Event types for driver logging.
enum DriverEventType {
  /// Navigation events (push, pop, replace).
  navigation,

  /// User feedback events (snackbar, dialog, toast).
  feedback,

  /// Error events (exceptions, failures).
  error,

  /// Async operation events (loading, complete, failed).
  async,
}

/// A single logged event for driver queries.
class DriverEvent {
  /// Creates a driver event.
  const DriverEvent({
    required this.timestamp,
    required this.type,
    required this.category,
    required this.message,
    this.data,
  });

  /// When the event occurred.
  final DateTime timestamp;

  /// The type of event.
  final DriverEventType type;

  /// Sub-category (e.g., 'push', 'snackbar', 'timeout').
  final String category;

  /// Human-readable description.
  final String message;

  /// Optional structured data.
  final Map<String, dynamic>? data;

  /// Convert to JSON for driver queries.
  Map<String, dynamic> toJson() => {
    'time': _formatTime(timestamp),
    'type': type.name,
    'category': category,
    'message': message,
    if (data != null) 'data': data,
  };

  static String _formatTime(DateTime dt) =>
      '${dt.hour.toString().padLeft(2, '0')}:'
      '${dt.minute.toString().padLeft(2, '0')}:'
      '${dt.second.toString().padLeft(2, '0')}.'
      '${dt.millisecond.toString().padLeft(3, '0')}';
}

/// Central event logging for agentic UI testing.
///
/// All methods are no-ops in release builds (tree-shaken via kDebugMode).
/// Events are stored in a rolling buffer and exposed via [getState].
///
/// Usage:
/// ```dart
/// DriverLogger.navigation('push', 'HomeScreen');
/// DriverLogger.feedback('snackbar', 'Login failed');
/// DriverLogger.error('API timeout', exception, stackTrace);
/// DriverLogger.async('start', 'Loading papers');
/// ```
///
/// Query via flutter_driver:
/// ```dart
/// String json = await driver.getText(find.byValueKey('driver_state'));
/// Map<String, dynamic> state = jsonDecode(json);
/// ```
class DriverLogger {
  DriverLogger._();

  /// Maximum number of events to keep in the buffer.
  static const int maxEvents = 100;

  /// Event buffer (rolling, oldest events dropped when full).
  static final List<DriverEvent> _events = [];

  /// Current screen name (updated by navigation observer).
  static String? _currentScreen;

  /// Whether an async operation is in progress.
  static bool _isLoading = false;

  /// Most recent feedback message (snackbar, dialog, etc.).
  static String? _lastFeedback;

  /// Most recent error message.
  static String? _lastError;

  /// Log a navigation event.
  ///
  /// Categories: 'push', 'pop', 'replace', 'remove'
  static void navigation(
    String category,
    String message, [
    Map<String, dynamic>? data,
  ]) {
    if (!kDebugMode) return;

    _addEvent(DriverEventType.navigation, category, message, data);

    // Update current screen for quick state queries
    if (category == 'push' || category == 'replace') {
      _currentScreen = message;
    } else if (category == 'pop' && data?['to'] != null) {
      _currentScreen = data!['to'] as String;
    }
  }

  /// Log a feedback event (snackbar, dialog, toast, banner).
  ///
  /// Categories: 'snackbar', 'dialog', 'toast', 'banner'
  static void feedback(
    String category,
    String message, [
    Map<String, dynamic>? data,
  ]) {
    if (!kDebugMode) return;

    _addEvent(DriverEventType.feedback, category, message, data);
    _lastFeedback = message;
  }

  /// Log an error event.
  static void error(String message, [Object? error, StackTrace? stackTrace]) {
    if (!kDebugMode) return;

    final data = <String, dynamic>{};
    if (error != null) {
      data['error'] = error.toString();
    }
    if (stackTrace != null) {
      // Only include first 3 lines of stack trace
      final lines = stackTrace.toString().split('\n').take(3).join('\n');
      data['stackTrace'] = lines;
    }

    _addEvent(
      DriverEventType.error,
      'error',
      message,
      data.isEmpty ? null : data,
    );
    _lastError = message;
  }

  /// Log an async operation event.
  ///
  /// Categories: 'start', 'complete', 'failed'
  static void async(
    String category,
    String message, [
    Map<String, dynamic>? data,
  ]) {
    if (!kDebugMode) return;

    _addEvent(DriverEventType.async, category, message, data);

    // Update loading state
    if (category == 'start') {
      _isLoading = true;
    } else if (category == 'complete' || category == 'failed') {
      _isLoading = false;
    }
  }

  /// Get the current state for driver queries.
  ///
  /// Returns a JSON-serializable map with:
  /// - `timestamp`: Current time
  /// - `currentState`: Quick-access state snapshot
  /// - `recentEvents`: Last N events for debugging
  static Map<String, dynamic> getState() {
    if (!kDebugMode) {
      return {'error': 'Driver logging disabled in release mode'};
    }

    return {
      'timestamp': DateTime.now().toIso8601String(),
      'currentState': {
        'screen': _currentScreen,
        'isLoading': _isLoading,
        'lastFeedback': _lastFeedback,
        'lastError': _lastError,
        'eventCount': _events.length,
      },
      'recentEvents': _events.map((e) => e.toJson()).toList(),
    };
  }

  /// Get the state as a JSON string.
  static String getStateJson() {
    if (!kDebugMode) return '{}';
    return jsonEncode(getState());
  }

  /// Clear all events and reset state.
  ///
  /// Useful for test isolation.
  static void clear() {
    if (!kDebugMode) return;

    _events.clear();
    _currentScreen = null;
    _isLoading = false;
    _lastFeedback = null;
    _lastError = null;
  }

  /// Add an event to the buffer.
  static void _addEvent(
    DriverEventType type,
    String category,
    String message,
    Map<String, dynamic>? data,
  ) {
    final event = DriverEvent(
      timestamp: DateTime.now(),
      type: type,
      category: category,
      message: message,
      data: data,
    );

    _events.add(event);

    // Trim to max size (remove oldest events)
    while (_events.length > maxEvents) {
      _events.removeAt(0);
    }

    // Also print to console for debugging
    debugPrint('[Driver] ${type.name}/$category: $message');
  }
}
