import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/list_items/list_item_container.dart';

/// Horizontal question upload row for paper upload screen.
/// Compact single-row layout: question label left, status icon right.
///
/// States:
/// - Empty: Circle icon (○) - neutral, indicates not uploaded
/// - Uploaded: Green checkmark icon (✓) - positive feedback
///
/// Design rationale:
/// - Full label "Question 2" instead of "Q2" - plenty of horizontal space
/// - Simple binary visual state (scannable at a glance)
/// - Green checkmark provides satisfying completion feedback
/// - Horizontal layout is more compact than vertical (saves 16px per row)
/// - Tappable entire row for quick access (no redundant buttons)
class QuestionUploadRow extends StatelessWidget {
  const QuestionUploadRow({
    required this.questionNumber,
    required this.photoCount,
    required this.onTap,
    required this.requiresNetwork,
    super.key,
  });

  final int questionNumber;
  final int photoCount;
  final VoidCallback onTap;
  final bool requiresNetwork;

  static const double _iconSize = 24;

  @override
  Widget build(BuildContext context) {
    final isEmpty = photoCount == 0;

    return ListItemContainer(
      onTap: onTap,
      requiresNetwork: requiresNetwork,
      child: Row(
        children: [
          // Left: Question label (Question 1, Question 2, etc.)
          Text(
            'Question $questionNumber',
            style: AppTypography.h2.copyWith(color: AppColors.textPrimary),
          ),

          const Spacer(),

          // Right: Status icon (circle or green checkmark)
          Icon(
            isEmpty ? LucideIcons.circle : LucideIcons.circle_check,
            size: _iconSize,
            color: isEmpty ? AppColors.textTertiary : AppColors.success,
          ),
        ],
      ),
    );
  }
}
