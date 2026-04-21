import 'dart:async';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:easy_image_viewer/easy_image_viewer.dart';
import 'package:flutter/material.dart';
import 'package:paperlab/models/student_work_image.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Your Work section of the Question Results Screen.
///
/// Provides reference to submitted images (supplementary).
///
/// Visual structure:
/// ```
/// YOUR WORK
/// ────────────────────────────
/// [Full-width image 1]
///
/// [Full-width image 2]
/// ```
///
/// Features:
/// - Section header: "YOUR WORK"
/// - Full-width images fitting to screen edges
/// - Tap-to-enlarge functionality with fullscreen viewer
/// - Multi-image swipe navigation
///
/// Edge cases:
/// - No images: Hide entire section (handled by parent)
class YourWorkSection extends StatelessWidget {
  const YourWorkSection({required this.images, super.key});

  /// Student work images to display
  final List<StudentWorkImage> images;

  @override
  Widget build(BuildContext context) {
    // Don't render if no images
    if (images.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section header
        Semantics(
          header: true,
          child: AppTypography.sectionTitle(
            'Your Work',
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: AppSpacing.md),

        // Full-width images
        ...images.asMap().entries.map(
          (entry) => Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.md),
            child: _buildStudentWorkImage(context, images, entry.key),
          ),
        ),
      ],
    );
  }

  /// Build student work image from presigned URL with fullscreen viewer on tap.
  ///
  /// Tapping the image opens a fullscreen viewer with:
  /// - Multi-image swipe navigation
  /// - Pinch to zoom
  /// - Double tap to zoom
  /// - Swipe down to dismiss
  Widget _buildStudentWorkImage(
    BuildContext context,
    List<StudentWorkImage> images,
    int currentIndex,
  ) {
    final url = images[currentIndex].url;

    return Semantics(
      label: 'Student work page ${currentIndex + 1}',
      child: GestureDetector(
        onTap: () => _openImageViewer(context, images, currentIndex),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: CachedNetworkImage(
            imageUrl: url,
            placeholder: (context, url) => Container(
              height: 200,
              color: AppColors.backgroundSecondary,
              child: const Center(
                child: CircularProgressIndicator.adaptive(
                  valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                ),
              ),
            ),
            errorWidget: (context, url, error) => Container(
              height: 200,
              color: AppColors.backgroundSecondary,
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error, color: AppColors.error, size: 32),
                  SizedBox(height: AppSpacing.xs),
                  Text(
                    'Failed to load image',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            fit: BoxFit.contain,
          ),
        ),
      ),
    );
  }

  /// Open fullscreen image viewer with multi-image swipe support.
  ///
  /// Features:
  /// - Swipe left/right between images
  /// - Pinch to zoom in/out
  /// - Swipe down to dismiss
  /// - Page indicator
  void _openImageViewer(
    BuildContext context,
    List<StudentWorkImage> images,
    int initialIndex,
  ) {
    // Create image providers for all student work images
    final imageProviders = images
        .map((image) => CachedNetworkImageProvider(image.url))
        .toList();

    // Open fullscreen viewer with swipe-dismiss
    unawaited(
      showImageViewerPager(
        context,
        MultiImageProvider(imageProviders, initialIndex: initialIndex),
        swipeDismissible: true,
        doubleTapZoomable: true,
        backgroundColor: Colors.black,
        closeButtonColor: Colors.white,
      ),
    );
  }
}
