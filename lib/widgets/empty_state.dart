import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Empty state component for lists.
/// See specs/SHARED_COMPONENTS.md for complete specification.
///
/// Used when no items exist in Papers or Questions tabs.
class EmptyState extends StatelessWidget {
  const EmptyState({
    required this.primaryText,
    required this.secondaryText,
    super.key,
  });

  final String primaryText;
  final String secondaryText;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.xxl,
        horizontal: AppSpacing.lg,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            primaryText,
            style: AppTypography.body.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            secondaryText,
            style: AppTypography.body.copyWith(color: AppColors.textTertiary),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    ),
  );
}
