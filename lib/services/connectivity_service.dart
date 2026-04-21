import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:paperlab/config.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'connectivity_service.g.dart';

/// Connectivity service that monitors network status.
///
/// Uses HTTP health checks as the source of truth for connectivity.
/// connectivity_plus triggers re-checks but is not trusted alone
/// (unreliable on desktop platforms).
class ConnectivityService {
  ConnectivityService() {
    _init();
  }

  final Connectivity _connectivity = Connectivity();
  final StreamController<bool> _controller = StreamController<bool>.broadcast();

  /// Completes when initial connectivity check is done.
  final Completer<void> _initialCheckComplete = Completer<void>();

  /// Wait for initial check to complete before reading [isOnline].
  Future<void> get ready => _initialCheckComplete.future;

  /// Stream of connectivity status changes (true = online, false = offline).
  Stream<bool> get onConnectivityChanged => _controller.stream;

  /// Current connectivity status. Null until initial check completes.
  bool? _isOnline;

  /// Current connectivity status. Defaults to true until proven otherwise.
  bool get isOnline => _isOnline ?? true;

  Timer? _debounceTimer;
  Timer? _periodicTimer;
  StreamSubscription<List<ConnectivityResult>>? _subscription;

  void _init() {
    // Listen to connectivity_plus as trigger for re-checks
    _subscription = _connectivity.onConnectivityChanged.listen((results) {
      _debounceConnectivityChange(results);
    });

    // Check initial status
    _checkInitialConnectivity();

    // Periodic re-check for resilience (catches missed events)
    _periodicTimer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => _checkConnectivity(),
    );
  }

  Future<void> _checkInitialConnectivity() async {
    try {
      await _checkConnectivity();
    } finally {
      // Always complete, even on error
      if (!_initialCheckComplete.isCompleted) {
        _initialCheckComplete.complete();
      }
    }
  }

  /// Debounce connectivity_plus events to prevent rapid flickering.
  void _debounceConnectivityChange(List<ConnectivityResult> results) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(AppConfig.connectivityDebounce, () {
      _checkConnectivity();
    });
  }

  /// Check connectivity via HTTP health check and update state.
  Future<void> _checkConnectivity() async {
    final isOnline = await _checkRealConnectivity();

    // Only emit if state changed
    if (_isOnline != isOnline) {
      _isOnline = isOnline;
      _controller.add(isOnline);
    }
  }

  /// Verify real internet access by making an HTTP request to our API.
  Future<bool> _checkRealConnectivity() async {
    try {
      final response = await http
          .get(Uri.parse('${AppConfig.apiBaseUrl}${AppConfig.healthCheckPath}'))
          .timeout(AppConfig.connectivityCheckTimeout);

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  void dispose() {
    _debounceTimer?.cancel();
    _periodicTimer?.cancel();
    _subscription?.cancel();
    _controller.close();
  }
}

/// Riverpod provider for connectivity status stream.
/// Waits for initial check, then emits current state and subsequent changes.
@riverpod
Stream<bool> connectivityStatus(Ref ref) async* {
  final service = ref.watch(connectivityServiceProvider);

  // Wait for initial check to complete before reading state
  await service.ready;

  // Yield current state (now accurate after initial check)
  yield service.isOnline;

  // Continue with change stream
  await for (final value in service.onConnectivityChanged) {
    yield value;
  }
}

/// Singleton ConnectivityService provider.
@Riverpod(keepAlive: true)
ConnectivityService connectivityService(Ref ref) {
  final service = ConnectivityService();
  ref.onDispose(service.dispose);
  return service;
}
