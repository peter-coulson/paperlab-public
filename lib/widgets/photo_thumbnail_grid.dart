import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/photo_thumbnail.dart';

/// Horizontal grid of photo thumbnails with optional fade effect on overflow.
/// See specs/SHARED_COMPONENTS.md (lines 500-557) for complete specification.
///
/// Features:
/// - Left-aligned horizontal row
/// - 8px spacing between thumbnails
/// - Fade effect on last visible thumbnail when more exist
/// - Tap thumbnails to open fullscreen viewer
/// - M5: Supports mock display (null images show colored placeholders)
///
/// Used in:
/// - Paper Upload Screen (question row photo previews)
/// - Question Upload Screen (photo grid)
class PhotoThumbnailGrid extends StatelessWidget {
  const PhotoThumbnailGrid({
    this.images,
    this.mockPhotoCount,
    required this.onImageTap,
    this.maxVisible = 3,
    this.showDeleteButtons = false,
    this.onImageDelete,
    super.key,
  });

  /// List of image files to display (null = use mockPhotoCount for M5)
  final List<XFile>? images;

  /// M5: Number of mock photos to display (only used if images is null)
  final int? mockPhotoCount;

  /// Maximum number of thumbnails to show (default: 3)
  final int maxVisible;

  /// Whether to show delete buttons on thumbnails
  final bool showDeleteButtons;

  /// Tap handler for opening fullscreen viewer
  /// Receives index of tapped image
  final void Function(int index) onImageTap;

  /// Delete handler for individual images
  /// Receives index of image to delete
  final void Function(int index)? onImageDelete;

  @override
  Widget build(BuildContext context) {
    // M5: Support mock photos (null images = use mockPhotoCount)
    final totalCount = images?.length ?? mockPhotoCount ?? 0;

    // Determine how many to show
    final visibleCount = totalCount > maxVisible ? maxVisible : totalCount;
    final hasOverflow = totalCount > maxVisible;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (int i = 0; i < visibleCount; i++) ...[
          PhotoThumbnail(
            imageFile: images != null && i < images!.length ? images![i] : null,
            mockPhotoIndex: i,
            onTap: () => onImageTap(i),
            showDeleteButton: showDeleteButtons,
            onDelete: showDeleteButtons ? () => onImageDelete?.call(i) : null,
            // Apply fade to last visible thumbnail if overflow exists
            fadeEffect: hasOverflow && i == visibleCount - 1,
          ),
          if (i < visibleCount - 1) const SizedBox(width: AppSpacing.sm),
        ],
      ],
    );
  }
}
