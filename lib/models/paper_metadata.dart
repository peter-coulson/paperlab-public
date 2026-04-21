/// Paper metadata from discovery API.
class PaperMetadata {
  const PaperMetadata({
    required this.paperId,
    required this.examBoard,
    required this.examLevel,
    required this.subject,
    required this.paperCode,
    required this.displayName,
    required this.year,
    required this.month,
    required this.totalMarks,
    required this.questionCount,
  });

  factory PaperMetadata.fromJson(Map<String, dynamic> json) => PaperMetadata(
    paperId: json['paper_id'] as int,
    examBoard: json['exam_board'] as String,
    examLevel: json['exam_level'] as String,
    subject: json['subject'] as String,
    paperCode: json['paper_code'] as String,
    displayName: json['display_name'] as String,
    year: json['year'] as int,
    month: json['month'] as int,
    totalMarks: json['total_marks'] as int,
    questionCount: json['question_count'] as int,
  );

  final int paperId;
  final String examBoard;
  final String examLevel;
  final String subject;
  final String paperCode;
  final String displayName;
  final int year;
  final int month;
  final int totalMarks;
  final int questionCount;
}
