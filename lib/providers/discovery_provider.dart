import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/models/question_metadata.dart';
import 'package:paperlab/providers/providers.dart';
import 'package:paperlab/utils/cache_extensions.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'discovery_provider.g.dart';

/// Available papers for selection (cached).
@riverpod
Future<List<PaperMetadata>> availablePapers(Ref ref) async {
  // Keep cached for 5 minutes after prefetch
  ref.cacheFor(const Duration(minutes: 5));

  final repo = ref.watch(discoveryRepositoryProvider);
  return repo.listPapers();
}

/// Available questions for selection (filtered by paper).
@riverpod
Future<List<QuestionMetadata>> availableQuestions(
  Ref ref, {
  int? paperId,
}) async {
  final repo = ref.watch(discoveryRepositoryProvider);
  return repo.listQuestions(paperId: paperId);
}

/// Combined provider for question selection (questions + papers).
/// Loads both providers in parallel for cleaner question selection flow.
@riverpod
Future<({List<QuestionMetadata> questions, List<PaperMetadata> papers})>
questionsWithPapers(Ref ref) async {
  final results = await Future.wait([
    ref.watch(availableQuestionsProvider().future),
    ref.watch(availablePapersProvider.future),
  ]);

  return (
    questions: results[0] as List<QuestionMetadata>,
    papers: results[1] as List<PaperMetadata>,
  );
}
