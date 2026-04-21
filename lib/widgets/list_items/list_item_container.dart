import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/network_aware_interactive.dart';

/// Shared container for all list items with consistent visual styling.
///
/// Provides single source of truth for:
/// - Background color (backgroundSecondary)
/// - Border (1px solid border)
/// - Border radius (8px)
/// - Shadow (two-layer shadow system)
/// - Interactive press feedback (via InteractiveEffect)
/// - Minimum height constraint (60px default)
///
/// Used by:
/// - PaperListItem (text content with padding)
/// - QuestionListItem (text content with padding)
/// - UploadListItem (text content with padding)
/// - ResultListItem (text content with padding)
/// - QuestionUploadRow (text content with padding)
/// - PhotoListItem (image content, no padding)
///
/// Design rationale:
/// - Enforces visual consistency across all list items
/// - Single place to change list item styling
/// - Follows DRY principle (no duplicated decoration code)
/// - Composition over inheritance (Flutter best practice)
///
/// Network Behavior:
/// - requiresNetwork: true → Auto-disables when offline
/// - requiresNetwork: false → Always enabled (for local-only actions)
class ListItemContainer extends StatelessWidget {
  const ListItemContainer({
    required this.child,
    required this.onTap,
    required this.requiresNetwork,
    this.padding = const EdgeInsets.all(AppSpacing.md),
    this.minHeight = 60.0,
    this.clipBehavior = Clip.none,
    super.key,
  });

  /// Content to display inside the container
  final Widget child;

  /// Callback when container is tapped
  final VoidCallback onTap;

  /// Whether this interaction requires network connectivity.
  /// REQUIRED parameter - must be explicitly set for every list item.
  /// - true: Auto-disables when offline (e.g., navigating to results
  ///   that require API call)
  /// - false: Always enabled (e.g., navigating to drafts, fullscreen
  ///   image view)
  final bool requiresNetwork;

  /// Padding around child content.
  /// Defaults to 16px (AppSpacing.md) for text-based list items.
  /// Use EdgeInsets.zero for photos that fill the container.
  final EdgeInsets padding;

  /// Minimum height constraint for container.
  /// Defaults to 60px (consistent with all current list items).
  final double minHeight;

  /// Clip behavior for container content.
  /// Use Clip.antiAlias for photos (rounds corners).
  /// Use Clip.none for text content (better performance).
  final Clip clipBehavior;

  @override
  Widget build(BuildContext context) => NetworkAwareInteractive(
    requiresNetwork: requiresNetwork,
    onTap: onTap,
    child: Container(
      constraints: BoxConstraints(minHeight: minHeight),
      decoration: BoxDecoration(
        color: AppColors.backgroundSecondary,
        border: Border.all(
          color: AppColors.border,
          width: AppEffects.borderWidth,
          strokeAlign: AppEffects.strokeAlignInside,
        ),
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        boxShadow: AppEffects.shadow,
      ),
      clipBehavior: clipBehavior,
      child: Padding(padding: padding, child: child),
    ),
  );
}
