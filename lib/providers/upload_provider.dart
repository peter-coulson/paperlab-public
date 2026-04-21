import 'package:image_picker/image_picker.dart';
import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/models/question_metadata.dart';
import 'package:paperlab/models/upload_state.dart';
import 'package:paperlab/providers/attempts_provider.dart';
import 'package:paperlab/providers/providers.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';

part 'upload_provider.g.dart';

/// Paper upload flow orchestration.
@Riverpod(keepAlive: true)
class PaperUploadFlow extends _$PaperUploadFlow {
  @override
  PaperUploadState build() => const PaperUploadState.initial();

  /// Step 1a: Create draft paper attempt (new paper).
  Future<void> createDraft(PaperMetadata paper) async {
    state = const PaperUploadState.creating();
    final repo = ref.read(uploadRepositoryProvider);
    final uuid = const Uuid().v4();

    final response = await repo.createPaperAttempt(
      attemptUuid: uuid,
      paper: paper,
    );

    state = PaperUploadState.draft(
      attemptId: response.id,
      attemptUuid: response.attemptUuid,
      paperName: response.paperName,
      examDate: response.examDate,
      questionCount: paper.questionCount,
      submittedQuestions: {},
    );

    // Invalidate so HomeScreen shows new draft immediately
    ref.invalidate(paperAttemptsProvider);
  }

  /// Step 1b: Load existing draft (resume paper).
  Future<void> loadDraft(int attemptId) async {
    state = const PaperUploadState.creating();
    final repo = ref.read(uploadRepositoryProvider);

    final details = await repo.getDraftDetails(attemptId);

    state = PaperUploadState.draft(
      attemptId: details.id,
      attemptUuid: details.attemptUuid,
      paperName: details.paperName,
      examDate: details.examDate,
      questionCount: details.questionCount,
      submittedQuestions: details.submittedQuestions,
    );
  }

  /// Step 2: Upload images for one question.
  /// Throws on failure - caller should handle errors.
  Future<void> uploadQuestion({
    required int questionNumber,
    required List<XFile> images,
  }) async {
    final currentState = state;
    if (currentState is! PaperUploadStateDraft) return;

    final repo = ref.read(uploadRepositoryProvider);
    final stagingKeys = <String>[];

    try {
      // 1. Get presigned URLs and upload each image
      for (int i = 0; i < images.length; i++) {
        final filename = 'q${questionNumber}_${i + 1}.jpg';
        final presigned = await repo.getPresignedUrl(
          attemptUuid: currentState.attemptUuid,
          filename: filename,
        );

        // 2. Upload to R2 (using bytes for cross-platform compatibility)
        final bytes = await images[i].readAsBytes();
        final success = await repo.uploadToR2(
          presignedUrl: presigned.uploadUrl,
          bytes: bytes,
        );
        if (!success) {
          throw UploadException('Failed to upload image ${i + 1}');
        }

        stagingKeys.add(presigned.stagingKey);
      }

      // 3. Submit question to API (atomic commit moves staging → permanent)
      await repo.submitPaperQuestion(
        attemptId: currentState.attemptId,
        questionNumber: questionNumber,
        stagingKeys: stagingKeys,
      );

      // 4. Update state on success
      state = currentState.copyWith(
        submittedQuestions: {
          ...currentState.submittedQuestions,
          questionNumber: stagingKeys.length,
        },
      );
    } catch (e) {
      // Staging images auto-delete via R2 lifecycle (24h TTL)
      // No manual cleanup needed - rethrow for UI to handle
      rethrow;
    }
  }

  /// Step 3: Finalize paper (triggers marking).
  Future<int> finalize() async {
    final currentState = state;
    if (currentState is! PaperUploadStateDraft) {
      throw StateError('Not in draft');
    }

    state = const PaperUploadState.submitting();

    final repo = ref.read(uploadRepositoryProvider);
    await repo.finalizePaperAttempt(currentState.attemptId);

    state = const PaperUploadState.submitted();

    // Invalidate attempts list so home screen refreshes
    ref.invalidate(paperAttemptsProvider);

    return currentState.attemptId;
  }
}

/// Practice upload flow (single-phase).
@Riverpod(keepAlive: true)
class PracticeUploadFlow extends _$PracticeUploadFlow {
  @override
  PracticeUploadState build() => const PracticeUploadState.initial();

  /// Reset state to initial (call before starting a new upload flow).
  void reset() {
    state = const PracticeUploadState.initial();
  }

  /// Single call: upload images + submit + mark.
  /// Throws on failure - caller should handle errors.
  Future<int> submit({
    required QuestionMetadata question,
    required List<XFile> images,
  }) async {
    // Guard against concurrent calls - defense in depth
    if (state is PracticeUploadStateUploading ||
        state is PracticeUploadStateSubmitting) {
      throw StateError('Upload already in progress');
    }

    state = const PracticeUploadState.uploading();

    try {
      final repo = ref.read(uploadRepositoryProvider);
      final uuid = const Uuid().v4();

      // 1. Upload all images to staging
      final stagingKeys = <String>[];
      for (int i = 0; i < images.length; i++) {
        final filename = 'img_${i + 1}.jpg';
        final presigned = await repo.getPresignedUrl(
          attemptUuid: uuid,
          filename: filename,
        );

        final bytes = await images[i].readAsBytes();
        final success = await repo.uploadToR2(
          presignedUrl: presigned.uploadUrl,
          bytes: bytes,
        );
        if (!success) {
          throw UploadException('Failed to upload image ${i + 1}');
        }

        stagingKeys.add(presigned.stagingKey);
      }

      // 2. Single submit call (creates + marks)
      state = const PracticeUploadState.submitting();
      final response = await repo.submitPracticeQuestion(
        attemptUuid: uuid,
        questionId: question.questionId,
        stagingKeys: stagingKeys,
      );

      state = const PracticeUploadState.submitted();

      // Invalidate attempts list
      ref.invalidate(questionAttemptsProvider);

      return response.id;
    } catch (e) {
      // Reset state on error so user can retry
      state = const PracticeUploadState.initial();
      rethrow;
    }
  }
}
