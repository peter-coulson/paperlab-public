import 'package:flutter/material.dart';
import 'package:paperlab/models/question_detail_result.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/question_results/question_part_content_widget.dart';

/// The Question section of the Question Results Screen.
///
/// Shows the complete question exactly as it appeared on the exam paper,
/// without any marking feedback or criteria.
///
/// Visual structure:
/// ```
/// THE QUESTION
/// ───────────────────────────
/// a) Find the value of x when y = 5
///    [diagram if present]
///
/// b) Hence, explain why the gradient must be
///    negative.
/// ```
///
/// Features:
/// - Section header: "THE QUESTION"
/// - All question parts in order
/// - Part labels inline with content
/// - LaTeX rendering
/// - Diagrams inline where they appear
/// - Clean, neutral styling (not evaluation)
class QuestionSection extends StatelessWidget {
  const QuestionSection({required this.result, super.key});

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
          'Question',
          color: AppColors.textSecondary,
        ),
      ),
      const SizedBox(height: AppSpacing.md),

      // Question parts (content only, no criteria)
      ...result.parts
          .where((part) => part.contentBlocks.isNotEmpty)
          .map(
            (part) => Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.md),
              child: QuestionPartContentWidget(part: part),
            ),
          ),
    ],
  );
}
