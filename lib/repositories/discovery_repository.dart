import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/models/question_metadata.dart';
import 'package:paperlab/repositories/api_client.dart';

/// Discovery API for selection screens.
class DiscoveryRepository {
  const DiscoveryRepository({required this.client});

  final ApiClient client;

  /// GET /api/papers (with optional filters).
  Future<List<PaperMetadata>> listPapers({
    String? examBoard,
    String? examLevel,
    String? subject,
  }) async {
    // Build query parameters
    final params = <String, String>{};
    if (examBoard != null) params['exam_board'] = examBoard;
    if (examLevel != null) params['exam_level'] = examLevel;
    if (subject != null) params['subject'] = subject;

    // Build query string
    final queryString = params.isNotEmpty
        ? '?${params.entries.map((e) => '${e.key}=${e.value}').join('&')}'
        : '';

    final responseBody = await client.get('/api/papers$queryString');
    final data = client.parseJson(responseBody);
    final papersList = data['papers'] as List<dynamic>;

    return papersList
        .map((p) => PaperMetadata.fromJson(p as Map<String, dynamic>))
        .toList();
  }

  /// GET /api/questions (with optional filters).
  Future<List<QuestionMetadata>> listQuestions({
    String? examBoard,
    String? examLevel,
    String? subject,
    int? paperId,
  }) async {
    // Build query parameters
    final params = <String, String>{};
    if (examBoard != null) params['exam_board'] = examBoard;
    if (examLevel != null) params['exam_level'] = examLevel;
    if (subject != null) params['subject'] = subject;
    if (paperId != null) params['paper_id'] = paperId.toString();

    // Build query string
    final queryString = params.isNotEmpty
        ? '?${params.entries.map((e) => '${e.key}=${e.value}').join('&')}'
        : '';

    final responseBody = await client.get('/api/questions$queryString');
    final data = client.parseJson(responseBody);
    final questionsList = data['questions'] as List<dynamic>;

    return questionsList
        .map((q) => QuestionMetadata.fromJson(q as Map<String, dynamic>))
        .toList();
  }
}
