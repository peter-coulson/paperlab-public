import 'package:flutter/material.dart';
import 'package:paperlab/models/score.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/list_items/list_item_container.dart';

/// Result list item with score (no badge).
/// See specs/SHARED_COMPONENTS.md for complete specification.
class ResultListItem extends StatelessWidget {
  const ResultListItem({
    required this.title,
    required this.score,
    required this.onTap,
    required this.requiresNetwork,
    super.key,
  });

  final String title;
  final Score score;
  final VoidCallback onTap;
  final bool requiresNetwork;

  @override
  Widget build(BuildContext context) => ListItemContainer(
    onTap: onTap,
    requiresNetwork: requiresNetwork,
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Title
        Expanded(
          child: Text(
            title,
            style: AppTypography.h2.copyWith(color: AppColors.textPrimary),
          ),
        ),
        const SizedBox(width: AppSpacing.md),
        // Score
        Text(
          '${score.awarded}/${score.available}',
          style: AppTypography.body.copyWith(color: AppColors.textSecondary),
        ),
      ],
    ),
  );
}
