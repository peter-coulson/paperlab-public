import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Inline error component for displaying failed marking attempts.
/// Matches design system specification from SHARED_COMPONENTS.md
/// (lines 699-726).
///
/// Features:
/// - Amber background with 10% opacity (error semantic color)
/// - Warning icon (⚠) positioned left
/// - Question number and error message
/// - Border in error color
///
/// Styling:
/// - Background: error (#F59E0B) with 10% opacity
/// - Border: 1px error (#F59E0B)
/// - Padding: 12px vertical, 16px horizontal
/// - Border radius: 8px
/// - Icon: 16px, error color
/// - Text: body (Inter, 16px, Regular), textPrimary color
///
/// Used in:
/// - Marking In Progress Screen - Failed questions list (State 2)
/// - Displays marking errors with clear visual hierarchy
///
/// Design rationale:
/// - Read-only display (retry handled by button, not inline)
/// - Clear visual distinction from success states
/// - Matches error semantic color throughout app
class InlineError extends StatelessWidget {
  const InlineError({
    required this.questionNumber,
    required this.errorMessage,
    super.key,
  });

  /// Question number (e.g., "Q3", "Q12")
  final String questionNumber;

  /// Error message (e.g., "Rate limit exceeded", "Request timeout")
  final String errorMessage;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(
      horizontal: AppSpacing.md,
      vertical: 12,
    ),
    decoration: BoxDecoration(
      color: AppColors.error.withValues(alpha: 0.1), // 10% opacity
      border: Border.all(color: AppColors.error, width: 1),
      borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
    ),
    child: Row(
      children: [
        // Question number
        Text(
          questionNumber,
          style: AppTypography.body.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w500, // Medium weight for emphasis
          ),
        ),

        const SizedBox(width: AppSpacing.md),

        // Warning icon
        const Icon(
          Icons.warning_amber_rounded,
          size: 16,
          color: AppColors.error,
        ),

        const SizedBox(width: AppSpacing.sm),

        // Error message
        Expanded(
          child: Text(
            errorMessage,
            style: AppTypography.body.copyWith(color: AppColors.textPrimary),
          ),
        ),
      ],
    ),
  );
}
