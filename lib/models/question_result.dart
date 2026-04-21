/// Question result model for displaying individual question scores in Paper
/// Results Screen.
///
/// Contains:
/// - Question number (e.g., 1, 2, 3)
/// - Question attempt ID for navigation to question details
/// - Marks awarded vs available (e.g., 3/6)
///
/// Used in PaperResult model to represent list of question results.
class QuestionResult {
  const QuestionResult({
    required this.questionNumber,
    required this.questionAttemptId,
    required this.awarded,
    required this.available,
  });

  factory QuestionResult.fromJson(Map<String, dynamic> json) => QuestionResult(
    questionNumber: json['question_number'] as int,
    questionAttemptId: json['question_attempt_id'] as int,
    awarded: json['awarded'] as int,
    available: json['available'] as int,
  );

  final int questionNumber;
  final int questionAttemptId;
  final int awarded;
  final int available;

  /// Display label for question (e.g., "Question 1", "Question 2")
  String get displayLabel => 'Question $questionNumber';
}
