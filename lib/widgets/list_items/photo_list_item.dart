import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/photo_thumbnail.dart';

/// Photo list item for student work images.
///
/// Displays full student work photos with minimal visual chrome (rounded
/// corners only). Preserves interactive feedback (scale animation + haptic)
/// without full list item styling.
///
/// Features:
/// - Clean presentation (rounded corners, no border/shadow/background)
/// - Full image display with BoxFit.contain
/// - Interactive tap feedback (scale + haptic via InteractiveEffect)
/// - Shows complete upload content for user verification
///
/// Used by:
/// - Question Upload Screen (vertical photo list)
///
/// Design rationale:
/// - Student work images are content to review, not buttons to press
/// - Visual consistency with results screen (same content, same styling)
/// - Clean interface lets images speak for themselves
/// - Preserved tap feedback maintains responsive feel
class PhotoListItem extends StatelessWidget {
  const PhotoListItem({
    required this.imageFile,
    required this.onTap,
    this.width,
    super.key,
  });

  /// Photo file to display
  final XFile imageFile;

  /// Callback when photo is tapped
  final VoidCallback onTap;

  /// Width of photo (optional, defaults to parent width)
  final double? width;

  @override
  Widget build(BuildContext context) => InteractiveEffect(
    onTap: onTap,
    child: ClipRRect(
      borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
      child: PhotoThumbnail(
        imageFile: imageFile,
        width: width,
        // No aspectRatio - show full image with BoxFit.contain
      ),
    ),
  );
}
