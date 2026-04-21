import 'package:flutter/material.dart';
import 'package:paperlab/models/question_attempt_state.dart';
import 'package:paperlab/models/score.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/list_items/list_item_container.dart';
import 'package:paperlab/widgets/list_items/pill_badge.dart';

/// Question list item with state badge.
/// See specs/SHARED_COMPONENTS.md for complete specification.
class QuestionListItem extends StatelessWidget {
  const QuestionListItem({
    required this.title,
    required this.state,
    required this.onTap,
    required this.requiresNetwork,
    this.score,
    super.key,
  });

  final String title;
  final QuestionAttemptState state;
  final VoidCallback onTap;
  final bool requiresNetwork;
  final Score? score;

  @override
  Widget build(BuildContext context) => ListItemContainer(
    onTap: onTap,
    requiresNetwork: requiresNetwork,
    child: _buildContent(),
  );

  Widget _buildContent() {
    final indicator = _buildRightIndicator();

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Title (flexible to allow badge space)
        Expanded(
          child: Text(
            title,
            style: AppTypography.h2.copyWith(color: AppColors.textPrimary),
          ),
        ),
        if (indicator != null) ...[
          const SizedBox(width: AppSpacing.md),
          // Right indicator (badge or text) - always right-aligned
          Align(alignment: Alignment.centerRight, child: indicator),
        ],
      ],
    );
  }

  Widget? _buildRightIndicator() {
    switch (state) {
      case QuestionAttemptState.marking:
        // Gray badge for marking state (consistent with papers)
        return const PillBadge(
          backgroundColor: Colors.transparent,
          borderColor: AppColors.textSecondary,
          textColor: AppColors.textSecondary,
          label: 'Marking',
        );
      case QuestionAttemptState.complete:
        // Show score for completed questions
        if (score != null) {
          return _buildTextIndicator('${score!.awarded}/${score!.available}');
        }
        return null;
    }
  }

  /// Helper to create text indicators that align consistently with pill badges.
  /// Uses body typography (Inter) for scores - secondary to title.
  Widget _buildTextIndicator(String text) => Text(
    text,
    style: AppTypography.body.copyWith(color: AppColors.textSecondary),
  );
}
