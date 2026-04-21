/// Question metadata from discovery API.
class QuestionMetadata {
  const QuestionMetadata({
    required this.questionId,
    required this.paperId,
    required this.paperName,
    required this.examDate,
    required this.questionNumber,
    required this.totalMarks,
  });

  factory QuestionMetadata.fromJson(Map<String, dynamic> json) {
    // Parse exam_date with error handling
    // Expected format: ISO 8601 (YYYY-MM-DD) from backend
    DateTime examDate;
    try {
      examDate = DateTime.parse(json['exam_date'] as String);
    } catch (e) {
      throw FormatException(
        'Invalid exam_date format: ${json['exam_date']}. '
        'Expected ISO 8601 format (YYYY-MM-DD).',
      );
    }

    return QuestionMetadata(
      questionId: json['question_id'] as int,
      paperId: json['paper_id'] as int,
      paperName: json['paper_name'] as String,
      examDate: examDate,
      questionNumber: json['question_number'] as int,
      totalMarks: json['total_marks'] as int,
    );
  }

  final int questionId;
  final int paperId;
  final String paperName;
  final DateTime examDate;
  final int questionNumber;
  final int totalMarks;
}
