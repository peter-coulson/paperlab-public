import 'package:paperlab/models/paper_attempt_state.dart';
import 'package:paperlab/utils/exam_date_utils.dart';
import 'package:paperlab/utils/string_utils.dart';

/// Paper attempt model for home screen display.
/// State is derived from timestamps (submitted_at, completed_at).
class PaperAttempt {
  const PaperAttempt({
    required this.id,
    required this.attemptUuid,
    required this.paperName,
    required this.examDate,
    required this.state,
    required this.createdAt,
    this.grade,
  });

  /// Factory from API JSON response.
  /// Derives state from timestamps.
  factory PaperAttempt.fromJson(Map<String, dynamic> json) {
    final submittedAt = json['submitted_at'] != null
        ? DateTime.parse(json['submitted_at'] as String)
        : null;
    final completedAt = json['completed_at'] != null
        ? DateTime.parse(json['completed_at'] as String)
        : null;
    final examDateStr = json['exam_date'] as String?;

    // Validate required field
    if (examDateStr == null || examDateStr.isEmpty) {
      throw FormatException(
        'Missing required field: exam_date. '
        'Paper attempt ${json['id']} has no exam date.',
      );
    }

    // Derive state from timestamps
    final state = _deriveState(
      submittedAt: submittedAt,
      completedAt: completedAt,
    );

    return PaperAttempt(
      id: json['id'] as int,
      attemptUuid: json['attempt_uuid'] as String,
      paperName: json['paper_name'] as String,
      examDate: DateTime.parse(examDateStr),
      state: state,
      createdAt: DateTime.parse(json['created_at'] as String),
      grade: json['grade'] as String?,
    );
  }

  final int id;
  final String attemptUuid;
  final String paperName;
  final DateTime examDate;
  final PaperAttemptState state;
  final DateTime createdAt;
  final String? grade; // Only populated for completed papers

  /// Get formatted display string for list items.
  /// Format: "Paper 3 Nov 2023"
  /// Extracts paper type from paperName and formats exam date.
  String get displayName {
    final paperType = extractPaperType(paperName);
    final formattedDate = formatExamDateFromDateTime(examDate);
    return '$paperType $formattedDate';
  }

  /// Derive state from timestamps (matches backend logic).
  static PaperAttemptState _deriveState({
    DateTime? submittedAt,
    DateTime? completedAt,
  }) {
    if (completedAt != null) return PaperAttemptState.complete;
    if (submittedAt != null) return PaperAttemptState.marking;
    return PaperAttemptState.draft;
  }
}
