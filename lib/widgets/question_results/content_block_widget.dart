import 'package:flutter/material.dart';
import 'package:paperlab/config.dart';
import 'package:paperlab/models/content_block.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/utils/string_utils.dart';
import 'package:paperlab/widgets/latex_text.dart';
import 'package:paperlab/widgets/question_results/diagram_placeholder.dart';

/// Displays a single content block (text or diagram).
///
/// Content blocks are used in:
/// - Question parts (question text and diagrams)
/// - Mark criteria (mark scheme descriptions and diagrams)
///
/// Handles:
/// - Text blocks with LaTeX rendering and auto-capitalization
/// - Diagram blocks with image display (M5: assets, M6: URLs)
/// - Fallback to placeholder when diagram image unavailable
class ContentBlockWidget extends StatelessWidget {
  const ContentBlockWidget({
    required this.block,
    this.bottomPadding = AppSpacing.sm,
    this.textStyle,
    super.key,
  });

  /// Content block to display (text or diagram)
  final ContentBlock block;

  /// Bottom padding for the widget (default: AppSpacing.sm)
  /// Can be customized based on context
  final double bottomPadding;

  /// Optional text style override for text blocks
  /// If not provided, uses default body style
  final TextStyle? textStyle;

  @override
  Widget build(BuildContext context) {
    if (block.isText) {
      return Padding(
        padding: EdgeInsets.only(bottom: bottomPadding),
        child: LatexText(
          capitalizeFirst(block.text!),
          style:
              textStyle ??
              AppTypography.body.copyWith(color: AppColors.textPrimary),
        ),
      );
    } else {
      // Diagram: show image if available, otherwise show placeholder
      return Padding(
        padding: EdgeInsets.only(bottom: bottomPadding),
        child: block.diagramImagePath != null
            ? _DiagramImage(
                imagePath: block.diagramImagePath!,
                description: block.diagramDescription!,
              )
            : DiagramPlaceholder(description: block.diagramDescription!),
      );
    }
  }
}

/// Displays a diagram image with error fallback.
///
/// M5: Loads from assets
/// M6: Will load from presigned URLs
class _DiagramImage extends StatelessWidget {
  const _DiagramImage({required this.imagePath, required this.description});

  /// Path to diagram image
  /// M5: Asset path (e.g., "assets/diagrams/triangle.png")
  /// M6: Presigned URL from backend
  final String imagePath;

  /// Description for screen readers and error fallback
  final String description;

  @override
  Widget build(BuildContext context) {
    // Resolve the image URL
    // - Full URLs (http/https): use directly
    // - Relative API paths (/api/...): prepend base URL
    // - Other paths: treat as assets
    final String resolvedPath;
    final bool isNetworkImage;

    if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
      resolvedPath = imagePath;
      isNetworkImage = true;
    } else if (imagePath.startsWith('/api/')) {
      resolvedPath = '${AppConfig.apiBaseUrl}$imagePath';
      isNetworkImage = true;
    } else {
      resolvedPath = imagePath;
      isNetworkImage = false;
    }

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(AppSpacing.diagramBorderRadius),
        border: Border.all(color: AppColors.border),
        boxShadow: AppEffects.shadow,
      ),
      clipBehavior: Clip.antiAlias,
      child: isNetworkImage
          ? Image.network(
              resolvedPath,
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) =>
                  DiagramPlaceholder(description: description),
            )
          : Image.asset(
              resolvedPath,
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) =>
                  DiagramPlaceholder(description: description),
            ),
    );
  }
}
