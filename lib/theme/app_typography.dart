import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:paperlab/theme/app_colors.dart';

/// Typography scale for PaperLab mobile app.
///
/// Based on design system specification:
/// context/frontend/DESIGN_SYSTEM.md
///
/// Fonts:
/// - IBM Plex Serif: Headers, screen titles
/// - Inter: Body text, UI elements, all content
class AppTypography {
  // Private constructor to prevent instantiation
  AppTypography._();
  // Headers (IBM Plex Serif)

  /// Logo - Brand identity
  static final logo = GoogleFonts.ibmPlexSerif(
    fontSize: 46,
    fontWeight: FontWeight.w600, // SemiBold
    height: 1.2, // 55.2px line height / 46px font size
    letterSpacing: -0.65,
  );

  /// H1 - Screen titles in ScreenHeader
  /// (e.g., "Q3 P1 June 2023", "Select Paper")
  static final h1 = GoogleFonts.ibmPlexSerif(
    fontSize: 28,
    fontWeight: FontWeight.w600, // SemiBold
    height: 1.4, // 39.2px line height / 28px font size
    letterSpacing: -0.4,
  );

  /// H2 - List/card/dialog titles (e.g., "Question 3", "Paper 1 Nov 2023")
  static final h2 = GoogleFonts.ibmPlexSerif(
    fontSize: 20,
    fontWeight: FontWeight.w500, // Medium
    height: 1.4, // 28px / 20px
    letterSpacing: 0,
  );

  // Body (Inter)

  /// Body - Default body text
  /// BASE SIZE for app: mark schemes, feedback, UI text
  static final body = GoogleFonts.inter(
    fontSize: 16,
    fontWeight: FontWeight.w400, // Regular
    height: 1.5, // 24px / 16px
    letterSpacing: 0,
  );

  /// Body Small - Secondary body text
  static final bodySmall = GoogleFonts.inter(
    fontSize: 14,
    fontWeight: FontWeight.w400, // Regular
    height: 1.43, // 20px / 14px
    letterSpacing: 0,
  );

  /// Header Subtitle - Context line in ScreenHeader
  /// (e.g., "Paper 2 Nov 2023", "Grade 5", "2/6 uploaded")
  /// Larger than bodySmall to maintain proper hierarchy with 28px h1 title.
  /// Used ONLY in ScreenHeader - use bodySmall for other secondary text.
  static final headerSubtitle = GoogleFonts.inter(
    fontSize: 16,
    fontWeight: FontWeight.w400, // Regular
    height: 1.5, // 24px / 16px
    letterSpacing: 0,
  );

  // UI (Inter)

  /// Label - Form labels, metadata
  static final label = GoogleFonts.inter(
    fontSize: 14,
    fontWeight: FontWeight.w500, // Medium
    height: 1.43, // 20px / 14px
    letterSpacing: 0.1,
  );

  /// Section Title - Organizational headers ("PAPERS", "YOUR WORK")
  /// Equal to body size, differentiated by uppercase + medium weight +
  /// wide spacing
  static final sectionTitleStyle = GoogleFonts.inter(
    fontSize: 16,
    fontWeight: FontWeight.w500, // Medium
    height: 1.5, // 24px / 16px
    letterSpacing: 0.8,
  );

  /// Caption - Hints, small metadata
  static final caption = GoogleFonts.inter(
    fontSize: 12,
    fontWeight: FontWeight.w400, // Regular
    height: 1.5, // 18px / 12px
    letterSpacing: 0.4,
  );

  /// Pill Badge - Compact pill badge labels (status indicators)
  static final pillBadgeText = GoogleFonts.inter(
    fontSize: 12,
    fontWeight: FontWeight.w500, // Medium
    height: 1.0, // Tight for compact badge
    letterSpacing: 0.8,
  );

  /// Score Badge - Header score badges (2/4, 50/80)
  /// Larger than status badges because scores are primary information users
  /// actively read, while status badges are recognition patterns
  static final scoreBadgeText = GoogleFonts.inter(
    fontSize: 14,
    fontWeight: FontWeight.w500, // Medium
    height: 1.0, // Tight for compact badge
    letterSpacing: 0.4,
  );

  // Helper methods for consistent text rendering

  /// Creates uppercase section title text with standardized styling.
  ///
  /// This helper enforces visual consistency across the app for a
  /// specific UI pattern:
  /// uppercase organizational headers that appear throughout the interface.
  ///
  /// **Why this helper exists:**
  /// - Provides single source of truth for section title styling
  /// - Eliminates boilerplate (.toUpperCase() + .copyWith()) on every screen
  /// - Ensures all section titles have identical appearance and behavior
  /// - Design system principle: abstract repeated UI patterns
  ///
  /// **When to use:**
  /// - Section headers on screens (e.g., "PAPERS", "QUESTIONS")
  /// - Labels above action buttons (e.g., "SELECT PAPER" above AddButton)
  /// - Any uppercase navigational or organizational labels
  ///
  /// **When NOT to use:**
  /// - Regular body text or headings (use h1, h2, body instead)
  /// - Button text inside buttons (buttons have their own styling)
  /// - Form field labels (use label instead)
  /// - Content that shouldn't be uppercase
  ///
  /// **Usage:**
  /// ```dart
  /// // Default (textPrimary color)
  /// AppTypography.sectionTitle('Papers')
  ///
  /// // Custom color
  /// AppTypography.sectionTitle('Questions', color: AppColors.textSecondary)
  /// ```
  static Widget sectionTitle(
    String text, {
    Color color = AppColors.textPrimary,
  }) =>
      Text(text.toUpperCase(), style: sectionTitleStyle.copyWith(color: color));
}
