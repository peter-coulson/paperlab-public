import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:paperlab/driver/driver_logger.dart';
import 'package:paperlab/exceptions/network_exceptions.dart';
import 'package:paperlab/theme/app_strings.dart';

/// Maps network exceptions to user-friendly error messages.
/// Provides consistent, actionable guidance throughout the app.
///
/// Usage:
/// ```dart
/// try {
///   await someNetworkCall();
/// } catch (e) {
///   final message = ErrorMessages.getUserMessage(e);
///   showSnackBar(message);
/// }
/// ```
class ErrorMessages {
  // Private constructor - utility class, never instantiated
  ErrorMessages._();

  /// Convert any exception to a user-friendly message.
  /// Returns specific guidance for known exceptions,
  /// generic message for unknown errors.
  ///
  /// In debug mode, also logs the error via [DriverLogger] for
  /// agentic UI testing queries.
  static String getUserMessage(Object error) {
    final message = switch (error) {
      NoConnectivityException() =>
        'No internet connection. Please check your WiFi or cellular data '
            'and try again.',
      RequestTimeoutException() =>
        'Request timed out. Please check your connection and try again.',
      ApiException(:final statusCode, :final message) => _getApiErrorMessage(
        statusCode,
        message,
      ),
      StorageConfigurationException(:final message) => message,
      UploadException(:final message) => 'Upload failed: $message',
      UnknownNetworkException() =>
        'An unexpected error occurred. Please try again.',
      // Catch-all for other exceptions
      _ => 'An unexpected error occurred. Please try again.',
    };

    // Log error for driver queries (tree-shaken in release)
    if (kDebugMode) {
      DriverLogger.error(message, error);
    }

    return message;
  }

  /// Map API status codes to user-friendly messages.
  static String _getApiErrorMessage(int statusCode, String serverMessage) =>
      switch (statusCode) {
        // 4xx Client Errors
        400 => 'Invalid request. Please check your input and try again.',
        401 => 'Authentication failed. Please sign in again.',
        403 => 'Access denied. You don\'t have permission for this action.',
        404 => 'Resource not found. Please try again.',
        429 => 'Too many requests. Please wait a moment and try again.',

        // 5xx Server Errors
        500 => 'Server error. Please try again later.',
        502 => 'Service temporarily unavailable. Please try again.',
        503 => 'Service temporarily unavailable. Please try again.',
        504 => 'Gateway timeout. Please check your connection and try again.',

        // Default - include server message if helpful
        _ =>
          serverMessage.isNotEmpty
              ? 'Request failed: $serverMessage'
              : 'Request failed. Please try again.',
      };

  /// Shows a refresh error snackbar with user-friendly message.
  static void showRefreshError(BuildContext context, Object error) {
    final message =
        '${AppStrings.failedToRefresh}: ${ErrorMessages.getUserMessage(error)}';
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }
}
