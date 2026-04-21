import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/models/paper_result.dart';
import 'package:paperlab/models/question_detail_result.dart';
import 'package:paperlab/providers/providers.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'results_provider.g.dart';

/// Paper results (fetched once, not polling).
@riverpod
Future<PaperResult> paperResults(Ref ref, int attemptId) async {
  final repo = ref.watch(resultsRepositoryProvider);
  return repo.getPaperResults(attemptId);
}

/// Question results from paper flow.
@riverpod
Future<QuestionDetailResult> paperQuestionResults(
  Ref ref, {
  required int paperAttemptId,
  required int questionAttemptId,
}) async {
  final repo = ref.watch(resultsRepositoryProvider);
  return repo.getPaperQuestionResults(
    paperAttemptId: paperAttemptId,
    questionAttemptId: questionAttemptId,
  );
}

/// Question results from practice flow.
@riverpod
Future<QuestionDetailResult> practiceResults(Ref ref, int attemptId) async {
  final repo = ref.watch(resultsRepositoryProvider);
  return repo.getPracticeResults(attemptId);
}
