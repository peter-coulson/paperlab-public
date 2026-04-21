import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/list_items/list_item_container.dart';

/// Displays a single student work image in a tappable card.
///
/// Features:
/// - Image fills container (no internal padding)
/// - Rounded corners (clipped)
/// - Error state with placeholder icon and text
/// - Tap to open fullscreen viewer
///
/// M5: Displays images from assets
/// M6: Displays images from presigned URLs with caching
class StudentWorkImage extends StatelessWidget {
  const StudentWorkImage({
    required this.imagePath,
    required this.onTap,
    super.key,
  });

  /// Path to student work image
  /// M5: Asset path (e.g., "assets/images/student_work_1.png")
  /// M6: Presigned URL from backend
  final String imagePath;

  /// Callback when image is tapped (opens fullscreen viewer)
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListItemContainer(
    onTap: onTap,
    requiresNetwork: false,
    padding: EdgeInsets.zero, // Image fills container
    clipBehavior: Clip.antiAlias, // Round image corners
    minHeight: 0, // Let image determine height
    child: Image.asset(
      imagePath,
      fit: BoxFit.contain, // Show full image without cropping
      width: double.infinity,
      errorBuilder: (context, error, stackTrace) =>
          const _StudentWorkImageErrorPlaceholder(),
    ),
  );
}

/// Error placeholder shown when student work image fails to load.
class _StudentWorkImageErrorPlaceholder extends StatelessWidget {
  const _StudentWorkImageErrorPlaceholder();

  @override
  Widget build(BuildContext context) => Container(
    height: AppSpacing.diagramPlaceholderHeight,
    color: AppColors.backgroundSecondary,
    child: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.photo_library_outlined,
            size: AppSpacing.iconSizeLarge,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Student Work',
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    ),
  );
}
