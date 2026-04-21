import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/list_items/list_item_container.dart';

/// Upload photo list item with consistent list item styling.
///
/// Displays camera icon and "Add Photo" text with the same container
/// treatment as PhotoListItem (border, shadow, background).
///
/// Features:
/// - Consistent visual treatment matching photo items
/// - Large camera icon (48px - dominant visual element)
/// - "Add Photo" label below icon (caption size, small explainer)
/// - Same aspect ratio as photo items (15:7)
/// - Interactive tap feedback
///
/// Used by:
/// - Question Upload Screen (always visible for adding photos)
///
/// Design rationale:
/// - Visual consistency with PhotoListItem creates clear pattern
/// - Single button style used in all contexts (empty and filled state)
/// - Students recognize this as "photo slot" immediately
/// - Calm, professional appearance (not loud/prominent)
/// - Large icon dominates, small text explains
/// - "Add Photo" is more approachable than technical "Upload Image"
class UploadPhotoListItem extends StatelessWidget {
  const UploadPhotoListItem({
    required this.onTap,
    required this.aspectRatio,
    this.width,
    super.key,
  });

  /// Callback when upload button is tapped
  final VoidCallback onTap;

  /// Aspect ratio for button display (width / height)
  /// Should match PhotoListItem aspect ratio (15/7) for visual consistency
  final double aspectRatio;

  /// Width of button (optional, defaults to parent width)
  final double? width;

  static const double _iconSize = 38; // Large, dominant icon
  static const double _iconTextSpacing = 8;

  @override
  Widget build(BuildContext context) {
    final double height = (width ?? 0) / aspectRatio;

    return ListItemContainer(
      onTap: onTap,
      requiresNetwork: true,
      padding: EdgeInsets.zero, // Content fills container
      minHeight: height,
      child: SizedBox(
        width: width,
        height: height,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Camera icon
              const Icon(
                LucideIcons.camera,
                size: _iconSize,
                color: AppColors.textSecondary,
              ),

              const SizedBox(height: _iconTextSpacing),

              // "Add Photo" label (small explainer text)
              Text(
                'Add Photo',
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
