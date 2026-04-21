import 'dart:io' if (dart.library.html) 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:image_picker/image_picker.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';

/// Photo thumbnail component with optional delete button and fade effect.
/// See specs/SHARED_COMPONENTS.md (lines 500-557) for complete specification.
///
/// Features:
/// - Flexible sizing (defaults to 80x80px, supports custom dimensions
///   and aspect ratios)
/// - Border and border radius
/// - Optional \[X\] delete button (top-right corner)
/// - Optional fade effect (for overflow indicator)
/// - Tap to open fullscreen viewer
/// - Cross-platform (web + mobile) via XFile
/// - M5: Supports mock display (null image shows colored placeholder)
///
/// Used in:
/// - Paper Upload Screen (question row previews) - 80×80px square
///   thumbnails with aspect ratio
/// - Question Upload Screen (photo list) - Full-width full images
///   (natural aspect ratio, max height 800px constraint)
class PhotoThumbnail extends StatelessWidget {
  const PhotoThumbnail({
    this.imageFile,
    this.onTap,
    this.width,
    this.height,
    this.aspectRatio,
    this.mockPhotoIndex = 0,
    this.showDeleteButton = false,
    this.fadeEffect = false,
    this.onDelete,
    super.key,
  });

  /// Photo file to display (XFile for cross-platform, null = mock placeholder)
  final XFile? imageFile;

  /// Width of thumbnail (defaults to 80px if not specified)
  final double? width;

  /// Height of thumbnail (defaults to 80px if not specified,
  /// calculated from width and aspectRatio if aspectRatio is provided)
  final double? height;

  /// Aspect ratio (width / height). If provided with width, height is calculated.
  /// Example: 2/3 for portrait orientation (width is 2, height is 3)
  final double? aspectRatio;

  /// Mock photo index (0-based, used for color variation in M5)
  final int mockPhotoIndex;

  /// Tap handler (opens fullscreen viewer).
  /// Optional - only provide if PhotoThumbnail handles tap directly.
  /// When wrapped in ListItemContainer, omit this (container handles tap).
  final VoidCallback? onTap;

  /// Whether to show \[X\] delete button
  final bool showDeleteButton;

  /// Whether to apply fade effect (overflow indicator)
  final bool fadeEffect;

  /// Delete button handler (required if showDeleteButton is true)
  final VoidCallback? onDelete;

  static const double _defaultSize = 80;
  static const double _deleteButtonSize = 24;

  static final List<Color> _mockColors = [
    Colors.blue.shade300,
    Colors.green.shade300,
    Colors.orange.shade300,
    Colors.purple.shade300,
    Colors.pink.shade300,
  ];

  @override
  Widget build(BuildContext context) {
    // Build the image container with specified dimensions
    Widget thumbnail = Container(
      width: width ?? _defaultSize,
      decoration: BoxDecoration(
        // Border only when aspectRatio is set (cropped previews)
        // No border when aspectRatio is null (full student work images)
        border: aspectRatio != null
            ? Border.all(color: AppColors.border)
            : null,
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
      ),
      clipBehavior: Clip.antiAlias,
      child: aspectRatio != null
          ? AspectRatio(
              aspectRatio: aspectRatio!,
              child: imageFile != null
                  ? _buildCrossPlatformImage()
                  : _buildMockPlaceholder(),
            )
          : imageFile != null
          ? ConstrainedBox(
              // Max height prevents excessively tall images from
              // breaking layout
              constraints: const BoxConstraints(maxHeight: 800),
              child: _buildCrossPlatformImage(),
            )
          : SizedBox(
              height: height ?? _defaultSize,
              child: _buildMockPlaceholder(),
            ),
    );

    // Apply fade effect if requested
    if (fadeEffect) {
      thumbnail = ShaderMask(
        shaderCallback: (bounds) => const LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          colors: [Colors.black, Colors.transparent],
          stops: [0.3, 1.0],
        ).createShader(bounds),
        blendMode: BlendMode.dstIn,
        child: thumbnail,
      );
    }

    // Wrap in GestureDetector for tap only if onTap provided
    // (when wrapped in ListItemContainer, container handles interaction)
    if (onTap != null) {
      thumbnail = GestureDetector(onTap: onTap, child: thumbnail);
    }

    // Add delete button if requested
    if (showDeleteButton) {
      thumbnail = Stack(
        clipBehavior: Clip.none,
        children: [
          thumbnail,
          Positioned(
            top: -8,
            right: -8,
            child: InteractiveEffect(
              onTap: onDelete!,
              child: Container(
                width: _deleteButtonSize,
                height: _deleteButtonSize,
                decoration: BoxDecoration(
                  color: AppColors.destructive.withValues(alpha: 0.9),
                  shape: BoxShape.circle,
                ),
                child: const Icon(LucideIcons.x, size: 16, color: Colors.white),
              ),
            ),
          ),
        ],
      );
    }

    return thumbnail;
  }

  /// Build cross-platform image (web uses bytes, mobile/desktop uses file)
  /// Uses BoxFit.cover for cropped previews (aspectRatio set),
  /// BoxFit.contain for full images
  Widget _buildCrossPlatformImage() {
    if (kIsWeb) {
      // Web: Use Image.network with XFile.path (blob URL) or
      // FutureBuilder with readAsBytes
      return FutureBuilder<Uint8List>(
        future: imageFile!.readAsBytes(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return Image.memory(
              snapshot.data!,
              fit: aspectRatio != null ? BoxFit.cover : BoxFit.contain,
              alignment: Alignment.topCenter,
            );
          }
          // Loading state (brief, usually instant)
          return const Center(child: CircularProgressIndicator());
        },
      );
    } else {
      // Mobile/Desktop: Use Image.file
      return Image.file(
        File(imageFile!.path),
        fit: aspectRatio != null ? BoxFit.cover : BoxFit.contain,
        alignment: Alignment.topCenter,
      );
    }
  }

  /// Build mock placeholder (M5 only - colored box with text)
  Widget _buildMockPlaceholder() {
    final color = _mockColors[mockPhotoIndex % _mockColors.length];

    return ColoredBox(
      color: color,
      child: Center(
        child: Text(
          'Photo ${mockPhotoIndex + 1}',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
