import 'package:flutter/material.dart';
// import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:paperlab/models/paper_result.dart';
import 'package:paperlab/models/score.dart';
import 'package:paperlab/providers/results_provider.dart';
import 'package:paperlab/router.dart';
import 'package:paperlab/theme/app_colors.dart';
// Remark feature temporarily disabled
// import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
// import 'package:paperlab/widgets/bottom_sheet_menu.dart';
import 'package:paperlab/widgets/list_items/result_list_item.dart';
import 'package:paperlab/widgets/screen_header.dart';
import 'package:skeletonizer/skeletonizer.dart';

/// Paper Results Screen - Displays complete marking results for a paper.
/// See specs/wireframes/06-paper-results-screen.md for complete specification.
///
/// Features:
/// - Header with paper name and combined score/grade
/// - Scrollable list of question results (Question 1 3/6, Question 2 6/10)
/// - Overflow menu for edge-case actions (Edit Photo Submissions)
/// - Navigation to individual question results
/// - Native back gesture/button returns to Home Screen (no X button)
///
/// Layout Pattern:
/// - Column with Expanded ListView for efficient scrolling (20+ questions)
/// - Single overflow icon in header (clean, minimal)
/// - Relies on platform back navigation (iOS gesture, Android button)
/// - SafeArea for notches/home bar handling
///
/// M6 Implementation:
/// - Fetch paperResult from API: GET /api/attempts/papers/{id}/results
/// - Loading/error states via AsyncValue
/// - Navigate to QuestionResultsScreen.fromPaper() with IDs
/// - "Edit Photo Submissions" logs to console (M7 feature)
class PaperResultsScreen extends ConsumerWidget {
  const PaperResultsScreen({required this.attemptId, super.key});

  /// Paper attempt ID for fetching results from API
  final int attemptId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final resultsAsync = ref.watch(paperResultsProvider(attemptId));

