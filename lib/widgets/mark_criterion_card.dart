import 'package:flutter/material.dart';
import 'package:paperlab/models/mark_criterion_result.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/latex_text.dart';

/// Display a single mark criterion with result and feedback.
///
/// Visual structure:
/// ```
/// +-------------------------------------------------------+
/// | M1 (1/1): Correct method for adding all sides         |
/// | [Additional content blocks if present]                |
/// | Feedback: Student correctly added 3 + 4 + 5           |
/// +-------------------------------------------------------+
/// ```
///
/// Features:
/// - Color-coded left border (green=awarded, amber=not awarded, purple=partial)
/// - GENERAL criteria styled as guidance (gray, no border)
/// - LaTeX support in criterion description and feedback
/// - Diagram placeholders for diagram content blocks
///
/// Used in: Question Results Screen (multiple per part)
class MarkCriterionCard extends StatelessWidget {
  const MarkCriterionCard({required this.criterion, super.key});

  final MarkCriterionResult criterion;

  @override
  Widget build(BuildContext context) {
    // GENERAL criteria styled differently (guidance only, not scored)
    if (criterion.isGeneral) {
      return _buildGeneralCriterion();
    }

    return Container(
      decoration: BoxDecoration(
        color: AppColors.background,
        border: Border(left: BorderSide(color: _getBorderColor(), width: 4)),
        borderRadius: BorderRadius.circular(8),
      ),
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Label + score + first content block
          _buildHeader(),

          // Additional content blocks (if more than one)
          if (criterion.contentBlocks.length > 1) ...[
            const SizedBox(height: AppSpacing.sm),
            ..._buildAdditionalContentBlocks(),
          ],

          // Feedback
          if (criterion.feedback.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.sm),
            _buildFeedback(),
          ],
        ],
      ),
    );
  }

  /// Build GENERAL criterion (guidance only, no border)
  Widget _buildGeneralCriterion() => Padding(
    padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'GENERAL: ',
          style: AppTypography.label.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 4),
        ...criterion.contentBlocks.map((block) {
          if (block.isText) {
            return LatexText(
              block.text!,
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondary,
              ),
            );
          } else {
            return _buildDiagramPlaceholder(block.diagramDescription!);
          }
        }),
      ],
    ),
  );

  /// Build header with label, score, and first content block
  Widget _buildHeader() {
    final firstBlock = criterion.contentBlocks.first;
    final scoreText = '(${criterion.marksAwarded}/${criterion.marksAvailable})';
    final blockText = firstBlock.isText ? firstBlock.text! : '';

    return LatexText(
      '${criterion.label} $scoreText: $blockText',
      style: AppTypography.body.copyWith(color: AppColors.textPrimary),
    );
  }

  /// Build additional content blocks (skip first block, shown in header)
  List<Widget> _buildAdditionalContentBlocks() =>
      criterion.contentBlocks.skip(1).map((block) {
        if (block.isText) {
          return Padding(
            padding: const EdgeInsets.only(top: AppSpacing.xs),
            child: LatexText(
              block.text!,
              style: AppTypography.body.copyWith(color: AppColors.textPrimary),
            ),
          );
        } else {
          return Padding(
            padding: const EdgeInsets.only(top: AppSpacing.xs),
            child: _buildDiagramPlaceholder(block.diagramDescription!),
          );
        }
      }).toList();

  /// Build feedback section
  Widget _buildFeedback() => LatexText(
    'Feedback: ${criterion.feedback}',
    style: AppTypography.bodySmall.copyWith(color: AppColors.textSecondary),
  );

  /// Build diagram (show image if available, otherwise placeholder)
  Widget _buildDiagramPlaceholder(String description) => Container(
    padding: const EdgeInsets.all(AppSpacing.md),
    decoration: BoxDecoration(
      color: AppColors.backgroundSecondary,
      borderRadius: BorderRadius.circular(8),
    ),
    child: Row(
      children: [
        const Icon(
          Icons.image_outlined,
          color: AppColors.textSecondary,
          size: 20,
        ),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
          child: LatexText(
            description,
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
              fontStyle: FontStyle.italic,
            ),
          ),
        ),
      ],
    ),
  );

  /// Get border color based on award status
  Color _getBorderColor() {
    if (criterion.isFullyAwarded) {
      return AppColors.success; // Green - fully correct
    } else if (criterion.isPartiallyAwarded) {
      return AppColors.primaryLight; // Purple - partial credit
    } else {
      return AppColors.error; // Amber - incorrect
    }
  }
}
