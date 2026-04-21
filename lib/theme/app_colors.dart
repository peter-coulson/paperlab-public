import 'package:flutter/material.dart';

/// Color palette for PaperLab mobile app.
///
/// Based on design system specification:
/// context/frontend/DESIGN_SYSTEM.md
class AppColors {
  // Private constructor to prevent instantiation
  AppColors._();
  // Brand
  /// Soft Indigo - buttons, logo, active states
  static const primary = Color(0xFF667EEA);

  /// Darker indigo - hover states
  static const primaryHover = Color(0xFF5568D3);

  /// Lighter indigo - subtle accents (moderately lighter, still has color)
  static const primaryLight = Color(0xFFA5B4FC);

  // Semantic
  /// Emerald - correct answers, positive feedback
  static const success = Color(0xFF10B981);

  /// Amber - incorrect answers, attention needed
  static const error = Color(0xFFF59E0B);

  /// Red - delete, remove, permanent actions
  static const destructive = Color(0xFFEF4444);

  // Backgrounds
  /// White - main background (matches Edexcel PDFs)
  static const background = Color(0xFFFFFFFF);

  /// Very subtle gray - cards, secondary surfaces
  static const backgroundSecondary = Color(0xFFF9FAFB);

  // Text
  /// Near-black - body text, headings
  static const textPrimary = Color(0xFF111827);

  /// Medium gray - meta info, labels
  static const textSecondary = Color(0xFF6B7280);

  /// Light gray - disabled, placeholder
  static const textTertiary = Color(0xFF9CA3AF);

  // UI Chrome
  /// Dividers, borders, outlines
  static const border = Color(0xFFE5E7EB);

  // Overlays
  /// Semi-transparent black overlay for fullscreen viewers
  /// (used for close button and page indicator backgrounds)
  static final overlayBackground = Colors.black.withValues(alpha: 0.5);
}
