import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/latex_text.dart';

/// Diagram placeholder shown when diagram image is not available.
///
/// Displays an icon and description text in a styled container.
/// Used in question content and mark scheme descriptions.
///
/// M5: Shows placeholder for all diagrams
/// M6: Shows placeholder only when image URL is not available
class DiagramPlaceholder extends StatelessWidget {
  const DiagramPlaceholder({required this.description, super.key});

  /// Diagram description (for screen readers and fallback display)
  /// Example: "A triangle with vertices labeled A, B, and C"
  final String description;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(AppSpacing.md),
    decoration: BoxDecoration(
      color: AppColors.backgroundSecondary,
      borderRadius: BorderRadius.circular(AppSpacing.diagramBorderRadius),
      border: Border.all(color: AppColors.border),
      boxShadow: AppEffects.shadow,
    ),
    child: Row(
      children: [
        const Icon(
          Icons.image_outlined,
          color: AppColors.textSecondary,
          size: AppSpacing.iconSizeSmall,
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: LatexText(
            description,
            style: AppTypography.body.copyWith(
              color: AppColors.textSecondary,
              fontStyle: FontStyle.italic,
            ),
          ),
        ),
      ],
    ),
  );
}
