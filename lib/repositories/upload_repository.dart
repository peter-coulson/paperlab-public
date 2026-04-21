import 'package:paperlab/exceptions/network_exceptions.dart';
import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/repositories/api_client.dart';

/// Response from presigned URL request.
class PresignedUrlResponse {
  const PresignedUrlResponse({
    required this.uploadUrl,
    required this.stagingKey,
  });

  factory PresignedUrlResponse.fromJson(Map<String, dynamic> json) =>
      PresignedUrlResponse(
        uploadUrl: json['upload_url'] as String,
        stagingKey: json['staging_key'] as String,
      );

  final String uploadUrl;
  final String stagingKey;
}

/// Response from create paper attempt request.
class CreatePaperAttemptResponse {
  const CreatePaperAttemptResponse({
    required this.id,
    required this.attemptUuid,
    required this.paperName,
    required this.examDate,
  });

  factory CreatePaperAttemptResponse.fromJson(Map<String, dynamic> json) =>
      CreatePaperAttemptResponse(
        id: json['id'] as int,
        attemptUuid: json['attempt_uuid'] as String,
        paperName: json['paper_name'] as String,
        examDate: DateTime.parse(json['exam_date'] as String),
      );

  final int id;
  final String attemptUuid;
  final String paperName;
  final DateTime examDate;
}

/// Response from paper question submission.
class PaperQuestionResponse {
  const PaperQuestionResponse({
    required this.questionAttemptId,
    required this.submissionId,
    required this.questionNumber,
  });

  factory PaperQuestionResponse.fromJson(Map<String, dynamic> json) =>
      PaperQuestionResponse(
        questionAttemptId: json['question_attempt_id'] as int,
        submissionId: json['submission_id'] as int,
        questionNumber: json['question_number'] as int,
      );

  final int questionAttemptId;
  final int submissionId;
  final int questionNumber;
}

/// Response from paper finalization.
class SubmitResponse {
  const SubmitResponse({required this.attemptId});

  factory SubmitResponse.fromJson(Map<String, dynamic> json) =>
      SubmitResponse(attemptId: json['attempt_id'] as int);

  final int attemptId;
}

/// Response from practice question submission.
class PracticeAttemptResponse {
  const PracticeAttemptResponse({
    required this.id,
    required this.attemptUuid,
    required this.submissionId,
  });

  factory PracticeAttemptResponse.fromJson(Map<String, dynamic> json) =>
      PracticeAttemptResponse(
        id: json['id'] as int,
        attemptUuid: json['attempt_uuid'] as String,
        submissionId: json['submission_id'] as int,
      );

  final int id;
  final String attemptUuid;
  final int submissionId;
}

/// Response from draft details request (for resuming drafts).
class DraftDetailsResponse {
  const DraftDetailsResponse({
    required this.id,
    required this.attemptUuid,
    required this.paperName,
    required this.examDate,
    required this.questionCount,
    required this.submittedQuestions,
  });

  factory DraftDetailsResponse.fromJson(Map<String, dynamic> json) {
    // Parse submitted_questions map (keys are strings in JSON, convert to int)
    final submittedQuestionsJson =
        json['submitted_questions'] as Map<String, dynamic>;
    final submittedQuestions = <int, int>{};
    for (final entry in submittedQuestionsJson.entries) {
      submittedQuestions[int.parse(entry.key)] = entry.value as int;
    }

    return DraftDetailsResponse(
      id: json['id'] as int,
      attemptUuid: json['attempt_uuid'] as String,
      paperName: json['paper_name'] as String,
      examDate: DateTime.parse(json['exam_date'] as String),
      questionCount: json['question_count'] as int,
      submittedQuestions: submittedQuestions,
    );
  }

  final int id;
  final String attemptUuid;
  final String paperName;
  final DateTime examDate;
  final int questionCount;
  final Map<int, int> submittedQuestions; // questionNumber → imageCount
}

/// R2 upload and submission operations.
class UploadRepository {
  const UploadRepository({required this.client});

  final ApiClient client;

  /// POST /api/uploads/presigned-url.
  /// Throws NetworkException on error.
  Future<PresignedUrlResponse> getPresignedUrl({
    required String attemptUuid,
    required String filename,
  }) async {
    final responseBody = await client.post(
      '/api/uploads/presigned-url',
      body: {'attempt_uuid': attemptUuid, 'filename': filename},
    );

    return PresignedUrlResponse.fromJson(client.parseJson(responseBody));
  }

  /// Upload file to R2 using presigned URL.
  /// Returns true on success.
  /// Throws NetworkException on error.
  Future<bool> uploadToR2({
    required String presignedUrl,
    required List<int> bytes,
  }) async {
    try {
      return await client.putBytes(
        presignedUrl,
        bytes,
        headers: {'Content-Type': 'image/jpeg'},
      );
    } catch (e) {
      // StorageConfigurationException has specific messages - pass through
      if (e is StorageConfigurationException) {
        rethrow;
      }
      // Convert other network exceptions to UploadException
      if (e is NetworkException) {
        throw UploadException('Failed to upload to storage: ${e.message}');
      }
      rethrow;
    }
  }

  /// POST /api/attempts/papers.
  /// Throws NetworkException on error.
  Future<CreatePaperAttemptResponse> createPaperAttempt({
    required String attemptUuid,
    required PaperMetadata paper,
  }) async {
    final responseBody = await client.post(
      '/api/attempts/papers',
      body: {
        'attempt_uuid': attemptUuid,
        'exam_board': paper.examBoard,
        'exam_level': paper.examLevel,
        'subject': paper.subject,
        'paper_code': paper.paperCode,
        'year': paper.year,
        'month': paper.month,
      },
    );

    return CreatePaperAttemptResponse.fromJson(client.parseJson(responseBody));
  }

  /// GET /api/attempts/papers/{id}.
  /// Fetch draft details for resuming paper upload.
  /// Throws NetworkException on error.
  Future<DraftDetailsResponse> getDraftDetails(int attemptId) async {
    final responseBody = await client.get('/api/attempts/papers/$attemptId');

    return DraftDetailsResponse.fromJson(client.parseJson(responseBody));
  }

  /// POST /api/attempts/papers/{id}/questions.
  /// Throws NetworkException on error.
  Future<PaperQuestionResponse> submitPaperQuestion({
    required int attemptId,
    required int questionNumber,
    required List<String> stagingKeys,
  }) async {
    final responseBody = await client.post(
      '/api/attempts/papers/$attemptId/questions',
      body: {'question_number': questionNumber, 'staging_keys': stagingKeys},
    );

    return PaperQuestionResponse.fromJson(client.parseJson(responseBody));
  }

  /// POST /api/attempts/papers/{id}/submit.
  /// Throws NetworkException on error.
  Future<SubmitResponse> finalizePaperAttempt(int attemptId) async {
    final responseBody = await client.post(
      '/api/attempts/papers/$attemptId/submit',
    );

    return SubmitResponse.fromJson(client.parseJson(responseBody));
  }

  /// POST /api/attempts/questions (single-phase practice).
  /// Throws NetworkException on error.
  Future<PracticeAttemptResponse> submitPracticeQuestion({
    required String attemptUuid,
    required int questionId,
    required List<String> stagingKeys,
  }) async {
    final responseBody = await client.post(
      '/api/attempts/questions',
      body: {
        'attempt_uuid': attemptUuid,
        'question_id': questionId,
        'staging_keys': stagingKeys,
      },
    );

    return PracticeAttemptResponse.fromJson(client.parseJson(responseBody));
  }
}
