import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Application theme configuration for PaperLab.
///
/// Defines Material theme using design system colors and typography.
/// Based on: context/frontend/DESIGN_SYSTEM.md
class AppTheme {
  // Private constructor to prevent instantiation
  AppTheme._();

  /// Light theme (only theme for M5)
  static ThemeData get lightTheme => ThemeData(
    // Use Material 3
    useMaterial3: true,

    // Color scheme
    colorScheme: const ColorScheme.light(
      primary: AppColors.primary,
      secondary: AppColors.primaryLight,
      surface: AppColors.background,
      error: AppColors.error,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
      onSurface: AppColors.textPrimary,
      onError: Colors.white,
    ),

    // Scaffold background
    scaffoldBackgroundColor: AppColors.background,

    // App bar theme
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.background,
      foregroundColor: AppColors.textPrimary,
      elevation: 0,
      titleTextStyle: AppTypography.h2.copyWith(color: AppColors.textPrimary),
    ),

    // Text theme (maps to AppTypography for single source of truth)
    textTheme: TextTheme(
      displayLarge: AppTypography.h1.copyWith(color: AppColors.textPrimary),
      displayMedium: AppTypography.h2.copyWith(color: AppColors.textPrimary),
      bodyLarge: AppTypography.body.copyWith(color: AppColors.textPrimary),
      bodyMedium: AppTypography.body.copyWith(color: AppColors.textPrimary),
      bodySmall: AppTypography.bodySmall.copyWith(
        color: AppColors.textSecondary,
      ),
      labelLarge: AppTypography.body.copyWith(
        color: Colors.white,
        fontWeight: FontWeight.w600,
      ),
      labelMedium: AppTypography.label.copyWith(color: AppColors.textSecondary),
      labelSmall: AppTypography.caption.copyWith(color: AppColors.textTertiary),
    ),

    // Button themes
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(
          vertical: 12,
          horizontal: AppSpacing.lg,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        ),
        minimumSize: const Size(double.infinity, 48),
        textStyle: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
      ),
    ),

    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.primary,
        side: const BorderSide(color: AppColors.border),
        padding: const EdgeInsets.symmetric(
          vertical: 12,
          horizontal: AppSpacing.lg,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        ),
        minimumSize: const Size(double.infinity, 48),
        textStyle: AppTypography.body.copyWith(fontWeight: FontWeight.w600),
      ),
    ),

    // Input decoration theme
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.background,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        borderSide: const BorderSide(color: AppColors.primary, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        borderSide: const BorderSide(color: AppColors.error),
      ),
      contentPadding: const EdgeInsets.symmetric(
        vertical: 12,
        horizontal: AppSpacing.md,
      ),
      labelStyle: AppTypography.label.copyWith(color: AppColors.textSecondary),
      hintStyle: AppTypography.body.copyWith(color: AppColors.textTertiary),
    ),

    // Card theme
    cardTheme: const CardThemeData(
      color: AppColors.background,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(
          Radius.circular(AppSpacing.borderRadius),
        ),
        side: BorderSide(color: AppColors.border),
      ),
    ),

    // Divider theme
    dividerTheme: const DividerThemeData(
      color: AppColors.border,
      thickness: 1,
      space: 1,
    ),
  );
}
