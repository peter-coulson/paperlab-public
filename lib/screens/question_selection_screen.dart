import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/providers/discovery_provider.dart';
import 'package:paperlab/screens/selection_screen.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_strings.dart';
import 'package:paperlab/utils/question_selection_builder.dart';
import 'package:paperlab/widgets/async_error_screen.dart';
import 'package:skeletonizer/skeletonizer.dart';

/// Domain-specific screen for question selection with async data loading.
///
/// Handles loading/error states for dual providers (questions + papers) and
/// delegates to generic SelectionScreen for presentation.
/// Implements "navigate then load" pattern (M7).
///
/// Architecture:
/// - Watches questionsWithPapersProvider (combines both providers)
/// - Shows skeleton while loading
/// - Shows error screen with retry/back on error
/// - Delegates to SelectionScreen when data ready
class QuestionSelectionScreen extends ConsumerWidget {
  const QuestionSelectionScreen({required this.onConfirm, super.key});

  /// Callback when user confirms selection.
  /// Receives list of selected values from dropdowns.
  final void Function(List<String>) onConfirm;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dataAsync = ref.watch(questionsWithPapersProvider);

    return dataAsync.when(
      loading: () => _buildSkeletonScreen(),
      error: (error, stackTrace) => AsyncErrorScreen(
        title: AppStrings.titleSelectQuestion,
        errorMessage: AppStrings.failedToLoadQuestions,
        errorDetails: error.toString(),
        onRetry: () => ref.invalidate(questionsWithPapersProvider),
      ),
      data: (data) => SelectionScreen(
        title: AppStrings.titleSelectQuestion,
        fieldBuilder: (selections) => buildQuestionSelectionFields(
          questions: data.questions,
          papers: data.papers,
          selectedPaperDisplayName: selections.isNotEmpty
              ? selections[0]
              : null,
          selectedExamDate: selections.length > 1 ? selections[1] : null,
        ),
        onConfirm: (selections) {
          onConfirm(selections); // Navigate first (will replace route)
        },
      ),
    );
  }

  Widget _buildSkeletonScreen() => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Skeletonizer(
        child: Column(
          children: [
            // Header skeleton - matches two-row layout
            const Padding(
              padding: EdgeInsets.all(AppSpacing.lg),
              child: Column(
                children: [
                  // Row 1: Navigation (back button only)
                  SizedBox(
                    height: 44,
                    child: Row(children: [Bone.icon(size: 24), Spacer()]),
                  ),
                  // Gap between rows
                  SizedBox(height: 8),
                  // Row 2: Title block (centered)
                  Bone.text(words: 2), // "Select Question"
                ],
              ),
            ),
            // Dropdowns skeleton
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                children: [
                  // Skeleton dropdowns using Bone widgets
                  _buildSkeletonDropdown(),
                  const SizedBox(height: AppSpacing.lg),
                  _buildSkeletonDropdown(),
                  const SizedBox(height: AppSpacing.lg),
                  _buildSkeletonDropdown(),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
  );

  /// Build skeleton dropdown using Bone widgets.
  /// Mimics AppDropdown visual structure without complex form widgets.
  Widget _buildSkeletonDropdown() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      // Label placeholder
      const Bone.text(words: 2),
      const SizedBox(height: AppSpacing.sm),
      // Dropdown placeholder - matches AppDropdown height (~48px)
      Container(
        height: 48,
        decoration: BoxDecoration(
          color: AppColors.background,
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        ),
      ),
    ],
  );
}
