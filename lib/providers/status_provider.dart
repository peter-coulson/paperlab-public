import 'dart:async';

import 'package:paperlab/models/marking_status.dart';
import 'package:paperlab/providers/providers.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'status_provider.g.dart';

/// Polling provider for paper marking status.
@riverpod
class PaperStatusPolling extends _$PaperStatusPolling {
  Timer? _timer;

  @override
  AsyncValue<PaperStatus> build(int attemptId) {
    // Start polling on build
    _startPolling(attemptId);

    // Cleanup on dispose
    ref.onDispose(() {
      _timer?.cancel();
      _timer = null;
    });

    return const AsyncValue.loading();
  }

  void _startPolling(int attemptId) {
    // Initial fetch
    _fetchStatus(attemptId);

    // Poll every 3 seconds
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _fetchStatus(attemptId);
    });
  }

  Future<void> _fetchStatus(int attemptId) async {
    final repo = ref.read(statusRepositoryProvider);

    try {
      final status = await repo.getPaperStatus(attemptId);
      state = AsyncValue.data(status);

      // Stop polling on terminal state
      if (status.status.isTerminal) {
        _timer?.cancel();
        _timer = null;
      }
    } catch (e, st) {
      // On error, set error state but continue polling (transient errors)
      // User can close screen to stop polling
      state = AsyncValue.error(e, st);
      // Note: Timer continues running - will retry on next interval
    }
  }
}

/// Polling provider for question marking status.
@riverpod
class QuestionStatusPolling extends _$QuestionStatusPolling {
  Timer? _timer;

  @override
  AsyncValue<QuestionStatus> build(int attemptId) {
    _startPolling(attemptId);
    ref.onDispose(() {
      _timer?.cancel();
      _timer = null;
    });
    return const AsyncValue.loading();
  }

  void _startPolling(int attemptId) {
    _fetchStatus(attemptId);
    _timer = Timer.periodic(const Duration(seconds: 3), (_) {
      _fetchStatus(attemptId);
    });
  }

  Future<void> _fetchStatus(int attemptId) async {
    final repo = ref.read(statusRepositoryProvider);

    try {
      final status = await repo.getQuestionStatus(attemptId);
      state = AsyncValue.data(status);

      if (status.status.isTerminal) {
        _timer?.cancel();
        _timer = null;
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      // Timer continues - will retry on next interval
    }
  }
}
