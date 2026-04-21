import 'package:flutter/material.dart';
import 'package:paperlab/models/question_detail_result.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/question_results/part_feedback_group.dart';

/// Results section of the Question Results Screen.
///
/// Shows evaluation results with clear part-by-part breakdown.
/// Encompasses both marking criteria (what was expected) and
/// feedback (what the student did).
///
/// Visual structure:
/// ```
/// RESULTS
/// ───────────────────────────────────────────────
///
/// (a)                                       3/4
/// ├─ [Criterion: METHOD • 2/3]
/// └─ [Criterion: ACCURACY • 1/1]
///
/// (b)                                       2/2
/// └─ [Criterion: COMMUNICATION • 2/2]
/// ```
///
/// Features:
/// - Section header: "RESULTS"
/// - Part groupings with subtotal scores
/// - Criterion cards with accent strip status indicators
/// - Typography hierarchy: label (semibold) → scheme (light) →
///   feedback (medium)
/// - NULL part criteria shown without part header
class MarkingFeedbackSection extends StatelessWidget {
  const MarkingFeedbackSection({required this.result, super.key});

  /// Complete question detail result
  final QuestionDetailResult result;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      // Section header
      Semantics(
        header: true,
        child: AppTypography.sectionTitle(
          'Results',
          color: AppColors.textSecondary,
        ),
      ),
      const SizedBox(height: AppSpacing.md),

      // Part feedback groups (only parts with criteria)
      ...result.parts
          .where((part) => part.criteria.isNotEmpty)
          .map((part) => PartFeedbackGroup(part: part)),
    ],
  );
}
