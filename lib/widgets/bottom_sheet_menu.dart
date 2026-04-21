import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Bottom sheet menu for overflow actions and secondary options.
///
/// Design pattern for edge-case actions that shouldn't have prominent
/// primary button placement (e.g., Edit Photos, Share, Report Issue).
///
/// Features:
/// - Slides up from bottom (native mobile pattern)
/// - List of menu items with icons and labels
/// - Tap-outside-to-dismiss (non-modal feel)
/// - Follows Material Design bottom sheet conventions
///
/// Usage:
/// ```dart
/// // In header overflow menu icon:
/// InteractiveEffect(
///   onTap: () => showBottomSheetMenu(
///     context: context,
///     items: [
///       BottomSheetMenuItem(
///         icon: LucideIcons.camera,
///         label: 'Edit Photo Submissions',
///         onTap: () {
///           Navigator.pop(context); // Close sheet
///           // Handle action
///         },
///       ),
///     ],
///   ),
///   child: const SizedBox(
///     width: 44,
///     height: 44,
///     child: Icon(LucideIcons.settings, size: 24),
///   ),
/// )
/// ```
class BottomSheetMenu extends StatelessWidget {
  const BottomSheetMenu({required this.items, super.key});

  /// Menu items to display
  final List<BottomSheetMenuItem> items;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: const BoxDecoration(
      color: AppColors.background,
      borderRadius: BorderRadius.vertical(
        top: Radius.circular(12), // Match dialog/card radius for large surfaces
      ),
    ),
    child: SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle bar (visual affordance for dragging)
          Padding(
            padding: const EdgeInsets.only(top: AppSpacing.sm),
            child: Container(
              width: 32,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          const SizedBox(height: AppSpacing.md),

          // Menu items
          ...items.map((item) => _buildMenuItem(item)),

          const SizedBox(height: AppSpacing.md),
        ],
      ),
    ),
  );

  Widget _buildMenuItem(BottomSheetMenuItem item) => InteractiveEffect(
    onTap: item.onTap,
    child: Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.md,
      ),
      child: Row(
        children: [
          Icon(item.icon, size: 24, color: AppColors.textPrimary),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              item.label,
              style: AppTypography.body.copyWith(color: AppColors.textPrimary),
            ),
          ),
        ],
      ),
    ),
  );
}

/// Configuration for a bottom sheet menu item.
class BottomSheetMenuItem {
  const BottomSheetMenuItem({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  /// Icon displayed on the left (Lucide icon)
  final IconData icon;

  /// Label text displayed next to icon
  final String label;

  /// Callback when menu item is tapped
  final VoidCallback onTap;
}

/// Show a bottom sheet menu using the BottomSheetMenu component.
/// Dismissible by tapping outside (barrierDismissible: true).
Future<T?> showBottomSheetMenu<T>({
  required BuildContext context,
  required List<BottomSheetMenuItem> items,
}) => showModalBottomSheet<T>(
  context: context,
  backgroundColor: Colors.transparent, // Transparent to show rounded corners
  barrierColor: Colors.black.withValues(alpha: 0.5), // Semi-transparent overlay
  builder: (context) => BottomSheetMenu(items: items),
);
