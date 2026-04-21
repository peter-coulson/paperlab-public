import 'package:paperlab/exceptions/network_exceptions.dart';
import 'package:paperlab/models/paper_attempt.dart';
import 'package:paperlab/models/question_attempt.dart';
import 'package:paperlab/providers/providers.dart';
import 'package:paperlab/utils/cache_extensions.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'attempts_provider.g.dart';

/// Paper attempts state with async loading.
@riverpod
class PaperAttempts extends _$PaperAttempts {
  @override
  Future<List<PaperAttempt>> build() async {
    // Keep cached for 5 minutes after prefetch
    ref.cacheFor(const Duration(minutes: 5));

    final repo = ref.watch(attemptsRepositoryProvider);
    return repo.listPaperAttempts();
  }

  /// Optimistic delete with undo support.
  /// Returns restore function for undo toast.
  Future<Future<void> Function()> delete(int id) async {
    final repo = ref.read(attemptsRepositoryProvider);

    // Get current state for optimistic update
    final currentState = state.valueOrNull ?? [];
    final deletedItem = currentState.firstWhere((p) => p.id == id);
    final deletedIndex = currentState.indexOf(deletedItem);

    // Optimistic update - remove from list immediately
    state = AsyncData(currentState.where((p) => p.id != id).toList());

    // Call API
    try {
      await repo.deletePaperAttempt(id);
    } on ApiException {
      // Restore on failure
      final restored = List<PaperAttempt>.from(state.valueOrNull ?? [])
        ..insert(deletedIndex, deletedItem);
      state = AsyncData(restored);
      rethrow;
    }

    // Return restore function for undo
    return () async {
      await repo.restorePaperAttempt(id);
      ref.invalidateSelf();
    };
  }

  /// Refresh from API.
  Future<void> refresh() async {
    ref.invalidateSelf();
  }
}

/// Question attempts state with async loading.
@riverpod
class QuestionAttempts extends _$QuestionAttempts {
  @override
  Future<List<QuestionAttempt>> build() async {
    // Keep cached for 5 minutes after prefetch
    ref.cacheFor(const Duration(minutes: 5));

    final repo = ref.watch(attemptsRepositoryProvider);
    return repo.listQuestionAttempts();
  }

  /// Optimistic delete with undo support.
  /// Returns restore function for undo toast.
  Future<Future<void> Function()> delete(int id) async {
    final repo = ref.read(attemptsRepositoryProvider);

    // Get current state for optimistic update
    final currentState = state.valueOrNull ?? [];
    final deletedItem = currentState.firstWhere((q) => q.id == id);
    final deletedIndex = currentState.indexOf(deletedItem);

    // Optimistic update - remove from list immediately
    state = AsyncData(currentState.where((q) => q.id != id).toList());

    // Call API
    try {
      await repo.deleteQuestionAttempt(id);
    } on ApiException {
      // Restore on failure
      final restored = List<QuestionAttempt>.from(state.valueOrNull ?? [])
        ..insert(deletedIndex, deletedItem);
      state = AsyncData(restored);
      rethrow;
    }

    // Return restore function for undo
    return () async {
      await repo.restoreQuestionAttempt(id);
      ref.invalidateSelf();
    };
  }

  /// Refresh from API.
  Future<void> refresh() async {
    ref.invalidateSelf();
  }
}
