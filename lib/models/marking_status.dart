/// Paper marking status from API.
class PaperStatus {
  const PaperStatus({
    required this.attemptId,
    required this.status,
    this.progress,
    this.error,
  });

  factory PaperStatus.fromJson(Map<String, dynamic> json) => PaperStatus(
    attemptId: json['attempt_id'] as int,
    status: PaperStatusType.fromString(json['status'] as String),
    progress: json['progress'] != null
        ? ProgressInfo.fromJson(json['progress'] as Map<String, dynamic>)
        : null,
    error: json['error'] != null
        ? ErrorInfo.fromJson(json['error'] as Map<String, dynamic>)
        : null,
  );

  final int attemptId;
  final PaperStatusType status;
  final ProgressInfo? progress;
  final ErrorInfo? error;
}

enum PaperStatusType {
  draft,
  submitted,
  marking,
  readyForGrading,
  completed,
  failed;

  static PaperStatusType fromString(String s) => switch (s) {
    'draft' => draft,
    'submitted' => submitted,
    'marking' => marking,
    'ready_for_grading' => readyForGrading,
    'completed' => completed,
    'failed' => failed,
    _ => throw ArgumentError('Unknown status: $s'),
  };

  bool get isTerminal => this == completed || this == failed;
}

class ProgressInfo {
  const ProgressInfo({
    required this.questionsTotal,
    required this.questionsCompleted,
    required this.questionsInProgress,
    required this.questionsFailed,
  });

  factory ProgressInfo.fromJson(Map<String, dynamic> json) => ProgressInfo(
    questionsTotal: json['questions_total'] as int,
    questionsCompleted: json['questions_completed'] as int,
    questionsInProgress: json['questions_in_progress'] as int,
    questionsFailed: json['questions_failed'] as int,
  );

  final int questionsTotal;
  final int questionsCompleted;
  final int questionsInProgress;
  final int questionsFailed;
}

class ErrorInfo {
  const ErrorInfo({required this.message, required this.failedQuestions});

  factory ErrorInfo.fromJson(Map<String, dynamic> json) => ErrorInfo(
    message: json['message'] as String,
    failedQuestions: (json['failed_questions'] as List)
        .map((q) => FailedQuestion.fromJson(q as Map<String, dynamic>))
        .toList(),
  );

  final String message;
  final List<FailedQuestion> failedQuestions;
}

class FailedQuestion {
  const FailedQuestion({
    required this.questionNumber,
    required this.errorType,
    required this.errorMessage,
  });

  factory FailedQuestion.fromJson(Map<String, dynamic> json) => FailedQuestion(
    questionNumber: json['question_number'] as int,
    errorType: json['error_type'] as String,
    errorMessage: json['error_message'] as String,
  );

  final int questionNumber;
  final String errorType;
  final String errorMessage;
}

/// Question marking status from API.
class QuestionStatus {
  const QuestionStatus({
    required this.attemptId,
    required this.status,
    this.error,
  });

  factory QuestionStatus.fromJson(Map<String, dynamic> json) => QuestionStatus(
    attemptId: json['attempt_id'] as int,
    status: QuestionStatusType.fromString(json['status'] as String),
    error: json['error'] != null
        ? QuestionErrorInfo.fromJson(json['error'] as Map<String, dynamic>)
        : null,
  );

  final int attemptId;
  final QuestionStatusType status;
  final QuestionErrorInfo? error;
}

enum QuestionStatusType {
  draft,
  submitted,
  completed,
  failed;

  static QuestionStatusType fromString(String s) => switch (s) {
    'draft' => draft,
    'submitted' => submitted,
    'completed' => completed,
    'failed' => failed,
    _ => throw ArgumentError('Unknown status: $s'),
  };

  bool get isTerminal => this == completed || this == failed;
}

class QuestionErrorInfo {
  const QuestionErrorInfo({
    required this.errorType,
    required this.errorMessage,
    required this.canRetry,
  });

  factory QuestionErrorInfo.fromJson(Map<String, dynamic> json) =>
      QuestionErrorInfo(
        errorType: json['error_type'] as String,
        errorMessage: json['error_message'] as String,
        canRetry: json['can_retry'] as bool,
      );

  final String errorType;
  final String errorMessage;
  final bool canRetry;
}
