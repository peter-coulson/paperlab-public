import 'package:flutter/material.dart';
import 'package:paperlab/models/marking_status.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/inline_error.dart';
import 'package:paperlab/widgets/primary_button.dart';
import 'package:paperlab/widgets/screen_header.dart';

/// UI for active marking state (spinner + progress)
class MarkingProgressUI extends StatelessWidget {
  const MarkingProgressUI({
    required this.title,
    required this.statusText,
    required this.fallbackText,
    this.subtitle,
    this.progress,
    this.onClose,
    super.key,
  });

  /// Header title (e.g., "Marking in Progress", "Marking")
  final String title;

  /// Optional subtitle (e.g., "Paper 1H Nov 2023")
  final String? subtitle;

  /// Status text below spinner (e.g., "Marking your paper")
  final String statusText;

  /// Text shown when progress is null (e.g., "This may take 2-3 minutes")
  final String fallbackText;

  /// Optional progress info (for papers only - questions don't have progress)
  final ProgressInfo? progress;

  /// Optional close callback
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            title: title,
            subtitle: subtitle,
            showBack: false,
            actions: onClose != null
                ? [HeaderCloseButton(onTap: onClose!)]
                : null,
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const SizedBox(
                    width: 48,
                    height: 48,
                    child: CircularProgressIndicator.adaptive(
                      valueColor: AlwaysStoppedAnimation<Color>(
                        AppColors.primary,
                      ),
                      strokeWidth: 3,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Text(
                    statusText,
                    style: AppTypography.body.copyWith(
                      color: AppColors.textPrimary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  if (progress != null)
                    Text(
                      '${progress!.questionsCompleted}/${progress!.questionsTotal} questions marked',
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                      ),
                      textAlign: TextAlign.center,
                    )
                  else
                    Text(
                      fallbackText,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

/// UI for network/API error state
class MarkingErrorUI extends StatelessWidget {
  const MarkingErrorUI({required this.errorMessage, this.onClose, super.key});

  final String errorMessage;
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            title: 'Connection Error',
            showBack: false,
            actions: onClose != null
                ? [HeaderCloseButton(onTap: onClose!)]
                : null,
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.cloud_off,
                    size: 48,
                    color: AppColors.textSecondary,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Text(
                    'Network error',
                    style: AppTypography.body.copyWith(
                      color: AppColors.textPrimary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    errorMessage,
                    style: AppTypography.bodySmall.copyWith(
                      color: AppColors.textSecondary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.md),
                  Text(
                    'Retrying...',
                    style: AppTypography.bodySmall.copyWith(
                      color: AppColors.textSecondary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

/// UI for paper marking failed state (multiple questions)
class MarkingFailedUI extends StatelessWidget {
  const MarkingFailedUI({
    required this.error,
    required this.onRetry,
    this.onClose,
    super.key,
  });

  final ErrorInfo error;
  final VoidCallback onRetry;
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            title: 'Marking Failed',
            showBack: false,
            actions: onClose != null
                ? [HeaderCloseButton(onTap: onClose!)]
                : null,
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Marking failed for some questions',
                    style: AppTypography.body.copyWith(
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          for (final question in error.failedQuestions) ...[
                            InlineError(
                              questionNumber: 'Q${question.questionNumber}',
                              errorMessage: question.errorMessage,
                            ),
                            const SizedBox(height: AppSpacing.sm),
                          ],
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  PrimaryButton(
                    text: 'Retry Marking',
                    onTap: onRetry,
                    requiresNetwork: true,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

/// UI for question marking failed state (single error)
class QuestionMarkingFailedUI extends StatelessWidget {
  const QuestionMarkingFailedUI({
    required this.error,
    required this.onRetry,
    this.onClose,
    super.key,
  });

  final QuestionErrorInfo error;
  final VoidCallback onRetry;
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        children: [
          ScreenHeader(
            title: 'Marking Failed',
            showBack: false,
            actions: onClose != null
                ? [HeaderCloseButton(onTap: onClose!)]
                : null,
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Marking failed',
                    style: AppTypography.body.copyWith(
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Expanded(
                    child: SingleChildScrollView(
                      child: InlineError(
                        questionNumber: 'Error',
                        errorMessage: error.errorMessage,
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  if (error.canRetry)
                    PrimaryButton(
                      text: 'Retry Marking',
                      onTap: onRetry,
                      requiresNetwork: true,
                    ),
                  const SizedBox(height: AppSpacing.lg),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  );
}
