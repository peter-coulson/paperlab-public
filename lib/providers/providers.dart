import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/config.dart';
import 'package:paperlab/repositories/account_repository.dart';
import 'package:paperlab/repositories/api_client.dart';
import 'package:paperlab/repositories/attempts_repository.dart';
import 'package:paperlab/repositories/discovery_repository.dart';
import 'package:paperlab/repositories/results_repository.dart';
import 'package:paperlab/repositories/status_repository.dart';
import 'package:paperlab/repositories/upload_repository.dart';
import 'package:paperlab/services/auth_service.dart';
import 'package:paperlab/services/dio_client.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'providers.g.dart';

/// Singleton AuthService provider.
/// Uses AuthService.instance singleton for Supabase auth.
@Riverpod(keepAlive: true)
AuthService authService(Ref ref) => AuthService.instance;

/// Singleton DioClient provider.
/// Provides Dio instance with global error interceptor.
/// Auth headers are added via AuthService.instance in the interceptor.
@Riverpod(keepAlive: true)
DioClient dioClient(Ref ref) => DioClient(baseUrl: AppConfig.apiBaseUrl);

/// Singleton ApiClient provider.
@Riverpod(keepAlive: true)
ApiClient apiClient(Ref ref) {
  final dio = ref.watch(dioClientProvider);
  return ApiClient(dioClient: dio);
}

/// Singleton AttemptsRepository provider.
@Riverpod(keepAlive: true)
AttemptsRepository attemptsRepository(Ref ref) {
  final client = ref.watch(apiClientProvider);
  return AttemptsRepository(client: client);
}

/// Singleton DiscoveryRepository provider.
@Riverpod(keepAlive: true)
DiscoveryRepository discoveryRepository(Ref ref) {
  final client = ref.watch(apiClientProvider);
  return DiscoveryRepository(client: client);
}

/// Singleton UploadRepository provider.
@Riverpod(keepAlive: true)
UploadRepository uploadRepository(Ref ref) {
  final client = ref.watch(apiClientProvider);
  return UploadRepository(client: client);
}

/// Singleton StatusRepository provider.
@Riverpod(keepAlive: true)
StatusRepository statusRepository(Ref ref) {
  final client = ref.watch(apiClientProvider);
  return StatusRepository(client: client);
}

/// Singleton ResultsRepository provider.
@Riverpod(keepAlive: true)
ResultsRepository resultsRepository(Ref ref) {
  final client = ref.watch(apiClientProvider);
  return ResultsRepository(client: client);
}

/// Singleton AccountRepository provider.
@Riverpod(keepAlive: true)
AccountRepository accountRepository(Ref ref) {
  final client = ref.watch(apiClientProvider);
  return AccountRepository(client: client);
}
