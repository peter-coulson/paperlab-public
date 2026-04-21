import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// InfoBanner component for displaying tips, warnings, and success messages.
/// See specs/SHARED_COMPONENTS.md (lines 562-618) for complete specification.
///
/// Features:
/// - Three variants: info, warning, success
/// - Optional dismissible with \[Dismiss\] button
/// - Custom icon and content
/// - Full-width display
///
/// Styling:
/// - Background: Variant color with 10% opacity
/// - Border: Variant color with 20% opacity
/// - Border radius: 8px
/// - Padding: 12px vertical, 16px horizontal
/// - Icon: 24px, positioned left
///
/// Used in:
/// - Question Upload Screen (photo quality tip)
/// - Future: Warnings, announcements, tips throughout app
class InfoBanner extends StatelessWidget {
  const InfoBanner({
    required this.content,
    this.variant = InfoBannerVariant.info,
    this.icon,
    this.dismissible = false,
    this.onDismiss,
    super.key,
  });

  /// Banner variant (determines colors and default icon)
  final InfoBannerVariant variant;

  /// Custom icon (emoji or text) - if null, uses variant default
  final String? icon;

  /// Banner content (text or rich widget)
  final Widget content;

  /// Whether to show \[Dismiss\] button
  final bool dismissible;

  /// Dismiss button handler (required if dismissible is true)
  final VoidCallback? onDismiss;

  @override
  Widget build(BuildContext context) {
    final variantConfig = _getVariantConfig(variant);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(
        vertical: 12,
        horizontal: AppSpacing.md,
      ),
      decoration: BoxDecoration(
        color: variantConfig.backgroundColor,
        border: Border.all(
          color: variantConfig.borderColor,
          width: AppEffects.borderWidth,
          strokeAlign: AppEffects.strokeAlignInside,
        ),
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon
          if (icon != null || variantConfig.defaultIcon != null)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: Text(
                icon ?? variantConfig.defaultIcon!,
                style: const TextStyle(fontSize: 24),
              ),
            ),

          // Content
          Expanded(child: content),

          // Dismiss button
          if (dismissible)
            Padding(
              padding: const EdgeInsets.only(left: 12),
              child: InteractiveEffect(
                onTap: onDismiss!,
                child: Text(
                  'Dismiss',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  _VariantConfig _getVariantConfig(InfoBannerVariant variant) {
    switch (variant) {
      case InfoBannerVariant.info:
        return _VariantConfig(
          backgroundColor: AppColors.primaryLight.withValues(alpha: 0.1),
          borderColor: AppColors.primaryLight.withValues(alpha: 0.2),
          defaultIcon: '📸',
        );
      case InfoBannerVariant.warning:
        return _VariantConfig(
          backgroundColor: AppColors.error.withValues(alpha: 0.1),
          borderColor: AppColors.error.withValues(alpha: 0.2),
          defaultIcon: '⚠️',
        );
      case InfoBannerVariant.success:
        return _VariantConfig(
          backgroundColor: AppColors.success.withValues(alpha: 0.1),
          borderColor: AppColors.success.withValues(alpha: 0.2),
          defaultIcon: '✓',
        );
    }
  }
}

/// Banner variant types
enum InfoBannerVariant {
  /// Information (blue) - tips, helpful information
  info,

  /// Warning (amber) - attention needed, fixable issues
  warning,

  /// Success (green) - positive confirmation
  success,
}

/// Internal configuration for banner variants
class _VariantConfig {
  const _VariantConfig({
    required this.backgroundColor,
    required this.borderColor,
    required this.defaultIcon,
  });

  final Color backgroundColor;
  final Color borderColor;
  final String? defaultIcon;
}
