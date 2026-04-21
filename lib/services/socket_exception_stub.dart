/// Stub for SocketException on web platform.
/// On web, dart:io is not available, so we provide a stub class
/// that will never match (since web doesn't have SocketException).
library;

/// Stub SocketException class for web platform.
/// This class is never instantiated on web - it's just for type checking.
class SocketException implements Exception {
  const SocketException(this.message, {this.osError, this.address, this.port});

  final String message;
  final dynamic osError;
  final dynamic address;
  final int? port;

  @override
  String toString() => 'SocketException: $message';
}
