import 'package:flutter/material.dart';
import 'package:paperlab/models/mark_criterion_result.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/utils/string_utils.dart';
import 'package:paperlab/widgets/latex_text.dart';
import 'package:paperlab/widgets/question_results/content_block_widget.dart';

/// Mark criterion card for Question Results Screen.
///
/// Displays mark scheme, awarded marks, and feedback with:
/// - Colored left accent strip (green=100%, amber=<100%, gray=GENERAL)
/// - Title with mark type and score (e.g., "METHOD • 2/3")
/// - Mark scheme description (lighter, supporting context)
/// - Feedback (bolder, primary insight)
///
/// Visual structure (no box, accent strip only):
/// ```
/// ■ METHOD • 2/3                    [semibold, primary]
///   Correct method for adding...    [small, secondary - mark scheme]
///   You correctly added 90 + 10...  [medium weight, primary - feedback]
/// ```
///
/// Typography hierarchy:
/// - Label + score: body 16px semibold (what criterion)
/// - Mark scheme: bodySmall 14px regular gray (what was expected)
/// - Feedback: body 16px medium (what you did - the insight)
///
/// GENERAL criteria (guidance only):
/// - Neutral gray accent strip
/// - No score display (hides "• X/Y")
/// - Italicized feedback text
///
/// Design rationale:
/// - Accent strip retained for status communication (research-backed pattern)
/// - Box removed to reduce visual weight
/// - Typography creates hierarchy without decoration
/// - Feedback emphasized as the actionable insight
class QuestionResultMarkCriterionCard extends StatelessWidget {
  const QuestionResultMarkCriterionCard({required this.criterion, super.key});

  /// Mark criterion with result and feedback
  final MarkCriterionResult criterion;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: AppSpacing.lg),
    child: Container(
      // Left border only for accent strip effect
      decoration: BoxDecoration(
        border: Border(
          left: BorderSide(
            color: _getAccentColor(),
            width: AppSpacing.accentStripWidth,
          ),
        ),
      ),
      padding: const EdgeInsets.only(left: AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title: METHOD • 2/3 (or just GENERAL for guidance criteria)
          Text(
            criterion.isGeneral
                ? criterion.label
                : '${criterion.label} • ${criterion.marksAwarded}/${criterion.marksAvailable}',
            style: AppTypography.body.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),

          // Mark scheme description (lighter, supporting)
          if (criterion.contentBlocks.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.xs),
            _MarkSchemeContent(criterion: criterion),
          ],

          // Feedback (bolder, primary insight)
          if (criterion.feedback.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.sm),
            LatexText(
              capitalizeFirst(criterion.feedback),
              style: AppTypography.body.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w500,
                fontStyle: criterion.isGeneral ? FontStyle.italic : null,
              ),
            ),
          ],
        ],
      ),
    ),
  );

  /// Get accent strip color for criterion
  /// Green = 100%, Amber = anything less than 100%
  /// Neutral gray = GENERAL criteria (guidance only, not scored)
  Color _getAccentColor() {
    if (criterion.isGeneral) {
      return AppColors.border; // Neutral gray - guidance only
    } else if (criterion.isFullyAwarded) {
      return AppColors.success; // Green - fully correct (100%)
    } else {
      return AppColors.error; // Amber - not fully correct (<100%)
    }
  }
}

/// Mark scheme content section.
///
/// Displays content blocks with lighter styling (supporting context).
/// Typography: bodySmall 14px, textSecondary color.
/// Handles both text and diagram content blocks.
class _MarkSchemeContent extends StatelessWidget {
  const _MarkSchemeContent({required this.criterion});

  final MarkCriterionResult criterion;

  /// Lighter text style for mark scheme (supporting context)
  static final _markSchemeStyle = AppTypography.bodySmall.copyWith(
    color: AppColors.textSecondary,
  );

  @override
  Widget build(BuildContext context) {
    if (criterion.contentBlocks.isEmpty) return const SizedBox.shrink();

    final firstBlock = criterion.contentBlocks.first;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // First content block (inline)
        ContentBlockWidget(
          block: firstBlock,
          bottomPadding: 0,
          textStyle: _markSchemeStyle,
        ),

        // Additional content blocks (if any)
        if (criterion.contentBlocks.length > 1)
          ...criterion.contentBlocks
              .skip(1)
              .map(
                (block) => Padding(
                  padding: const EdgeInsets.only(top: AppSpacing.xs),
                  child: ContentBlockWidget(
                    block: block,
                    bottomPadding: 0,
                    textStyle: _markSchemeStyle,
                  ),
                ),
              ),
      ],
    );
  }
}
