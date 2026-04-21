import 'package:flutter/material.dart';
import 'package:paperlab/models/question_part_result.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/utils/string_utils.dart';
import 'package:paperlab/widgets/latex_text.dart';
import 'package:paperlab/widgets/question_results/content_block_widget.dart';

/// Displays question part content with inline part label.
///
/// Extracted from QuestionPartWidget._PartContent for reuse in the
/// Question Section of the redesigned Question Results Screen.
///
/// Handles:
/// - Inline label with first text block (e.g., "a) Find the value...")
/// - Label above first diagram block (can't inline with image)
/// - Remaining content blocks below
/// - NULL part (no label)
class QuestionPartContentWidget extends StatelessWidget {
  const QuestionPartContentWidget({required this.part, super.key});

  /// Question part with content blocks
  final QuestionPartResult part;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      // First content block with inline part label
      if (part.contentBlocks.isNotEmpty)
        _FirstContentBlockWithLabel(part: part),

      // Remaining content blocks
      if (part.contentBlocks.length > 1)
        ...part.contentBlocks
            .skip(1)
            .map((block) => ContentBlockWidget(block: block)),
    ],
  );
}

/// First content block with part label inline (for text) or above (for
/// diagrams).
///
/// Text example: "a) Find the value of x"
/// Diagram example:
/// ```
/// a)
/// [diagram]
/// ```
class _FirstContentBlockWithLabel extends StatelessWidget {
  const _FirstContentBlockWithLabel({required this.part});

  final QuestionPartResult part;

  @override
  Widget build(BuildContext context) {
    final firstBlock = part.contentBlocks.first;

    if (firstBlock.isText) {
      final questionText = capitalizeFirst(firstBlock.text!);

      // For parts with labels, prefix the text and render with LaTeX support
      // Using LatexText for all text to ensure LaTeX expressions render
      // Markdown bold (**...**) for part label to maintain visual hierarchy
      final displayText = part.isNullPart
          ? questionText
          : '**${part.partLabel}** $questionText';

      return Padding(
        padding: const EdgeInsets.only(bottom: AppSpacing.sm),
        child: LatexText(
          displayText,
          style: AppTypography.body.copyWith(color: AppColors.textPrimary),
        ),
      );
    } else {
      // For diagrams, show label above (can't inline with image)
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!part.isNullPart) ...[
            Text(
              part.partLabel,
              style: AppTypography.body.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
          ],
          ContentBlockWidget(block: firstBlock),
        ],
      );
    }
  }
}
