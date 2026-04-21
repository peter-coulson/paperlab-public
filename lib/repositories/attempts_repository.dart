import 'dart:convert';

import 'package:paperlab/models/paper_attempt.dart';
import 'package:paperlab/models/question_attempt.dart';
import 'package:paperlab/repositories/api_client.dart';

/// Data access for paper and practice attempts.
class AttemptsRepository {
  AttemptsRepository({required this.client});

  final ApiClient client;

  /// GET /api/attempts/papers
  Future<List<PaperAttempt>> listPaperAttempts() async {
    final responseBody = await client.get('/api/attempts/papers');
    final list = jsonDecode(responseBody) as List<dynamic>;
    return list
        .map((json) => PaperAttempt.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// GET /api/attempts/questions
  Future<List<QuestionAttempt>> listQuestionAttempts() async {
    final responseBody = await client.get('/api/attempts/questions');
    final list = jsonDecode(responseBody) as List<dynamic>;
    return list
        .map((json) => QuestionAttempt.fromJson(json as Map<String, dynamic>))
        .toList();
  }

  /// DELETE /api/attempts/papers/{id}
  Future<void> deletePaperAttempt(int id) async {
    await client.delete('/api/attempts/papers/$id');
  }

  /// DELETE /api/attempts/questions/{id}
  Future<void> deleteQuestionAttempt(int id) async {
    await client.delete('/api/attempts/questions/$id');
  }

  /// POST /api/attempts/papers/{id}/restore
  Future<void> restorePaperAttempt(int id) async {
    await client.post('/api/attempts/papers/$id/restore');
  }

  /// POST /api/attempts/questions/{id}/restore
  Future<void> restoreQuestionAttempt(int id) async {
    await client.post('/api/attempts/questions/$id/restore');
  }
}
