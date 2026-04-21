import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:paperlab/models/upload_state.dart';
import 'package:paperlab/providers/upload_provider.dart';
import 'package:paperlab/router.dart';
import 'package:paperlab/screens/question_upload_screen.dart';
import 'package:paperlab/services/consent_service.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/utils/error_messages.dart';
import 'package:paperlab/widgets/list_items/question_upload_row.dart';
import 'package:paperlab/widgets/primary_button.dart';
import 'package:paperlab/widgets/screen_header.dart';

/// Paper Upload Screen - Upload photos for each question in a paper.
///
/// Features:
/// - Screen header with paper name and \[X\] close button
/// - Compact horizontal list of questions (Q1-Q20)
/// - Empty state: Shows AddButton on right
/// - Filled state: Shows photo count badge on right
/// - Auto-saves draft on exit (no confirmation dialog)
/// - Confirm button (enabled when all questions have photos)
/// - State-aware navigation (tap question → Question Upload Screen)
///
/// Design improvements (from UX review):
/// - Removed photo thumbnails (too small to verify; verified in detail screen)
/// - Horizontal layout (more compact, saves vertical space)
/// - ListView.builder for smooth performance
/// - Increased spacing (24px) for breathing room
/// - Auto-save drafts (modern UX pattern, aligns with Effortless principle)
///
/// Navigation:
/// - Back/\[X\] → Home (auto-saves draft if photos exist)
/// - Question row tap → Question Upload Screen (paper context)
/// - Confirm → Marking in Progress Screen
class PaperUploadScreen extends ConsumerStatefulWidget {
  const PaperUploadScreen({super.key});

  @override
  ConsumerState<PaperUploadScreen> createState() => _PaperUploadScreenState();
}

class _PaperUploadScreenState extends ConsumerState<PaperUploadScreen> {
  // Track photos for each question (Map<questionNumber, List<XFile>>)
  final Map<int, List<XFile>> _questionPhotos = {};

