import 'package:paperlab/models/question_attempt_state.dart';
import 'package:paperlab/models/score.dart';
import 'package:paperlab/utils/exam_date_utils.dart';
import 'package:paperlab/utils/string_utils.dart';

/// Practice question attempt model for home screen display.
/// State is derived from timestamps (submitted_at, completed_at).
class QuestionAttempt {
  const QuestionAttempt({
    required this.id,
    required this.attemptUuid,
    required this.questionName,
    required this.paperName,
    required this.examDate,
    required this.state,
    required this.createdAt,
    this.score,
  });

  /// Factory from API JSON response.
  /// Derives state from timestamps.
  factory QuestionAttempt.fromJson(Map<String, dynamic> json) {
    final completedAt = json['completed_at'] != null
        ? DateTime.parse(json['completed_at'] as String)
        : null;
    final examDateStr = json['exam_date'] as String?;

    // Validate required field
    if (examDateStr == null || examDateStr.isEmpty) {
      throw FormatException(
        'Missing required field: exam_date. '
        'Question attempt ${json['id']} has no exam date.',
      );
    }

    // Derive state from timestamps
    // Practice questions go straight to marking on submit, no draft state
    final state = _deriveState(completedAt: completedAt);

    // Parse score if available (only for completed attempts)
    final marksAwarded = json['marks_awarded'] as int?;
    final marksAvailable = json['marks_available'] as int?;
    final score = (marksAwarded != null && marksAvailable != null)
        ? Score(awarded: marksAwarded, available: marksAvailable)
        : null;

    return QuestionAttempt(
      id: json['id'] as int,
      attemptUuid: json['attempt_uuid'] as String,
      questionName: json['question_display'] as String,
      paperName: json['paper_name'] as String,
      examDate: DateTime.parse(examDateStr),
      state: state,
      createdAt: DateTime.parse(json['created_at'] as String),
      score: score,
    );
  }

  final int id;
  final String attemptUuid;
  final String questionName;
  final String paperName;
  final DateTime examDate;
  final QuestionAttemptState state;
  final DateTime createdAt;
  final Score? score; // Only populated for completed questions

  /// Get formatted display string for list items.
  /// Format: "Q3 Paper 3 Nov 2023"
  /// Combines question number, paper type, and exam date.
  String get displayName {
    final paperType = extractPaperType(paperName);
    final formattedDate = formatExamDateFromDateTime(examDate);
    return '$questionName $paperType $formattedDate';
  }

  /// Derive state from timestamps (matches backend logic).
  /// Practice questions only have marking and complete states.
  static QuestionAttemptState _deriveState({DateTime? completedAt}) {
    if (completedAt != null) return QuestionAttemptState.complete;
    // Practice questions go straight to marking on submit
    return QuestionAttemptState.marking;
  }
}
