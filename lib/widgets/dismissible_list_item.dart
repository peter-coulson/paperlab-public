import 'package:flutter/material.dart';
import 'package:flutter_slidable/flutter_slidable.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';

/// Wrapper for ListItem that adds swipe-to-reveal delete functionality.
///
/// Features:
/// - Swipe right ~25% to reveal delete button (cannot swipe further)
/// - Delete button stays revealed (doesn't auto-dismiss)
/// - Tap delete button to remove item
/// - Parent handles undo toast (via onDelete callback)
/// - Follows iOS/Material Design patterns (Gmail, iOS Mail, etc.)
///
/// Design rationale:
/// - Two-step interaction (reveal + tap) prevents accidents
/// - No modal dialogs - keeps user in context
/// - Parent controls undo behavior (keeps widget reusable)
/// - Consistent for all items (draft, marking, completed)
class DismissibleListItem extends StatefulWidget {
  const DismissibleListItem({
    required this.itemKey,
    required this.child,
    required this.onDelete,
    super.key,
  });

  /// Unique key for the item being dismissed
  final Key itemKey;

  /// The list item widget to wrap
  final Widget child;

  /// Callback when item is deleted
  final VoidCallback onDelete;

  /// Threshold at which the delete button is revealed (25% of width)
  /// - 25%: Good balance - deliberate intent without being too far
  /// - This is the maximum swipe distance (cannot swipe further)
  static const double _revealThreshold = 0.25;

  @override
  State<DismissibleListItem> createState() => _DismissibleListItemState();
}

class _DismissibleListItemState extends State<DismissibleListItem>
    with SingleTickerProviderStateMixin {
  bool _isDeleting = false;
  late AnimationController _controller;
  late Animation<double> _heightFactor;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: AppEffects.deleteDuration,
      vsync: this,
    );
    _heightFactor = Tween<double>(
      begin: 1.0,
      end: 0.0,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.linear));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  // Industry-standard delete animation: height collapse + fade + slide
  // No clipping - allows shadows to render properly
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: _heightFactor,
    // ignore: prefer_expression_function_bodies
    builder: (context, child) => Align(
      alignment: Alignment.topCenter,
      heightFactor: _heightFactor.value,
      child: Padding(
        padding: EdgeInsets.only(bottom: AppSpacing.sm * _heightFactor.value),
        child: child,
      ),
    ),
    child: AnimatedSlide(
      offset: _isDeleting ? const Offset(1.0, 0) : Offset.zero,
      duration: AppEffects.deleteDuration,
      curve: Curves.linear,
      child: AnimatedOpacity(
        opacity: _isDeleting ? 0.0 : 1.0,
        duration: AppEffects.deleteDuration,
        curve: Curves.linear,
        child: Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Slidable(
            key: widget.itemKey,
            closeOnScroll: true,
            endActionPane: ActionPane(
              // Behind motion - delete area appears from behind
              motion: const BehindMotion(),
              extentRatio: DismissibleListItem._revealThreshold,
              dragDismissible: false,
              children: [
                // Delete action - rounded to match list item corners
                CustomSlidableAction(
                  onPressed: _handleDelete,
                  backgroundColor: AppColors.destructive,
                  foregroundColor: AppColors.background,
                  padding: EdgeInsets.zero,
                  autoClose: true,
                  borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
                  child: const Center(
                    child: Icon(
                      Icons.delete_outline,
                      size: 28,
                      color: AppColors.background,
                    ),
                  ),
                ),
              ],
            ),
            child: widget.child,
          ),
        ),
      ),
    ),
  );

  /// Handles deletion - triggers fade/collapse animation then calls onDelete callback
  void _handleDelete(BuildContext context) {
    // Start all animations
    setState(() => _isDeleting = true);
    _controller
      ..forward()
      ..addStatusListener((status) {
        if (status == AnimationStatus.completed && mounted) {
          widget.onDelete();
        }
      });
  }
}
