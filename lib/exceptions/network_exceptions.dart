/// Custom network exceptions for categorized error handling.
/// These exceptions are thrown by the Dio interceptor and ApiClient
/// to provide clear, user-friendly error messages throughout the app.
library;

/// Base class for all network-related exceptions.
sealed class NetworkException implements Exception {
  const NetworkException(this.message);

  final String message;

  @override
  String toString() => message;
}

/// No internet connectivity (WiFi/cellular unavailable).
/// Thrown when device has no active network connection.
class NoConnectivityException extends NetworkException {
  const NoConnectivityException() : super('No internet connection detected');
}

/// Request timeout - server took too long to respond.
/// Thrown when HTTP request exceeds timeout duration.
class RequestTimeoutException extends NetworkException {
  const RequestTimeoutException()
    : super('Request timed out - please try again');
}

/// API returned non-2xx response (4xx/5xx errors).
/// Includes status code and server message for debugging.
class ApiException extends NetworkException {
  const ApiException({required this.statusCode, required String message})
    : super(message);

  final int statusCode;

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// Upload operation failed (presigned URL fetch or R2 upload).
/// Used specifically for file upload failures.
class UploadException extends NetworkException {
  const UploadException(super.message);
}

/// Storage configuration error (CORS, invalid bucket, permissions).
/// Thrown when R2/S3 uploads fail due to misconfiguration.
/// Flutter Web specific - often caused by CORS issues or invalid bucket names.
class StorageConfigurationException extends NetworkException {
  const StorageConfigurationException({required String message})
    : super(message);
}

/// Unknown network error - catch-all for unexpected failures.
/// Includes original error for debugging.
class UnknownNetworkException extends NetworkException {
  const UnknownNetworkException(this.originalError)
    : super('An unexpected error occurred');

  final Object originalError;

  @override
  String toString() => 'UnknownNetworkException: $originalError';
}
