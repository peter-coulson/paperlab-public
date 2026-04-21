import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:go_router/go_router.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Universal screen header for ALL screens in the app.
/// Two-row layout pattern: navigation separated from title content.
///
/// Design:
/// - Row 1: Navigation (back button, actions) - fixed 44px height
/// - Row 2: Title block (title, subtitle, badge) - centered or left-aligned
/// - 8px gap between rows for breathing room
///
/// Features:
/// - Optional back button (default: true, uses Navigator.pop)
/// - Optional subtitle line (16px Inter Regular, gray)
/// - Optional badge (14px pill with backgroundSecondary)
/// - Optional action icons (right side of navigation row)
/// - Alignment control: center (default) or left
///
/// Used in:
/// - Selection Screen (Select Paper, Select Question)
/// - Paper Upload Screen
/// - Question Upload Screen
/// - Marking Progress Screen
/// - Paper Results Screen
/// - Question Results Screen
/// - Settings Screen
enum HeaderAlignment { center, left }

class ScreenHeader extends StatelessWidget {
  const ScreenHeader({
    required this.title,
    this.subtitle,
    this.badge,
    this.showBack = true,
    this.onBack,
    this.actions,
    this.alignment = HeaderAlignment.center,
    super.key,
  });

  /// Screen title (e.g., "Question 2", "Select Paper")
  /// Uses 28px IBM Plex Serif SemiBold
  final String title;

  /// Optional context line (e.g., "Paper 2 Nov 2023")
  /// Uses 16px Inter Regular, textSecondary
  final String? subtitle;

  /// Optional badge text (e.g., "2/4", "Draft")
  /// Rendered as pill with backgroundSecondary
  final String? badge;

  /// Show back chevron in navigation row (default: true)
  /// When true, uses Navigator.pop on tap
  final bool showBack;

  /// Optional custom back behavior
  /// If null, defaults to Navigator.pop(context)
  final VoidCallback? onBack;

  /// Optional action icons for navigation row (right side)
  /// Should be wrapped in InteractiveEffect with 44×44 touch target
  final List<Widget>? actions;

  /// Title block alignment (default: center)
  final HeaderAlignment alignment;

  @override
  Widget build(BuildContext context) => Padding(
    // Tight top padding (8px) - SafeArea already handles system UI
    // Standard horizontal margin (24px) - aligns with content throughout app
    // Moderate bottom padding (16px) - separates from content below
    padding: const EdgeInsets.only(
      left: AppSpacing.screenHorizontalMargin,
      right: AppSpacing.screenHorizontalMargin,
      top: AppSpacing.sm,
      bottom: AppSpacing.md,
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Row 1: Navigation (back button + actions)
        SizedBox(
          height: 44,
          child: Row(
            children: [
              // Back button
              // Icon left-aligned within 44×44 touch target for proper
              // alignment with left-aligned titles
              if (showBack)
                Tooltip(
                  message: 'Back',
                  child: InteractiveEffect(
                    key: const ValueKey('back_button'),
                    onTap: onBack ?? () => context.pop(),
                    child: const SizedBox(
                      width: 44,
                      height: 44,
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Icon(
                          LucideIcons.chevron_left,
                          size: 24,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                  ),
                )
              else
                const SizedBox(width: 44), // Maintain alignment

              const Spacer(),

              // Action icons
              if (actions != null) ...actions!,
            ],
          ),
        ),

        // Gap between navigation and title
        const SizedBox(height: 8),

        // Row 2: Title block (title, subtitle, badge)
        Column(
          crossAxisAlignment: alignment == HeaderAlignment.center
              ? CrossAxisAlignment.center
              : CrossAxisAlignment.start,
          children: [
            // Title
            Text(
              title,
              style: AppTypography.h1.copyWith(color: AppColors.textPrimary),
              textAlign: alignment == HeaderAlignment.center
                  ? TextAlign.center
                  : TextAlign.left,
            ),

            // Subtitle
            if (subtitle != null) ...[
              const SizedBox(height: 4),
              Text(
                subtitle!,
                style: AppTypography.headerSubtitle.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: alignment == HeaderAlignment.center
                    ? TextAlign.center
                    : TextAlign.left,
              ),
            ],

            // Badge
            if (badge != null) ...[
              const SizedBox(height: 8),
              _HeaderBadge(text: badge!),
            ],
          ],
        ),
      ],
    ),
  );
}

/// Badge widget for header scores and status indicators.
/// Renders as a pill with backgroundSecondary and border.
/// Flat styling (no shadow) to indicate informational, not interactive.
class _HeaderBadge extends StatelessWidget {
  const _HeaderBadge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
    decoration: BoxDecoration(
      color: AppColors.backgroundSecondary,
      border: Border.all(color: AppColors.border),
      borderRadius: BorderRadius.circular(4),
    ),
    child: Text(
      text,
      style: AppTypography.scoreBadgeText.copyWith(
        color: AppColors.textPrimary,
      ),
    ),
  );
}

/// Close button for ScreenHeader actions.
/// Standard 44×44 touch target with X icon.
/// Icon right-aligned within touch target for symmetric edge alignment
/// with left-aligned back button.
///
/// Usage:
/// ```dart
/// ScreenHeader(
///   title: 'Upload',
///   actions: [HeaderCloseButton(onTap: () => Navigator.pop(context))],
/// )
/// ```
class HeaderCloseButton extends StatelessWidget {
  const HeaderCloseButton({required this.onTap, super.key});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => InteractiveEffect(
    onTap: onTap,
    child: const SizedBox(
      width: 44,
      height: 44,
      child: Align(
        alignment: Alignment.centerRight,
        child: Icon(LucideIcons.x, size: 24, color: AppColors.textPrimary),
      ),
    ),
  );
}
