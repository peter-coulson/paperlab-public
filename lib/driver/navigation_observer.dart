import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:paperlab/driver/driver_logger.dart';
import 'package:paperlab/driver/driver_state_widget.dart'
    show DriverStateWidget;

/// NavigatorObserver that logs all navigation events for driver queries.
///
/// Add this observer to [MaterialApp.navigatorObservers] to automatically
/// log all navigation events (push, pop, replace, remove).
///
/// Usage in main.dart:
/// ```dart
/// MaterialApp(
///   navigatorObservers: [
///     if (kDebugMode) DriverNavigationObserver(),
///   ],
/// )
/// ```
///
/// Events are logged via [DriverLogger.navigation] and can be queried
/// through the [DriverStateWidget].
class DriverNavigationObserver extends NavigatorObserver {
  /// Creates a navigation observer for driver logging.
  DriverNavigationObserver();

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (!kDebugMode) return;

    DriverLogger.navigation('push', _routeName(route), {
      'from': _routeName(previousRoute),
    });
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (!kDebugMode) return;

    DriverLogger.navigation('pop', _routeName(previousRoute), {
      'popped': _routeName(route),
      'to': _routeName(previousRoute),
    });
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    if (!kDebugMode) return;

    DriverLogger.navigation('replace', _routeName(newRoute), {
      'replaced': _routeName(oldRoute),
    });
  }

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (!kDebugMode) return;

    DriverLogger.navigation('remove', _routeName(route), {
      'previous': _routeName(previousRoute),
    });
  }

  /// Extract a readable name from a route.
  ///
  /// Tries in order:
  /// 1. Route settings name (if set)
  /// 2. Route runtime type (e.g., MaterialPageRoute)
  /// 3. 'unknown' as fallback
  String _routeName(Route<dynamic>? route) {
    if (route == null) return 'null';

    // Try to get named route
    final name = route.settings.name;
    if (name != null && name.isNotEmpty) {
      return name;
    }

    // Try to extract screen name from MaterialPageRoute
    // The builder creates widgets like HomeScreen, LoginScreen, etc.
    // We can get the type from the route's current result or settings
    final settings = route.settings;
    if (settings.arguments != null) {
      return '${route.runtimeType}(${settings.arguments})';
    }

    // Fall back to route type
    return route.runtimeType.toString();
  }
}
