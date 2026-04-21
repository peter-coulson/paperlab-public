import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Pill-shaped badge indicator for list items.
/// Follows 8-point grid system with subtle, refined styling.
///
/// Design specifications:
/// - Height: 24px (3× 8pt grid) - compact, unobtrusive
/// - Horizontal padding: 11px - tight but readable
/// - Border radius: 12px (half-height) - perfect pill shape
/// - Border width: 1px - delicate outline for subtle presence
/// - Text: 12px pillBadgeText (Inter, weight 500, 0.8px letter-spacing)
///   compact for pill badge display, meets WCAG minimum
/// - Style: Outlined (transparent bg) - less visual weight than filled
class PillBadge extends StatelessWidget {
  const PillBadge({
    required this.backgroundColor,
    required this.borderColor,
    required this.textColor,
    required this.label,
    super.key,
  });

  final Color backgroundColor;
  final Color borderColor;
  final Color textColor;
  final String label;

  // Badge dimensions - compact and unobtrusive
  static const double _height = 24.0;
  static const double _minWidth = 70.0;
  static const double _horizontalPadding = 11.0;
  static const double _borderRadius = 12.0;
  static const double _borderWidth = 1.0;

  @override
  Widget build(BuildContext context) => Container(
    height: _height,
    constraints: const BoxConstraints(minWidth: _minWidth),
    padding: const EdgeInsets.symmetric(horizontal: _horizontalPadding),
    decoration: BoxDecoration(
      color: backgroundColor,
      border: Border.all(color: borderColor, width: _borderWidth),
      borderRadius: BorderRadius.circular(_borderRadius),
    ),
    child: Center(
      child: Text(
        label.toUpperCase(),
        style: AppTypography.pillBadgeText.copyWith(color: textColor),
      ),
    ),
  );
}
