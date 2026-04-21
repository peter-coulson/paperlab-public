import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Extensions for Riverpod cache management.
extension CacheForExtension on Ref {
  /// Keep provider alive for specified duration.
  ///
  /// Useful for prefetched data - prevents disposal before user needs it.
  /// Without this, autoDispose providers clear cache ~1s after prefetch,
  /// making the optimization ineffective.
  void cacheFor(Duration duration) {
    final link = keepAlive();
    Timer(duration, link.close);
  }
}
