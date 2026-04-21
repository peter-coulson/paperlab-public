import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/list_items/list_item_container.dart';

/// Upload list item with content area (no badge).
/// See specs/SHARED_COMPONENTS.md for complete specification.
class UploadListItem extends StatelessWidget {
  const UploadListItem({
    required this.title,
    required this.content,
    required this.onTap,
    required this.requiresNetwork,
    super.key,
  });

  final String title;
  final Widget content;
  final VoidCallback onTap;
  final bool requiresNetwork;

  @override
  Widget build(BuildContext context) => ListItemContainer(
    onTap: onTap,
    requiresNetwork: requiresNetwork,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: AppTypography.h2.copyWith(color: AppColors.textPrimary),
        ),
        const SizedBox(height: AppSpacing.md),
        content,
      ],
    ),
  );
}