  @override
  Widget build(BuildContext context) {
    final uploadState = ref.watch(paperUploadFlowProvider);

    return uploadState.when(
      initial: () => const Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(child: Center(child: Text('No draft found'))),
      ),
      creating: () => const Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(child: Center(child: CircularProgressIndicator())),
      ),
      draft:
          (
            attemptId,
            attemptUuid,
            paperName,
            examDate,
            questionCount,
            submitted,
          ) {
            // Initialize photos map if needed
            for (int i = 1; i <= questionCount; i++) {
              _questionPhotos.putIfAbsent(i, () => []);
            }

            return _buildUploadUI(
              paperName,
              examDate,
              questionCount,
              submitted,
            );
          },
      submitting: () => const Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(child: Center(child: CircularProgressIndicator())),
      ),
      submitted: () => const Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(child: Center(child: Text('Submitted'))),
      ),
    );
  }

  Widget _buildUploadUI(
    String paperName,
    DateTime examDate,
    int questionCount,
    Map<int, int> submittedQuestions,
  ) {
    /// Count how many questions have at least one photo
    /// Use backend data (submittedQuestions) as source of truth
    final completedCount = submittedQuestions.length;

    /// Check if all questions have at least one photo
    /// Use backend data to validate completion
    final isFormValid = completedCount == questionCount;

    // Format paper display name using centralized logic
    final paperDisplayName = QuestionUploadScreen.formatPaperName(
      paperName: paperName,
      examDate: examDate,
    );

    return Scaffold(
      backgroundColor: AppColors.background,
      body: RefreshIndicator(
        onRefresh: _handleRefresh,
        child: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header with paper name, progress, and [X] close button
              ScreenHeader(
                title: paperDisplayName,
                subtitle: '$completedCount/$questionCount uploaded',
                actions: [
                  // Navigate to home (clears navigation stack)
                  // Handles both new drafts and existing drafts
                  HeaderCloseButton(onTap: () => context.go(AppRoutes.home)),
                ],
              ),

              // Scrollable question list (ListView.builder for performance)
              Expanded(
                child: ListView.builder(
                  itemCount: questionCount,
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.lg,
                  ),
                  itemBuilder: (context, index) {
                    final questionNumber = index + 1;
                    return Padding(
                      padding: EdgeInsets.only(
                        top: index == 0 ? 0 : AppSpacing.lg,
                        bottom: index == questionCount - 1 ? AppSpacing.lg : 0,
                      ),
                      child: _buildQuestionRow(
                        questionNumber,
                        paperName,
                        examDate,
                        submittedQuestions,
                      ),
                    );
                  },
                ),
              ),

              // Bottom action: Confirm button
              Padding(
                padding: const EdgeInsets.all(AppSpacing.lg),
                child: PrimaryButton(
                  text: 'Confirm',
                  onTap: isFormValid ? _handleConfirm : null,
                  requiresNetwork: true,
                  disabled: !isFormValid,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildQuestionRow(
    int questionNumber,
    String paperName,
    DateTime examDate,
    Map<int, int> submittedQuestions,
  ) {
    // Use backend data as source of truth
    // If question is submitted, show count from backend
    // Otherwise, show count from local state (for questions being edited)
    final photoCount =
        submittedQuestions[questionNumber] ??
        (_questionPhotos[questionNumber]?.length ?? 0);

    return QuestionUploadRow(
      questionNumber: questionNumber,
      photoCount: photoCount,
      onTap: () => _navigateToQuestionUpload(
        questionNumber,
        paperName,
        examDate,
        submittedQuestions,
      ),
      requiresNetwork: false,
    );
  }

  void _navigateToQuestionUpload(
    int questionNumber,
    String paperName,
    DateTime examDate,
    Map<int, int> submittedQuestions,
  ) {
    // If question already submitted to backend, show blank upload screen
    // This allows fresh resubmission without cached local images
    final isAlreadySubmitted = submittedQuestions.containsKey(questionNumber);
    final existingPhotos = isAlreadySubmitted
        ? <XFile>[]
        : _questionPhotos[questionNumber]!;

    context
        .push<List<XFile>>(
          AppRoutes.paperQuestionUpload(questionNumber),
          extra: {
            'title': QuestionUploadScreen.formatQuestionTitle(questionNumber),
            'subtitle': QuestionUploadScreen.formatPaperName(
              paperName: paperName,
              examDate: examDate,
            ),
            'existingPhotos': existingPhotos,
          },
        )
        .then((updatedPhotos) async {
          if (!mounted) return;
          if (updatedPhotos != null && updatedPhotos.isNotEmpty) {
            // Check AI consent before uploading (App Store requirement)
            final hasConsent = await ConsentService.instance.ensureAiConsent(
              context,
            );
            if (!hasConsent) {
              // User declined consent - don't upload
              // Photos are not saved to local state either
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      'AI consent is required to mark your papers. '
                      'You can grant consent when you next upload.',
                    ),
                    duration: Duration(seconds: 4),
                  ),
                );
              }
              return;
            }

            // Update local state
            setState(() {
              _questionPhotos[questionNumber] = updatedPhotos;
            });

            // Upload to backend
            try {
              await ref
                  .read(paperUploadFlowProvider.notifier)
                  .uploadQuestion(
                    questionNumber: questionNumber,
                    images: updatedPhotos,
                  );
            } catch (e) {
              // Error occurred - show user-friendly message
              // Local state is preserved, so user can retry
              if (mounted) {
                final errorMessage = ErrorMessages.getUserMessage(e);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(errorMessage),
                    backgroundColor: AppColors.error,
                    duration: const Duration(seconds: 4),
                  ),
                );
              }
            }
          }
        });
  }

  Future<void> _handleRefresh() async {
    try {
      final uploadState = ref.read(paperUploadFlowProvider);
      if (uploadState is! PaperUploadStateDraft) return;

      // Reload draft details from backend
      await ref
          .read(paperUploadFlowProvider.notifier)
          .loadDraft(uploadState.attemptId);
    } catch (e) {
      if (mounted) ErrorMessages.showRefreshError(context, e);
    }
  }

  Future<void> _handleConfirm() async {
    try {
      final attemptId = await ref
          .read(paperUploadFlowProvider.notifier)
          .finalize();

      if (mounted) {
        context.go(AppRoutes.paperMarking(attemptId));
      }
    } catch (e) {
      // Error occurred - show user-friendly message
      // User can retry by tapping Confirm again
      if (mounted) {
        final errorMessage = ErrorMessages.getUserMessage(e);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }
}
