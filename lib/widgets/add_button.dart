import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/network_aware_interactive.dart';

/// Full-width AddButton component - primary CTA.
/// Used for primary "add" actions throughout the app.
///
/// See specs/SHARED_COMPONENTS.md for complete specification.
///
/// Styling:
/// - Width: 100% (full-width, no exceptions)
/// - Height: 72px (20% larger than ListItem)
/// - Background: Primary color (soft indigo #667EEA)
/// - Icon: + symbol, white, 38px
/// - Shadow: Neutral with consistent depth
///
/// Note: Button text/labels are rendered ABOVE the button, not inside it.
/// This maintains consistent UI pattern across the app.
///
/// Network Behavior:
/// - requiresNetwork: true → Auto-disables when offline
/// - requiresNetwork: false → Always enabled (for local-only actions)
class AddButton extends StatelessWidget {
  const AddButton({
    required this.onTap,
    required this.requiresNetwork,
    this.disabled = false,
    super.key,
  });

  final VoidCallback onTap;

  /// Whether this button requires network connectivity.
  /// REQUIRED parameter - must be explicitly set.
  /// - true: Button auto-disables when offline (e.g., fetching available papers/questions)
  /// - false: Button works offline (e.g., local draft creation)
  final bool requiresNetwork;

  final bool disabled;

  static const double _height = 72;
  static const double _iconSize = 38;

  @override
  Widget build(BuildContext context) {
    // Button container (styling)
    final buttonContainer = Container(
      height: _height,
      decoration: BoxDecoration(
        color: disabled ? AppColors.backgroundSecondary : AppColors.primary,
        border: disabled
            ? Border.all(
                color: AppColors.border.withValues(alpha: 0.5),
                width: AppEffects.borderWidth,
                strokeAlign: AppEffects.strokeAlignInside,
              )
            : null,
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        boxShadow: disabled ? null : AppEffects.shadow,
      ),
      child: Center(
        child: Icon(
          LucideIcons.plus,
          size: _iconSize,
          color: disabled ? AppColors.textTertiary : Colors.white,
        ),
      ),
    );

    // Disabled state - no interactive wrapper
    if (disabled) {
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
