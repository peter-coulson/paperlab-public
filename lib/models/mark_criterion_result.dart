import 'package:paperlab/models/content_block.dart';

/// Mark criterion with marking result and feedback.
/// Corresponds to SQL tables:
/// - mark_criteria (criterion definition)
/// - mark_criteria_content_blocks (criterion description)
/// - question_marking_results (marks awarded and feedback)
///
/// Examples:
/// - METHOD • 2/3: Correct method for adding all sides
/// - ACCURACY • 0/1: Correct answer 80
/// - GENERAL: Accept equivalent forms throughout this question
class MarkCriterionResult {
  const MarkCriterionResult({
    required this.markTypeCode,
    required this.displayName,
    required this.sequenceNumber,
    required this.marksAwarded,
    required this.marksAvailable,
    required this.contentBlocks,
    required this.feedback,
  }) : assert(
         marksAwarded >= 0 && marksAwarded <= marksAvailable,
         'Marks awarded must be between 0 and marksAvailable',
       ),
       assert(marksAvailable >= 0, 'Marks available must be non-negative');

  factory MarkCriterionResult.fromJson(Map<String, dynamic> json) =>
      MarkCriterionResult(
        markTypeCode: json['mark_type_code'] as String,
        displayName: json['display_name'] as String,
        sequenceNumber: json['sequence_number'] as int,
        marksAwarded: json['marks_awarded'] as int,
        marksAvailable: json['marks_available'] as int,
        contentBlocks: (json['content_blocks'] as List)
            .map((b) => ContentBlock.fromJson(b as Map<String, dynamic>))
            .toList(),
        feedback: json['feedback'] as String,
      );

  /// Mark type code from mark_types table
  /// Common values: 'M' (Method), 'A' (Accuracy),
  /// 'B' (Both), 'P' (Process), 'C' (Communication)
  /// Special value: 'GENERAL' (guidance only, not scored)
  final String markTypeCode;

  /// Display name from mark_types.display_name (ALL CAPS for visual hierarchy)
  /// Examples: 'METHOD', 'ACCURACY', 'BOTH', 'PROCESS', 'COMMUNICATION'
  /// Special value: 'GENERAL' for guidance criteria
  /// M6: This will come from the API (joined from mark_types table)
  final String displayName;

  /// Sequence number within this mark type for the question
  /// Used to generate labels: M1, M2, A1, A2...
  /// Note: Numbering is sequential within mark type, not across the question
  /// Example: M1, A1, M2, A2 (NOT M1, M2, A1, A2)
  final int sequenceNumber;

  /// Marks awarded by the marking system (0 to marksAvailable)
  final int marksAwarded;

  /// Maximum marks available for this criterion
  final int marksAvailable;

  /// Content blocks describing the criterion
  /// May contain LaTeX in text blocks
  /// Example: "Correct use of formula that all angles add up to $180°$"
  final List<ContentBlock> contentBlocks;

  /// Feedback from the marking system
  /// Example: "Student used formula $90 + 10 + B = 180$"
  final String feedback;

  /// Display label for this criterion
  /// Examples: "METHOD", "ACCURACY", "GENERAL"
  String get label => displayName;

  /// Whether this is a GENERAL criterion (guidance only, not scored)
  bool get isGeneral => markTypeCode == 'GENERAL';

  /// Whether the student was awarded marks for this criterion
  bool get isAwarded => marksAwarded > 0;

  /// Whether the student was awarded full marks for this criterion
  bool get isFullyAwarded => marksAwarded == marksAvailable;

  /// Whether the student was awarded partial marks for this criterion
  bool get isPartiallyAwarded =>
      marksAwarded > 0 && marksAwarded < marksAvailable;
}
