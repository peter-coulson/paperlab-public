import 'package:paperlab/models/marking_status.dart';
import 'package:paperlab/repositories/api_client.dart';

/// Status polling for marking progress.
class StatusRepository {
  StatusRepository({required this.client});

  final ApiClient client;

  /// GET /api/attempts/papers/{id}/status
  Future<PaperStatus> getPaperStatus(int attemptId) async {
    final response = await client.get('/api/attempts/papers/$attemptId/status');
    final json = client.parseJson(response);
    return PaperStatus.fromJson(json);
  }

  /// GET /api/attempts/questions/{id}/status
  Future<QuestionStatus> getQuestionStatus(int attemptId) async {
    final response = await client.get(
      '/api/attempts/questions/$attemptId/status',
    );
    final json = client.parseJson(response);
    return QuestionStatus.fromJson(json);
  }
}
