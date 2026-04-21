import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:paperlab/exceptions/network_exceptions.dart';
import 'package:paperlab/services/dio_client.dart';

/// Central HTTP client using Dio with global error handling.
/// All repositories use this for consistency.
/// Errors are automatically converted to NetworkException types
/// by the DioClient interceptor.
class ApiClient {
  ApiClient({required DioClient dioClient}) : _dioClient = dioClient;

  final DioClient _dioClient;

  /// GET request with auth headers.
  /// Throws NetworkException on error.
  Future<String> get(String path) async {
    try {
      final response = await _dioClient.get<String>(path);
      return response.data ?? '';
    } on DioException catch (e) {
      // Extract our custom exception from Dio error
      if (e.error is NetworkException) {
        throw e.error as NetworkException;
      }
      // Fallback for unexpected errors
      throw UnknownNetworkException(e);
    }
  }

  /// POST request with auth headers and optional JSON body.
  /// Throws NetworkException on error.
  Future<String> post(String path, {Map<String, dynamic>? body}) async {
    try {
      final response = await _dioClient.post<String>(path, data: body);
      return response.data ?? '';
    } on DioException catch (e) {
      // Extract our custom exception from Dio error
      if (e.error is NetworkException) {
        throw e.error as NetworkException;
      }
      // Fallback for unexpected errors
      throw UnknownNetworkException(e);
    }
  }

  /// DELETE request with auth headers.
  /// Throws NetworkException on error.
  Future<String> delete(String path) async {
    try {
      final response = await _dioClient.delete<String>(path);
      return response.data ?? '';
    } on DioException catch (e) {
      // Extract our custom exception from Dio error
      if (e.error is NetworkException) {
        throw e.error as NetworkException;
      }
      // Fallback for unexpected errors
      throw UnknownNetworkException(e);
    }
  }

  /// PUT request with raw bytes (for R2 uploads).
  /// Bypasses JSON encoding and auth headers.
  /// Returns true on success (200 status).
  /// Throws NetworkException on error.
  Future<bool> putBytes(
    String url,
    List<int> bytes, {
    Map<String, String>? headers,
  }) async {
    try {
      final response = await _dioClient.putBytes(url, bytes, headers: headers);
      return response.statusCode == 200;
    } on DioException catch (e) {
      // Extract our custom exception from Dio error
      if (e.error is NetworkException) {
        throw e.error as NetworkException;
      }
      // Fallback for unexpected errors
      throw UnknownNetworkException(e);
    }
  }

  /// Parse JSON response body.
  Map<String, dynamic> parseJson(String body) =>
      jsonDecode(body) as Map<String, dynamic>;
}
