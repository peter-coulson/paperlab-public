import 'package:dio/dio.dart';
import 'package:paperlab/config.dart';
import 'package:paperlab/exceptions/network_exceptions.dart';
import 'package:paperlab/services/auth_service.dart';
import 'package:paperlab/services/socket_exception_stub.dart'
    if (dart.library.io) 'dart:io';

/// Global Dio client with error interceptor.
/// Handles all network errors consistently across the app.
class DioClient {
  DioClient({required this.baseUrl}) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    // Add global error interceptor
    _dio.interceptors.add(_ErrorInterceptor());
  }

  final String baseUrl;
  late final Dio _dio;

  /// Access underlying Dio instance.
  Dio get instance => _dio;

  /// GET request with auth headers.
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async => _dio.get<T>(path, queryParameters: queryParameters);

  /// POST request with auth headers and optional JSON body.
  Future<Response<T>> post<T>(
    String path, {
    Map<String, dynamic>? data,
  }) async => _dio.post<T>(path, data: data);

  /// DELETE request with auth headers.
  Future<Response<T>> delete<T>(String path) async => _dio.delete<T>(path);

  /// PUT request with raw bytes (for R2 uploads).
  /// Bypasses JSON encoding and auth headers.
  Future<Response<T>> putBytes<T>(
    String url,
    List<int> bytes, {
    Map<String, String>? headers,
  }) async => _dio.put<T>(
    url,
    data: bytes,
    options: Options(
      headers: headers ?? {'Content-Type': 'image/jpeg'},
      // Don't add auth headers for R2 presigned URLs
      // (they have auth built into the URL)
    ),
  );
}

/// Global error interceptor - catches all network errors.
/// Converts Dio errors into our custom exception types.
class _ErrorInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    // Add auth headers to all API requests (but not R2 uploads)
    // R2 presigned URLs have auth built into the URL
    if (!options.path.contains(AppConfig.r2Domain)) {
      // Use AuthService singleton for Supabase token
      options.headers.addAll(AuthService.instance.authHeaders);
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final exception = _convertDioError(err);
    handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        error: exception,
        type: err.type,
        response: err.response,
        message: err.message,
      ),
    );
  }

  /// Convert DioException to our custom exception types.
  NetworkException _convertDioError(DioException error) {
    // Check if this is an R2/S3 storage request
    final isStorageRequest = _isStorageRequest(error.requestOptions.uri);

    return switch (error.type) {
      // Connection errors - could be CORS/storage config on R2, or actual network failure
      DioExceptionType.connectionError =>
        isStorageRequest
            ? _handleStorageConnectionError(error)
            : const NoConnectivityException(),

      // Timeout errors
      DioExceptionType.connectionTimeout ||
      DioExceptionType.receiveTimeout ||
      DioExceptionType.sendTimeout => const RequestTimeoutException(),

      // HTTP response errors (4xx/5xx)
      DioExceptionType.badResponse =>
        isStorageRequest
            ? _handleStorageResponseError(error)
            : _parseApiError(error),

      // Request cancelled
      DioExceptionType.cancel => UnknownNetworkException(error),

      // Other errors - check for SocketException or storage issues
      _ => _handleOtherError(error, isStorageRequest),
    };
  }

  /// Parse API error response (4xx/5xx).
  ApiException _parseApiError(DioException error) {
    final statusCode = error.response?.statusCode ?? 0;
    String message;

    try {
      final data = error.response?.data;
      if (data is Map<String, dynamic>) {
        message =
            data['detail']?.toString() ?? data['message']?.toString() ?? '';
      } else {
        message = data?.toString() ?? '';
      }
    } catch (_) {
      message = '';
    }

    return ApiException(statusCode: statusCode, message: message);
  }

  /// Handle other error types - check for SocketException.
  NetworkException _handleOtherError(
    DioException error,
    bool isStorageRequest,
  ) {
    final originalError = error.error;

    // SocketException indicates no connectivity (unless storage-related)
    if (originalError is SocketException) {
      return isStorageRequest
          ? const StorageConfigurationException(
              message: 'Storage connection failed - check bucket configuration',
            )
          : const NoConnectivityException();
    }

    // Unknown error
    return UnknownNetworkException(originalError ?? error);
  }

  /// Check if the request is to R2/S3 storage.
  bool _isStorageRequest(Uri uri) =>
      uri.toString().contains(AppConfig.r2Domain);

  /// Handle connection errors for storage requests.
  /// On Flutter Web, CORS errors manifest as connectionError.
  NetworkException _handleStorageConnectionError(DioException error) {
    final errorMessage = error.message ?? '';
    final errorString = error.error?.toString() ?? '';

    // Check for CORS-specific indicators (Flutter Web)
    if (errorMessage.contains('XMLHttpRequest') ||
        errorString.contains('XMLHttpRequest')) {
      return const StorageConfigurationException(
        message: 'Storage upload failed - check CORS config and bucket name',
      );
    }

    // Fallback for other connection errors to storage
    return const StorageConfigurationException(
      message: 'Storage upload failed - check bucket configuration',
    );
  }

  /// Handle HTTP response errors for storage requests.
  NetworkException _handleStorageResponseError(DioException error) {
    final statusCode = error.response?.statusCode ?? 0;

    return switch (statusCode) {
      403 => const StorageConfigurationException(
        message: 'Storage access denied - check bucket permissions or CORS',
      ),
      404 => const StorageConfigurationException(
        message: 'Storage bucket not found - check bucket name',
      ),
      _ => StorageConfigurationException(
        message: 'Storage upload failed (HTTP $statusCode)',
      ),
    };
  }
}
