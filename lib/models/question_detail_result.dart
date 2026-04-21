import 'package:paperlab/models/question_part_result.dart';
import 'package:paperlab/models/student_work_image.dart';
import 'package:paperlab/utils/exam_date_utils.dart';
import 'package:paperlab/utils/string_utils.dart';

/// Complete question marking results with hierarchical structure.
/// Top-level model for Question Results Screen.
///
/// Corresponds to SQL query joining:
/// - questions, question_parts, question_content_blocks
/// - mark_criteria, mark_criteria_content_blocks
/// - question_marking_results, marking_attempts
/// - submission_images
///
/// M5: Hardcoded mock data
/// M6: Fetched from GET /api/question-results/{submission_id}
class QuestionDetailResult {
  const QuestionDetailResult({
    required this.questionNumber,
    required this.paperName,
    required this.examDate,
    required this.totalAwarded,
    required this.totalAvailable,
    required this.parts,
    required this.images,
  }) : assert(
         totalAwarded >= 0 && totalAwarded <= totalAvailable,
         'Total awarded must be between 0 and totalAvailable',
       ),
       assert(totalAvailable > 0, 'Total available must be positive');

  factory QuestionDetailResult.fromJson(Map<String, dynamic> json) =>
      QuestionDetailResult(
        questionNumber: json['question_number'] as int,
        paperName: json['paper_name'] as String,
        examDate: DateTime.parse(json['exam_date'] as String),
        totalAwarded: json['total_awarded'] as int,
        totalAvailable: json['total_available'] as int,
        parts: (json['parts'] as List)
            .map((p) => QuestionPartResult.fromJson(p as Map<String, dynamic>))
            .toList(),
        images: (json['images'] as List)
            .map((i) => StudentWorkImage.fromJson(i as Map<String, dynamic>))
            .toList(),
      );

  /// Question number (e.g., 3 for "Q3")
  final int questionNumber;

  /// Paper name for display (e.g., "P1 June 2023")
  final String paperName;

  /// Exam date for the paper
  final DateTime examDate;

  /// Total marks awarded across all parts
  final int totalAwarded;

  /// Total marks available across all parts
  final int totalAvailable;

  /// Question parts in display order (includes NULL part if present)
  /// Parts are ordered by display_order from SQL
  final List<QuestionPartResult> parts;

  /// Student work images ordered by sequence
  final List<StudentWorkImage> images;

  /// Score label for display (e.g., "5/6")
  String get scoreLabel => '$totalAwarded/$totalAvailable';

  /// Question identifier for header (e.g., "Q3 Paper 3 Nov 2023")
  /// Formats paper name and exam date consistently with home screen display
  String get questionLabel {
    final paperType = extractPaperType(paperName);
    final formattedDate = formatExamDateFromDateTime(examDate);
    return 'Q$questionNumber $paperType $formattedDate';
  }

  /// Question title only (e.g., "Question 3")
  /// Used in new header design for clean separation
  String get questionTitle => 'Question $questionNumber';

  /// Paper context without question number (e.g., "Paper 3 Nov 2023")
  /// Used in new header design as subtitle
  String get paperContext {
    final paperType = extractPaperType(paperName);
    final formattedDate = formatExamDateFromDateTime(examDate);
    return '$paperType $formattedDate';
  }

  /// Percentage score (0-100)
  double get percentage => (totalAwarded / totalAvailable) * 100;
}
