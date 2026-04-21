import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/models/question_detail_result.dart';
import 'package:paperlab/providers/results_provider.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/question_results/marking_feedback_section.dart';
import 'package:paperlab/widgets/question_results/question_section.dart';
import 'package:paperlab/widgets/question_results/your_work_section.dart';
import 'package:paperlab/widgets/screen_header.dart';
import 'package:skeletonizer/skeletonizer.dart';

/// Question Results Screen - Displays detailed marking results for a question.
///
/// Redesigned structure (M7.5):
/// 1. Question - Complete question with all parts
/// 2. Results - All evaluation results grouped by part
/// 3. Your Work - Student submission images (supplementary reference)
///
/// Design rationale:
/// - Separates question content from evaluation to reduce cognitive load
/// - Students can review "what was asked" and "how it was marked" independently
/// - Physical paper is primary reference; images are supplementary
/// - Typography creates hierarchy without heavy visual decoration
/// - Accent strips retained for status indication (research-backed pattern)
///
/// Features:
/// - Header with question identifier (Q3 P1 June 2023) and total score (5/6)
/// - NULL part handling (general context)
/// - Hierarchical parts display (a), a) i), a) ii), b))
/// - LaTeX rendering in all text content
/// - Criterion accent strips (green=100%, amber=<100%, gray=GENERAL)
/// - Typography hierarchy: label (semibold) → scheme (light) →
///   feedback (medium)
/// - Thumbnail grid for student work images
/// - Context-aware back navigation
///
/// M6 Implementation:
/// - Two navigation flows: fromPaper() and fromPractice()
/// - Fetch from API using appropriate provider
/// - Loading/error states via AsyncValue
/// - Student work images from presigned URLs
/// - Diagram images from presigned URLs
class QuestionResultsScreen extends ConsumerWidget {
  /// Constructor for paper flow - navigate from PaperResultsScreen
  const QuestionResultsScreen.fromPaper({
    required this.paperAttemptId,
    required this.questionAttemptId,
    super.key,
  }) : practiceAttemptId = null;

  /// Constructor for practice flow - navigate from MarkingInProgressScreen
  const QuestionResultsScreen.fromPractice({
    required this.practiceAttemptId,
    super.key,
  }) : paperAttemptId = null,
       questionAttemptId = null;

  /// For paper flow (both required together)
  final int? paperAttemptId;
  final int? questionAttemptId;

  /// For practice flow
  final int? practiceAttemptId;

  bool get _isPractice => practiceAttemptId != null;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final resultsAsync = _isPractice
        ? ref.watch(practiceResultsProvider(practiceAttemptId!))
        : ref.watch(
            paperQuestionResultsProvider(
              paperAttemptId: paperAttemptId!,
              questionAttemptId: questionAttemptId!,
            ),
          );

    return resultsAsync.when(
      loading: () => _buildQuestionDetailSkeleton(),
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
      data: (result) => _buildResultsUI(result),
    );
  }

  /// Build skeleton loading state for question detail results.
  /// Matches the layout of question parts and student work images.
  Widget _buildQuestionDetailSkeleton() => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header skeleton - matches two-row layout
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.screenHorizontalMargin,
                vertical: AppSpacing.lg,
              ),
              child: Skeletonizer(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Row 1: Navigation (back button)
                    const SizedBox(
                      height: 44,
                      child: Row(children: [Bone.icon(size: 24), Spacer()]),
                    ),
                    // Gap between rows
                    const SizedBox(height: 8),
                    // Row 2: Title block (left-aligned)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Bone.text(words: 2), // "Question 2"
                        const SizedBox(height: 4),
                        const Bone.text(words: 3), // "Paper 2 Nov 2023"
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.backgroundSecondary,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Bone.text(words: 1), // "2/4"
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            // Scrollable content skeleton
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.screenHorizontalMargin,
              ),
              child: Skeletonizer(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Question parts skeleton (2-3 parts)
                    ...List.generate(
                      2,
                      (_) => Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.md),
                        child: _buildSkeletonQuestionPart(),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xl),
                    // Student work section
                    const Bone.text(words: 2),
                    const SizedBox(height: AppSpacing.md),
                    // Student work image skeleton
                    Container(
                      height: 200,
                      decoration: const BoxDecoration(
                        color: AppColors.backgroundSecondary,
                        borderRadius: BorderRadius.all(Radius.circular(8)),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.lg),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );

  /// Build skeleton for a question part matching QuestionPartWidget structure.
  Widget _buildSkeletonQuestionPart() => const Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      // Part label
      Bone.text(words: 1),
      SizedBox(height: AppSpacing.xs),
      // Mark criteria card
      _SkeletonMarkCriteriaCard(),
    ],
  );

  Widget _buildResultsUI(QuestionDetailResult result) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header with question identifier and total score
            // Relies on native back gesture/button for navigation (no X needed)
            // Left-aligned for consistency with left-aligned content below
            ScreenHeader(
              title: result.questionTitle,
              subtitle: result.paperContext,
              badge: result.scoreLabel,
              alignment: HeaderAlignment.left,
            ),

            // Scrollable content with three sections
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.screenHorizontalMargin,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 1. Question section
                  QuestionSection(result: result),
                  const SizedBox(height: AppSpacing.lg),

                  // 2. Results section
                  MarkingFeedbackSection(result: result),

                  // 3. Your Work section (if images present)
                  if (result.images.isNotEmpty) ...[
                    const SizedBox(height: AppSpacing.lg),
                    YourWorkSection(images: result.images),
                  ],

                  // Bottom padding
                  const SizedBox(height: AppSpacing.lg),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

/// Skeleton widget for mark criteria card.
/// Extracted to allow const constructor.
class _SkeletonMarkCriteriaCard extends StatelessWidget {
  const _SkeletonMarkCriteriaCard();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(AppSpacing.md),
    decoration: BoxDecoration(
      color: AppColors.backgroundSecondary,
      border: Border.all(color: AppColors.border),
      borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
    ),
    child: const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Bone.text(words: 4),
        SizedBox(height: AppSpacing.xs),
        Bone.text(words: 6),
      ],
    ),
  );
}
