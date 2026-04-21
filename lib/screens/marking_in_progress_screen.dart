import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:paperlab/models/marking_status.dart';
import 'package:paperlab/providers/status_provider.dart';
import 'package:paperlab/router.dart';
import 'package:paperlab/widgets/marking/marking_state_ui.dart';

/// Marking In Progress Screen - Shared screen for tracking marking progress.
/// See specs/wireframes/05-marking-in-progress-screen.md for complete
/// specification.
///
/// Features:
/// - State 1: Marking in progress (spinner, status text, progress counter)
/// - State 2: Marking failed (failure list, retry button)
/// - Real API polling every 3 seconds
/// - Auto-navigation to results when complete
/// - Supports both paper and practice question contexts
///
/// States:
/// - loading/marking: Active marking, shows spinner
/// - completed: Auto-navigate to results screen
/// - failed: Marking complete with failures, shows error list
/// - error: Network/API error during polling (continues polling)
///
/// Navigation:
/// - X button → Navigator.pop (return to home)
/// - Retry Marking → M7 feature (for M6: logs to console)
/// - Auto-navigate → Results screen (paper or question based on context)
class MarkingInProgressScreen extends ConsumerStatefulWidget {
  const MarkingInProgressScreen({
    required this.attemptId,
    required this.isPaper,
    this.subtitle,
    super.key,
  });

  /// Attempt ID for polling status
  final int attemptId;

  /// Whether this is a paper (true) or practice question (false)
  final bool isPaper;

  /// Optional subtitle for header (e.g., "Paper 1H Nov 2023")
  final String? subtitle;

  @override
  ConsumerState<MarkingInProgressScreen> createState() =>
      _MarkingInProgressScreenState();
}

class _MarkingInProgressScreenState
    extends ConsumerState<MarkingInProgressScreen> {
  @override
  Widget build(BuildContext context) {
    if (widget.isPaper) {
      return _buildPaperPolling();
    } else {
      return _buildQuestionPolling();
    }
  }

  Widget _buildPaperPolling() {
    const title = 'Marking in Progress';
    const statusText = 'Marking your paper';
    const fallbackText = 'This may take 2-3 minutes';

    final statusAsync = ref.watch(paperStatusPollingProvider(widget.attemptId));

    return statusAsync.when(
      loading: () => MarkingProgressUI(
        title: title,
        subtitle: widget.subtitle,
        statusText: statusText,
        fallbackText: fallbackText,
        onClose: _handleClose,
      ),
      error: (e, _) =>
          MarkingErrorUI(errorMessage: e.toString(), onClose: _handleClose),
      data: (status) {
        // Auto-navigate on completion
        if (status.status == PaperStatusType.completed) {
          _navigateToPaperResults();
          return const SizedBox.shrink(); // Placeholder during navigation
        }

        if (status.status == PaperStatusType.failed) {
          return MarkingFailedUI(
            error: status.error!,
            onRetry: _handleRetry,
            onClose: _handleClose,
          );
        }

        return MarkingProgressUI(
          title: title,
          subtitle: widget.subtitle,
          statusText: statusText,
          fallbackText: fallbackText,
          progress: status.progress,
          onClose: _handleClose,
        );
      },
    );
  }

  Widget _buildQuestionPolling() {
    const title = 'Marking';
    const statusText = 'Marking your question';
    const fallbackText = 'This may take 30 seconds';

    final statusAsync = ref.watch(
      questionStatusPollingProvider(widget.attemptId),
    );

    // Note: Questions don't have progress info from the API,
    // so we always show fallbackText (never progress counter)
    return statusAsync.when(
      loading: () => MarkingProgressUI(
        title: title,
        subtitle: widget.subtitle,
        statusText: statusText,
        fallbackText: fallbackText,
        onClose: _handleClose,
      ),
      error: (e, _) =>
          MarkingErrorUI(errorMessage: e.toString(), onClose: _handleClose),
      data: (status) {
        // Auto-navigate on completion
        if (status.status == QuestionStatusType.completed) {
          _navigateToQuestionResults();
          return const SizedBox.shrink();
        }

        if (status.status == QuestionStatusType.failed) {
          return QuestionMarkingFailedUI(
            error: status.error!,
            onRetry: _handleRetry,
            onClose: _handleClose,
          );
        }

        return MarkingProgressUI(
          title: title,
          subtitle: widget.subtitle,
          statusText: statusText,
          fallbackText: fallbackText,
          onClose: _handleClose,
        );
      },
    );
  }

  void _handleClose() {
    context.go(AppRoutes.home);
  }

  void _navigateToPaperResults() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        context.go(AppRoutes.paperResults(widget.attemptId));
      }
    });
  }

  void _navigateToQuestionResults() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        context.go(AppRoutes.questionResults(widget.attemptId));
      }
    });
  }

  void _handleRetry() {
    // M7: Implement retry logic
    // For M6: Just log and close
    print('🔄 Retry marking requested for attempt ${widget.attemptId}');
    print('   M7 feature: Create new attempt with inheritance');
    if (mounted) {
      context.go(AppRoutes.home);
    }
  }
}
