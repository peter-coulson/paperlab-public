import 'package:paperlab/models/question_result.dart';
import 'package:paperlab/utils/exam_date_utils.dart';
import 'package:paperlab/utils/string_utils.dart';

/// Paper result model for displaying complete paper marking results.
///
/// Contains:
/// - Paper name (e.g., "P3 NOV 2023")
/// - Total marks awarded vs available (e.g., 50/80)
/// - Grade achieved (e.g., '6', 'U', or null if not calculated)
/// - List of individual question results
///
/// Used in Paper Results Screen to display complete marking feedback.
class PaperResult {
  const PaperResult({
    required this.attemptId,
    required this.paperName,
    required this.examDate,
    required this.totalAwarded,
    required this.totalAvailable,
    required this.percentage,
    required this.grade,
    required this.questions,
  });

  factory PaperResult.fromJson(Map<String, dynamic> json) => PaperResult(
    attemptId: json['attempt_id'] as int,
    paperName: json['paper_name'] as String,
    examDate: DateTime.parse(json['exam_date'] as String),
    totalAwarded: json['total_awarded'] as int,
    totalAvailable: json['total_available'] as int,
    percentage: (json['percentage'] as num).toDouble(),
    grade: json['grade'] as String?,
    questions: (json['questions'] as List)
        .map((q) => QuestionResult.fromJson(q as Map<String, dynamic>))
        .toList(),
  );

  final int attemptId;
  final String paperName;
  final DateTime examDate;
  final int totalAwarded;
  final int totalAvailable;
  final double percentage;
  final String? grade;
  final List<QuestionResult> questions;

  /// Get formatted display string for screen headers.
  /// Format: "Paper 3 Nov 2023"
  /// Extracts paper type from paperName and formats exam date.
  String get displayName {
    final paperType = extractPaperType(paperName);
    final formattedDate = formatExamDateFromDateTime(examDate);
    return '$paperType $formattedDate';
  }

  /// Combined display label for grade and score
  /// (e.g., "Grade 6 • 50/80 (62.5%)" or "50/80 (62.5%)" if no grade)
  String get resultLabel {
    final percentageStr = percentage.toStringAsFixed(1);
    if (grade != null) {
      return 'Grade $grade • $totalAwarded/$totalAvailable ($percentageStr%)';
    }
    return '$totalAwarded/$totalAvailable ($percentageStr%)';
  }
}