    return resultsAsync.when(
      loading: () => _buildResultsSkeleton(),
      error: (e, _) => Scaffold(
        backgroundColor: AppColors.background,
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Text(
              'Error loading results: $e',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.error),
            ),
          ),
        ),
      ),
      data: (result) => _buildResultsUI(context, result),
    );
  }

  /// Build skeleton loading state for results list.
  /// Matches the layout of ResultListItem in a ListView.
  Widget _buildResultsSkeleton() => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header skeleton - matches two-row layout
          const Padding(
            padding: EdgeInsets.all(AppSpacing.lg),
            child: Skeletonizer(
              child: Column(
                children: [
                  // Row 1: Navigation (back button + overflow menu)
                  SizedBox(
                    height: 44,
                    child: Row(
                      children: [
                        Bone.icon(size: 24),
                        Spacer(),
                        Bone.icon(size: 24),
                      ],
                    ),
                  ),
                  // Gap between rows
                  SizedBox(height: 8),
                  // Row 2: Title block (centered)
                  Column(
                    children: [
                      Bone.text(words: 3), // "Paper 1H Nov 2023"
                      SizedBox(height: 4),
                      Bone.text(words: 3), // "Grade 6 • 50/80"
                    ],
                  ),
                ],
              ),
            ),
          ),
          // List skeleton
          Expanded(
            child: Skeletonizer(
              child: ListView.separated(
                padding: const EdgeInsets.only(
                  left: AppSpacing.screenHorizontalMargin,
                  right: AppSpacing.screenHorizontalMargin,
                  bottom: AppSpacing.lg,
                ),
                itemCount: 5,
                separatorBuilder: (context, index) =>
                    const SizedBox(height: AppSpacing.sm),
                itemBuilder: (context, index) => _buildSkeletonResultItem(),
              ),
            ),
          ),
        ],
      ),
    ),
  );

  /// Build individual skeleton result item matching ResultListItem structure.
  Widget _buildSkeletonResultItem() => Container(
    constraints: const BoxConstraints(minHeight: 60.0),
    decoration: BoxDecoration(
      color: AppColors.backgroundSecondary,
      border: Border.all(color: AppColors.border),
      borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
    ),
    padding: const EdgeInsets.all(AppSpacing.md),
    child: const Row(
      children: [
        Expanded(child: Bone.text(words: 2)),
        SizedBox(width: AppSpacing.md),
        Bone.text(words: 1),
      ],
    ),
  );

  Widget _buildResultsUI(BuildContext context, PaperResult result) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header with paper name, score/grade, and overflow menu
          // Relies on native back gesture/button for navigation (no X needed)
          // Centered alignment for results summary presentation
          ScreenHeader(
            title: result.displayName,
            subtitle: result.grade != null
                ? 'Grade ${result.grade} • ${result.totalAwarded}/${result.totalAvailable}'
                : '${result.totalAwarded}/${result.totalAvailable}',
            // Remark feature temporarily disabled
            // actions: [
            //   InteractiveEffect(
            //     onTap: () => _showOverflowMenu(context),
            //     child: const SizedBox(
            //       width: 44,
            //       height: 44,
            //       child: Icon(
            //         LucideIcons.ellipsis_vertical,
            //         size: 24,
            //         color: AppColors.textPrimary,
            //       ),
            //     ),
            //   ),
            // ],
          ),

          // Scrollable question list (takes remaining space)
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.only(
                left: AppSpacing.screenHorizontalMargin,
                right: AppSpacing.screenHorizontalMargin,
                bottom: AppSpacing.lg,
              ),
              itemCount: result.questions.length,
              separatorBuilder: (context, index) =>
                  const SizedBox(height: AppSpacing.sm),
              itemBuilder: (context, index) {
                final question = result.questions[index];
                return ResultListItem(
                  title: question.displayLabel,
                  score: Score(
                    awarded: question.awarded,
                    available: question.available,
                  ),
                  onTap: () =>
                      _onQuestionTapped(context, question.questionAttemptId),
                  requiresNetwork: false,
                );
              },
            ),
          ),
        ],
      ),
    ),
  );

  /// Handle question row tap - navigate to Question Results Screen.
  void _onQuestionTapped(BuildContext context, int questionAttemptId) {
    context.push(
      AppRoutes.questionResultsFromPaper(attemptId, questionAttemptId),
    );
  }

  // Remark feature temporarily disabled
  // /// Show overflow menu with edge-case actions.
  // ///
  // /// Design pattern: Overflow menu (⋮) keeps edge-case actions available
  // /// but not prominent, matching their actual use frequency.
  // ///
  // /// M6: Single menu item (Edit Photo Submissions)
  // /// M7+: Implement retry flow with backend
  // void _showOverflowMenu(BuildContext context) {
  //   showBottomSheetMenu(
  //     context: context,
  //     items: [
  //       BottomSheetMenuItem(
  //         icon: LucideIcons.camera,
  //         label: 'Edit Photo Submissions',
  //         onTap: () {
  //           Navigator.pop(context); // Close bottom sheet
  //           _onEditPhotoSubmissionsTapped(context);
  //         },
  //       ),
  //     ],
  //   );
  // }

  // /// Handle "Edit Photo Submissions" action from overflow menu.
  // ///
  // /// Workflow:
  // /// - Creates new attempt with inheritance (copies all question photos)
  // /// - New attempt appears in Home Screen with "Draft" badge
  // /// - User navigates to Paper Upload Screen to override specific questions
  // /// - On confirm: Marking pipeline runs (only overridden questions re-marked)
  // /// - On complete: Old attempt soft-deleted (only new attempt visible)
  // ///
  // /// M6 Implementation:
  // /// - Logs to console (feature implemented in M7)
  // ///
  // /// M7 Implementation:
  // /// - POST /api/paper-attempts with student_id, paper_id, inherit_from
  // /// - Response: attempt_id, attempt_uuid
  // /// - Navigator.pushReplacement to Paper Upload Screen (new draft)
  // void _onEditPhotoSubmissionsTapped(BuildContext context) {
  //   print('Edit Photo Submissions tapped for attempt $attemptId');
  //   print('   M7 feature: Create new attempt with inheritance');
  // }
}
