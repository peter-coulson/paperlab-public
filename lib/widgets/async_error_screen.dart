import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_strings.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/screen_header.dart';

/// Standardized error screen for async data loading failures.
///
/// Displays error icon, title, message, and action buttons (Go Back, Retry).
/// Used by async screens (PaperSelectionScreen, QuestionSelectionScreen, etc.)
/// to provide consistent error UX across the app.
///
/// Uses ScreenHeader for consistent h1 (28px) title styling across all screens.
///
/// Example:
/// ```dart
/// AsyncErrorScreen(
///   title: 'Select Paper',
///   errorMessage: 'Failed to load papers',
///   errorDetails: error.toString(),
///   onRetry: () => ref.invalidate(availablePapersProvider),
/// )
/// ```
class AsyncErrorScreen extends StatelessWidget {
  const AsyncErrorScreen({
    required this.title,
    required this.errorMessage,
    required this.errorDetails,
    required this.onRetry,
    super.key,
  });

  /// Screen title (shown in ScreenHeader with h1 typography)
  final String title;

  /// User-friendly error message (e.g., "Failed to load papers")
  final String errorMessage;

  /// Detailed error information (e.g., exception.toString())
  final String errorDetails;

  /// Callback to retry the failed operation
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ScreenHeader(title: title),
          Expanded(
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.xl),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.error_outline,
                      size: AppSpacing.iconSizeError,
                      color: Colors.red,
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    Text(
                      errorMessage,
                      style: AppTypography.h2.copyWith(
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      errorDetails,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: AppSpacing.xl),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        OutlinedButton.icon(
                          onPressed: () => context.pop(),
                          icon: const Icon(Icons.arrow_back),
                          label: const Text(AppStrings.goBack),
                        ),
                        const SizedBox(width: AppSpacing.md),
                        ElevatedButton.icon(
                          onPressed: onRetry,
                          icon: const Icon(Icons.refresh),
                          label: const Text(AppStrings.retry),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    ),
  );
}
