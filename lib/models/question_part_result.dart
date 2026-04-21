import 'package:paperlab/models/content_block.dart';
import 'package:paperlab/models/mark_criterion_result.dart';

/// Question part with content and marking results.
/// Corresponds to SQL table: question_parts
///
/// Three patterns:
/// 1. NULL part (general context): partLetter=null, subPartLetter=null
/// 2. Part only: partLetter='a', subPartLetter=null
/// 3. Sub-part: partLetter='a', subPartLetter='i'
///
/// Examples:
/// - NULL part (display_order=0): General context, may have GENERAL criteria
/// - Part a): partLetter='a', subPartLetter=null
/// - Part a) i): partLetter='a', subPartLetter='i'
class QuestionPartResult {
  const QuestionPartResult({
    required this.partLetter,
    required this.subPartLetter,
    required this.expectedAnswer,
    required this.contentBlocks,
    required this.criteria,
  });

  factory QuestionPartResult.fromJson(Map<String, dynamic> json) =>
      QuestionPartResult(
        partLetter: json['part_letter'] as String?,
        subPartLetter: json['sub_part_letter'] as String?,
        expectedAnswer: json['expected_answer'] as String?,
        contentBlocks: (json['content_blocks'] as List)
            .map((b) => ContentBlock.fromJson(b as Map<String, dynamic>))
            .toList(),
        criteria: (json['criteria'] as List)
            .map((c) => MarkCriterionResult.fromJson(c as Map<String, dynamic>))
            .toList(),
      );

  /// Part letter (null for NULL part, 'a'/'b'/'c' for lettered parts)
  final String? partLetter;

  /// Sub-part letter (null for main parts, 'i'/'ii'/'iii' for sub-parts)
  final String? subPartLetter;

  /// Expected answer from mark scheme (e.g., "$x = 5$", "42 cm")
  final String? expectedAnswer;

  /// Content blocks for this part (question text/diagrams)
  final List<ContentBlock> contentBlocks;

  /// Mark criteria with results for this part
  final List<MarkCriterionResult> criteria;

  /// Display label for this part
  /// Examples: '' (NULL part), 'a)', 'a) ii)'
  /// Format: lowercase with no space before sub-part
  String get partLabel {
    if (partLetter == null) return '';
    if (subPartLetter == null) return '$partLetter)';
    return '$partLetter) $subPartLetter)';
  }

  /// Whether this is the NULL part (display_order=0)
  bool get isNullPart => partLetter == null;

  /// Whether this part has displayable content
  /// NULL part shown if: has content blocks OR has non-GENERAL criteria
  /// Regular parts always shown
  bool get hasContent {
    if (!isNullPart) return true; // Regular parts always shown
    return contentBlocks.isNotEmpty || criteria.any((c) => !c.isGeneral);
  }

  /// Subtotal marks awarded for this part (sum of criterion marks)
  int get subtotal => criteria.fold(0, (sum, c) => sum + c.marksAwarded);

  /// Subtotal marks available for this part (sum of criterion max marks)
  int get subtotalAvailable =>
      criteria.fold(0, (sum, c) => sum + c.marksAvailable);

  /// Whether to display subtotal (parts with sub-parts show subtotals)
  /// Determined by context (if multiple parts share same partLetter)
  /// Implementation note: QuestionResultsScreen will compute this
  /// from full parts list
}
