import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_slidable/flutter_slidable.dart';
import 'package:go_router/go_router.dart';
import 'package:paperlab/models/paper_attempt.dart';
import 'package:paperlab/models/paper_attempt_state.dart';
import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/models/question_attempt.dart';
import 'package:paperlab/models/question_attempt_state.dart';
import 'package:paperlab/providers/attempts_provider.dart';
import 'package:paperlab/providers/discovery_provider.dart';
import 'package:paperlab/providers/upload_provider.dart';
import 'package:paperlab/router.dart';
import 'package:paperlab/screens/question_upload_screen.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_durations.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_strings.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/utils/error_messages.dart';
import 'package:paperlab/widgets/add_button.dart';
import 'package:paperlab/widgets/app_logo.dart';
import 'package:paperlab/widgets/dismissible_list_item.dart';
import 'package:paperlab/widgets/empty_state.dart';
import 'package:paperlab/widgets/home_skeleton_widgets.dart';
import 'package:paperlab/widgets/list_items/paper_list_item.dart';
import 'package:paperlab/widgets/list_items/question_list_item.dart';

/// Home Screen - Root screen for authenticated users.
/// See specs/wireframes/01-home-screen.md for complete specification.
///
/// Features:
/// - Toggle between Papers and Questions tabs
/// - AddButton for creating new attempts
/// - List of attempts with state badges
/// - State-aware navigation (tap paper/question row)
/// - Settings navigation
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({this.extra, super.key});

  /// Extra data passed from router (e.g., selection results)
  final Map<String, dynamic>? extra;

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  _TabType _selectedTab = _TabType.papers;

  /// Track processed extras to avoid duplicate handling
  Map<String, dynamic>? _lastProcessedExtra;

  @override
  void initState() {
    super.initState();

    // Prefetch common data after first frame
    // Only runs after authentication
    // (HomeScreen only shown to authenticated users)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _prefetchData();
      // Handle any selection data passed from router
      _handleSelectionExtras();
    });
  }

  @override
  void didUpdateWidget(HomeScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Handle selection data when widget is updated (e.g., navigation with
    // extra)
    if (widget.extra != oldWidget.extra && widget.extra != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _handleSelectionExtras();
      });
    }
  }

  /// Handle selection data passed from paper/question selection screens.
  void _handleSelectionExtras() {
    final extra = widget.extra;
    if (extra == null) return;

    // Avoid processing the same extra twice
    if (extra == _lastProcessedExtra) return;
    _lastProcessedExtra = extra;

    // Handle paper selection
    if (extra.containsKey('paperSelections')) {
      final selections = extra['paperSelections'] as List<String>;
      _onPaperSelectionConfirmed(selections);
    }

    // Handle question selection
    if (extra.containsKey('questionSelections')) {
      final selections = extra['questionSelections'] as List<String>;
      _onQuestionSelectionConfirmed(selections);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SlidableAutoCloseBehavior(
      // Automatically close any open slidables when another opens
      // or user scrolls
      closeWhenOpened: true,
      child: RefreshIndicator(
        onRefresh: _handleRefresh,
        child: SafeArea(
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                children: [
                  const SizedBox(height: AppSpacing.lg),
                  _buildHeader(),
                  // Optically balanced spacing for logo (40px above, 48px below
                  // for visual hierarchy with 46px logo)
                  const SizedBox(height: AppSpacing.layoutXl),
                  const AppLogo(),
                  const SizedBox(height: AppSpacing.xxl),
                  _buildAddButton(),
                  const SizedBox(height: AppSpacing.lg),
                  _buildSectionLabel(),
                  const SizedBox(height: AppSpacing.md),
                  _buildList(),
                  const SizedBox(height: AppSpacing.lg),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );

  Widget _buildHeader() => Row(
    mainAxisAlignment: MainAxisAlignment.spaceBetween,
    children: [
      _buildHeaderIcon(icon: LucideIcons.settings, onTap: _onSettingsTapped),
      _buildHeaderIcon(
        icon: LucideIcons.repeat,
        onTap: () {
          setState(() {
            _selectedTab = _selectedTab == _TabType.papers
                ? _TabType.questions
                : _TabType.papers;
          });
        },
      ),
    ],
  );

  /// Helper to create header icons with consistent interactive effects.
  /// Uses InteractiveEffect for consistent scale animation on press.
  Widget _buildHeaderIcon({
    required IconData icon,
    required VoidCallback onTap,
  }) => InteractiveEffect(
    onTap: onTap,
    child: SizedBox(
      width: 48,
      height: 48,
      child: Icon(icon, size: 26, color: AppColors.textPrimary),
    ),
  );

  Widget _buildAddButton() {
    final buttonText = _selectedTab == _TabType.papers
        ? 'Select Paper'
        : 'Select Question';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppTypography.sectionTitle(buttonText),
        const SizedBox(height: AppSpacing.sm),
        AddButton(onTap: _onAddButtonTapped, requiresNetwork: true),
      ],
    );
  }

  Widget _buildSectionLabel() {
    final labelText = _selectedTab == _TabType.papers ? 'Papers' : 'Questions';

    return Align(
      alignment: Alignment.centerLeft,
      child: AppTypography.sectionTitle(labelText),
    );
  }

  Widget _buildList() {
    if (_selectedTab == _TabType.papers) {
      final papersAsync = ref.watch(paperAttemptsProvider);
      return papersAsync.when(
        loading: () => _buildPapersSkeleton(),
        error: (e, _) => _buildErrorState(e.toString(), _TabType.papers),
        data: (papers) => _buildItemsList<PaperAttempt>(
          items: papers,
          emptyPrimaryText: 'No papers yet',
          emptySecondaryText: 'Tap "Select Paper" to get started',
          getId: (paper) => paper.id,
          buildListItem: (paper) => PaperListItem(
            title: paper.displayName,
            state: paper.state,
            grade: paper.grade,
            onTap: () => _onPaperTapped(paper),
            requiresNetwork: paper.state == PaperAttemptState.complete,
          ),
          getOnDelete: (paper) =>
              () => _onPaperDeleted(paper),
        ),
      );
    } else {
      final questionsAsync = ref.watch(questionAttemptsProvider);
      return questionsAsync.when(
        loading: () => _buildQuestionsSkeleton(),
        error: (e, _) => _buildErrorState(e.toString(), _TabType.questions),
        data: (questions) => _buildItemsList<QuestionAttempt>(
          items: questions,
          emptyPrimaryText: 'No questions yet',
          emptySecondaryText: 'Tap "Select Question" to get started',
          getId: (question) => question.id,
          buildListItem: (question) => QuestionListItem(
            title: question.displayName,
            state: question.state,
            score: question.score,
            onTap: () => _onQuestionTapped(question),
            requiresNetwork: question.state == QuestionAttemptState.complete,
          ),
          getOnDelete: (question) =>
              () => _onQuestionDeleted(question),
        ),
      );
    }
  }

  Widget _buildErrorState(String message, _TabType tabType) {
    final itemType = tabType == _TabType.papers
        ? AppStrings.papers
        : AppStrings.questions;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            '${AppStrings.failedToLoad} $itemType',
            style: AppTypography.body.copyWith(fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(message, style: AppTypography.bodySmall),
          const SizedBox(height: AppSpacing.md),
          TextButton(
            onPressed: () {
              if (tabType == _TabType.papers) {
                ref.invalidate(paperAttemptsProvider);
              } else {
                ref.invalidate(questionAttemptsProvider);
              }
            },
            child: const Text(AppStrings.retry),
          ),
        ],
      ),
    );
  }

  /// Generic list builder to eliminate duplication between papers and
  /// questions lists. Takes configuration and returns consistent list layout
  /// with dismissible items.
  Widget _buildItemsList<T>({
    required List<T> items,
    required String emptyPrimaryText,
    required String emptySecondaryText,
    required int Function(T) getId,
    required Widget Function(T) buildListItem,
    required VoidCallback Function(T) getOnDelete,
  }) {
    if (items.isEmpty) {
      return EmptyState(
        primaryText: emptyPrimaryText,
        secondaryText: emptySecondaryText,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final item in items)
          DismissibleListItem(
            key: ValueKey(getId(item)),
            itemKey: ValueKey(getId(item)),
            onDelete: getOnDelete(item),
            child: buildListItem(item),
          ),
      ],
    );
  }

  /// Build skeleton loading state for papers list.
  /// Matches PaperListItem layout structure.
  Widget _buildPapersSkeleton() => const PapersSkeleton();

  /// Build skeleton loading state for questions list.
  /// Matches QuestionListItem layout structure.
  Widget _buildQuestionsSkeleton() => const QuestionsSkeleton();

  Future<void> _onAddButtonTapped() async {
    if (_selectedTab == _TabType.papers) {
      _handlePaperSelection();
    } else {
      _handleQuestionSelection();
    }
  }

  void _handlePaperSelection() {
    context.push(AppRoutes.paperSelect);
  }

  void _handleQuestionSelection() {
    context.push(AppRoutes.questionSelect);
  }

  Future<void> _handleRefresh() async {
    try {
      // Invalidate current tab's provider
      if (_selectedTab == _TabType.papers) {
        ref.invalidate(paperAttemptsProvider);
        // Wait for new data to load
        await ref.read(paperAttemptsProvider.future);
      } else {
        ref.invalidate(questionAttemptsProvider);
        await ref.read(questionAttemptsProvider.future);
      }
    } catch (e) {
      if (mounted) ErrorMessages.showRefreshError(context, e);
    }
  }

  Future<void> _onPaperSelectionConfirmed(List<String> selections) async {
    // Parse selections: [0] = paper_code, [1] = "year-month"
    final paperCode = selections[0];
    final examDate = selections[1];

    // Read from provider (data already cached by Riverpod from
    // selection screen)
    final papers = await ref.read(availablePapersProvider.future);

    PaperMetadata selectedPaper;

    try {
      final examDateParts = examDate.split('-');
      if (examDateParts.length != 2) {
        throw const FormatException('Invalid date format. Expected "YYYY-MM"');
      }
      final year = int.parse(examDateParts[0]);
      final month = int.parse(examDateParts[1]);

      selectedPaper = papers.firstWhere(
        (p) => p.paperCode == paperCode && p.year == year && p.month == month,
        orElse: () => throw Exception(
          'Selected paper not found: $paperCode $year-$month',
        ),
      );
    } on FormatException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Invalid date format: ${e.message}')),
        );
      }
      return;
    }

    // Create draft via API
    try {
      await ref
          .read(paperUploadFlowProvider.notifier)
          .createDraft(selectedPaper);

      if (mounted) {
        unawaited(context.push(AppRoutes.paperUpload));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Failed to create draft: $e')));
      }
    }
  }

  Future<void> _onQuestionSelectionConfirmed(List<String> selections) async {
    // Parse selections:
    // [0] = paper_display_name, [1] = exam_date, [2] = question_id
    final questionId = int.parse(selections[2]);

    // Read from provider (data already cached by Riverpod from
    // selection screen)
    final questions = await ref.read(availableQuestionsProvider().future);

    final selectedQuestion = questions.firstWhere(
      (q) => q.questionId == questionId,
      orElse: () => throw Exception('Selected question not found: $questionId'),
    );

    if (mounted) {
      unawaited(
        context.push(
          AppRoutes.questionUpload(questionId),
          extra: {
            'title': QuestionUploadScreen.formatQuestionTitle(
              selectedQuestion.questionNumber,
            ),
            'subtitle': QuestionUploadScreen.formatPaperName(
              paperName: selectedQuestion.paperName,
              examDate: selectedQuestion.examDate,
            ),
            'question': selectedQuestion,
          },
        ),
      );
    }
  }

  void _onSettingsTapped() {
    context.push(AppRoutes.settings);
  }

  Future<void> _onPaperTapped(PaperAttempt paper) async {
    // State-aware navigation (see specs/STATE-LOGIC.md)
    switch (paper.state) {
      case PaperAttemptState.draft:
        // Load draft data before navigating (Riverpod best practice)
        try {
          await ref.read(paperUploadFlowProvider.notifier).loadDraft(paper.id);

          if (!mounted) return;

          // Navigate to Paper Upload Screen
          unawaited(context.push(AppRoutes.paperUpload));
        } catch (e) {
          if (!mounted) return;

          // Show error if draft can't be loaded
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text('Failed to load draft: $e')));
        }
        break;
      case PaperAttemptState.marking:
        // Navigate to Marking Progress Screen
        final subtitle = Uri.encodeComponent(paper.displayName);
        final path = '${AppRoutes.paperMarking(paper.id)}?subtitle=$subtitle';
        unawaited(context.push(path));
        break;
      case PaperAttemptState.complete:
        // Navigate to Paper Results Screen
        unawaited(context.push(AppRoutes.paperResults(paper.id)));
        break;
    }
  }

  void _onQuestionTapped(QuestionAttempt question) {
    // State-aware navigation (see specs/STATE-LOGIC.md)
    switch (question.state) {
      case QuestionAttemptState.marking:
        // Navigate to Marking Progress Screen
        context.push(AppRoutes.questionMarking(question.id));
        break;
      case QuestionAttemptState.complete:
        // Navigate to Question Results Screen
        // Practice questions use fromPractice constructor
        context.push(AppRoutes.questionResults(question.id));
        break;
    }
  }

  Future<void> _onPaperDeleted(PaperAttempt paper) async {
    try {
      final restore = await ref
          .read(paperAttemptsProvider.notifier)
          .delete(paper.id);
      if (!mounted) return;
      _showUndoToast(AppStrings.paperDeleted, restore);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${AppStrings.failedToDelete}: $e')),
      );
    }
  }

  Future<void> _onQuestionDeleted(QuestionAttempt question) async {
    try {
      final restore = await ref
          .read(questionAttemptsProvider.notifier)
          .delete(question.id);
      if (!mounted) return;
      _showUndoToast(AppStrings.questionDeleted, restore);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${AppStrings.failedToDelete}: $e')),
      );
    }
  }

  void _showUndoToast(String message, Future<void> Function() restore) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: AppDurations.undoToast,
        action: SnackBarAction(
          label: AppStrings.undo,
          onPressed: () async {
            try {
              await restore();
            } catch (e) {
              if (!mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('${AppStrings.failedToRestore}: $e')),
              );
            }
          },
        ),
      ),
    );
  }

  /// Warm Riverpod cache with commonly needed data.
  ///
  /// Prefetches data that users are likely to need immediately:
  /// - paperAttemptsProvider: Always shown on home screen
  /// - questionAttemptsProvider: One tab switch away
  /// - availablePapersProvider: Needed when tapping "Select Paper"
  ///
  /// Implementation notes:
  /// - Uses unawaited() to signal fire-and-forget intent (dart:async)
  /// - Uses Future.wait() for parallel execution (not sequential cascade)
  /// - Uses catchError() for graceful failure handling
  /// - Failures are silent - first screen to watch provider will see error
  ///   state
  /// - Only runs after authentication (HomeScreen = authenticated users only)
  /// - Providers use cacheFor() to prevent autoDispose from clearing cache
  ///
  /// Performance characteristics:
  /// - Executes in <10ms on UI thread (verified via Timeline)
  /// - Network I/O happens asynchronously off UI thread
  /// - Does not block user interaction
  ///
  /// Memory impact:
  /// - Loads ~130-315KB total (paper attempts + question attempts + papers)
  /// - Acceptable for modern devices, improves UX significantly
  void _prefetchData() {
    // Fire-and-forget with proper error handling
    unawaited(
      Future.wait([
            // Execute all three requests in PARALLEL
            ref.read(paperAttemptsProvider.future),
            ref.read(questionAttemptsProvider.future),
            ref.read(availablePapersProvider.future),
          ])
          .timeout(
            const Duration(seconds: 10),
            onTimeout: () {
              debugPrint('Prefetch timed out after 10s');
              return <List<Object>>[];
            },
          )
          .catchError((error, stackTrace) {
            // Log but don't crash - prefetch failures are graceful
            debugPrint('Prefetch failed: $error');
            if (kDebugMode) {
              debugPrintStack(stackTrace: stackTrace);
            }
            // TODO M7: Report to crash analytics (Sentry, Firebase, etc.)
            return <List<Object>>[]; // Satisfy Future.wait return type
          }),
    );
  }
}

enum _TabType { papers, questions }
