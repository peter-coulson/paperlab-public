import 'package:paperlab/models/paper_result.dart';
import 'package:paperlab/models/question_detail_result.dart';
import 'package:paperlab/repositories/api_client.dart';

/// Results data access.
class ResultsRepository {
  ResultsRepository({required this.client});

  final ApiClient client;

  /// GET /api/attempts/papers/{id}/results
  Future<PaperResult> getPaperResults(int attemptId) async {
    final response = await client.get(
      '/api/attempts/papers/$attemptId/results',
    );
    final json = client.parseJson(response);
    return PaperResult.fromJson(json);
  }

  /// GET /api/attempts/papers/{paper_attempt_id}/questions/{question_attempt_id}/results
  Future<QuestionDetailResult> getPaperQuestionResults({
    required int paperAttemptId,
    required int questionAttemptId,
  }) async {
    final response = await client.get(
      '/api/attempts/papers/$paperAttemptId/questions/$questionAttemptId/results',
    );
    final json = client.parseJson(response);
    return QuestionDetailResult.fromJson(json);
  }

  /// GET /api/attempts/practice/{id}/results
  Future<QuestionDetailResult> getPracticeResults(int attemptId) async {
    final response = await client.get(
      '/api/attempts/practice/$attemptId/results',
    );
    final json = client.parseJson(response);
    return QuestionDetailResult.fromJson(json);
  }
}
