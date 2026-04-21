import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:skeletonizer/skeletonizer.dart';

/// Skeleton loading state for papers list.
///
/// Displays 3 skeleton items matching the structure of PaperListItem.
/// Used by HomeScreen while paperAttemptsProvider is loading.
class PapersSkeleton extends StatelessWidget {
  const PapersSkeleton({super.key});

  @override
  Widget build(BuildContext context) => Skeletonizer(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: List.generate(
        3,
        (_) => const Padding(
          padding: EdgeInsets.only(bottom: AppSpacing.sm),
          child: _SkeletonListItem(),
        ),
      ),
    ),
  );
}

/// Skeleton loading state for questions list.
///
/// Displays 3 skeleton items matching the structure of QuestionListItem.
/// Used by HomeScreen while questionAttemptsProvider is loading.
class QuestionsSkeleton extends StatelessWidget {
  const QuestionsSkeleton({super.key});

  @override
  Widget build(BuildContext context) => Skeletonizer(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: List.generate(
        3,
        (_) => const Padding(
          padding: EdgeInsets.only(bottom: AppSpacing.sm),
          child: _SkeletonListItem(),
        ),
      ),
    ),
  );
}

/// Shared skeleton list item matching ListItemContainer structure.
///
/// Private widget used by both PapersSkeleton and QuestionsSkeleton.
/// Matches the visual structure of PaperListItem and QuestionListItem.
class _SkeletonListItem extends StatelessWidget {
  const _SkeletonListItem();

  @override
  Widget build(BuildContext context) => Container(
    constraints: const BoxConstraints(minHeight: 60.0),
    decoration: BoxDecoration(
      color: AppColors.backgroundSecondary,
      border: Border.all(color: AppColors.border),
      borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
    ),
    padding: const EdgeInsets.all(AppSpacing.md),
    child: const Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [Bone.text(words: 3)],
          ),
        ),
        SizedBox(width: AppSpacing.md),
        Bone.text(words: 1),
      ],
    ),
  );
}
