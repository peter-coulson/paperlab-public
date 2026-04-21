import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/network_aware_interactive.dart';

/// Secondary button component for secondary actions.
/// Matches design system specification from SHARED_COMPONENTS.md
/// (lines 217-247).
///
/// Features:
/// - Interactive press feedback via InteractiveEffect
/// - Full-width by default (can be overridden)
/// - Disabled state (null onTap)
///
/// States:
/// - Default: Transparent background with border
/// - Hover/Press: backgroundSecondary (via InteractiveEffect)
/// - Disabled: Tertiary text and border, reduced opacity
///
/// Styling:
/// - Height: 48px (minimum touch target)
/// - Padding: 12px vertical, 24px horizontal
/// - Border: 1px border color
/// - Border radius: 8px
/// - Text: Button style (Inter, 16px, SemiBold), primary color
///
/// Used for:
/// - Secondary actions (e.g., "Return to Home", "Cancel")
/// - Less important actions than primary button
/// - Actions that don't commit data
///
/// Network Behavior:
/// - requiresNetwork: true → Auto-disables when offline
/// - requiresNetwork: false → Always enabled (for local-only actions)
class SecondaryButton extends StatelessWidget {
  const SecondaryButton({
    required this.text,
    required this.onTap,
    required this.requiresNetwork,
    this.disabled = false,
    this.fullWidth = true,
    super.key,
  });

  /// Button label
  final String text;

  /// Tap callback (null disables button)
  final VoidCallback? onTap;

  /// Whether this button requires network connectivity.
  /// REQUIRED parameter - must be explicitly set for every button.
  /// - true: Button auto-disables when offline (e.g., API calls)
  /// - false: Button works offline (e.g., navigation, cancel)
  final bool requiresNetwork;

  /// Whether button is disabled
  final bool disabled;

  /// Whether button should fill available width
  final bool fullWidth;

  static const double _height = 48;
  static const double _horizontalPadding = 24;

  @override
  Widget build(BuildContext context) {
    final bool isDisabled = disabled || onTap == null;

    // Button container (styling)
    final buttonContainer = Container(
      height: _height,
      width: fullWidth ? double.infinity : null,
      padding: const EdgeInsets.symmetric(
        horizontal: _horizontalPadding,
        vertical: AppSpacing.buttonVerticalPadding,
      ),
      decoration: BoxDecoration(
        color: Colors.transparent,
        border: Border.all(
          color: isDisabled ? AppColors.textTertiary : AppColors.border,
          width: 1,
        ),
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
      ),
      child: Center(
        child: Text(
          text,
          style: AppTypography.body.copyWith(
            fontWeight: FontWeight.w600,
            color: isDisabled ? AppColors.textTertiary : AppColors.primary,
          ),
        ),
      ),
    );

    // Disabled state - no interactive wrapper
    if (isDisabled) {
      return buttonContainer;
    }

    // Active state - wrap with network-aware interactive
    return NetworkAwareInteractive(
      requiresNetwork: requiresNetwork,
      onTap: onTap,
      child: buttonContainer,
    );
  }
}
