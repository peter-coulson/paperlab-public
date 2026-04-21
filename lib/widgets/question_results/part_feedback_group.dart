import 'package:flutter/material.dart';
import 'package:paperlab/models/question_part_result.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/latex_text.dart';
import 'package:paperlab/widgets/question_results/question_result_mark_criterion_card.dart';

/// Part feedback grouping for the Results section.
///
/// Shows part label with inline score, followed by criteria.
///
/// Visual structure:
/// ```
/// a)  3/4
/// Answer: 15.12
/// ■ METHOD • 2/3
///   ...
/// ```
///
/// Design: Clean, simple layout with consistent body typography.
///
/// Edge cases:
/// - NULL part criteria: No part header shown
/// - Parts with no criteria: Not rendered (filtered out by parent)
class PartFeedbackGroup extends StatelessWidget {
  const PartFeedbackGroup({required this.part, super.key});

  /// Question part with marking results
  final QuestionPartResult part;

  @override
  Widget build(BuildContext context) {
    // Don't render if no criteria
    if (part.criteria.isEmpty) {
      return const SizedBox.shrink();
    }

    final hasExpectedAnswer =
        part.expectedAnswer != null && part.expectedAnswer!.isNotEmpty;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Part header with inline score (skip for NULL part)
          if (!part.isNullPart) ...[
            Row(
              children: [
                Text(
                  part.partLabel,
                  style: AppTypography.body.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  '${part.subtotal}/${part.subtotalAvailable}',
                  style: AppTypography.body.copyWith(
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
          ],

          // Answer (if available)
          if (hasExpectedAnswer) ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Answer: ',
                  style: AppTypography.body.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                Expanded(
                  child: LatexText(
                    part.expectedAnswer!,
                    style: AppTypography.body.copyWith(
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
          ],

          // Criterion cards
          ...part.criteria.map(
            (criterion) =>
                QuestionResultMarkCriterionCard(criterion: criterion),
          ),
        ],
      ),
    );
  }
}
