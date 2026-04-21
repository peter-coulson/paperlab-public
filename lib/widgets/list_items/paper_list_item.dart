import 'package:flutter/material.dart';
import 'package:paperlab/models/paper_attempt_state.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/list_items/list_item_container.dart';
import 'package:paperlab/widgets/list_items/pill_badge.dart';

/// Paper list item with state badge.
/// See specs/SHARED_COMPONENTS.md for complete specification.
class PaperListItem extends StatelessWidget {
  const PaperListItem({
    required this.title,
    required this.state,
    required this.onTap,
    required this.requiresNetwork,
    this.grade,
    super.key,
  });

  final String title;
  final PaperAttemptState state;
  final VoidCallback onTap;
  final String? grade;

  /// Whether this interaction requires network connectivity.
  /// Determined by caller based on navigation target (e.g., complete
  /// state needs API).
  final bool requiresNetwork;

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
      case PaperAttemptState.draft:
        // Use subtle border style instead of filled background
        // for less visual weight
        return const PillBadge(
          backgroundColor: Colors.transparent,
          borderColor: AppColors.primary,
          textColor: AppColors.primary,
          label: 'Draft',
        );
      case PaperAttemptState.marking:
        // Gray badge for marking state
        // (neutral - works for in-progress and failed)
        return const PillBadge(
          backgroundColor: Colors.transparent,
          borderColor: AppColors.textSecondary,
          textColor: AppColors.textSecondary,
          label: 'Marking',
        );
      case PaperAttemptState.complete:
        // Show grade for completed papers (h2 for visual weight)
        if (grade != null) {
          return Text(
            '$grade',
            style: AppTypography.h2.copyWith(color: AppColors.textSecondary),
          );
        }
        return null;
    }
  }
}
