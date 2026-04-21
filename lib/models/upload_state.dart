import 'package:freezed_annotation/freezed_annotation.dart';

part 'upload_state.freezed.dart';

/// Exception thrown when R2 upload fails.
class UploadException implements Exception {
  const UploadException(this.message);
  final String message;

  @override
  String toString() => 'UploadException: $message';
}

/// Paper upload flow state (multi-step: draft → upload questions → submit).
@freezed
class PaperUploadState with _$PaperUploadState {
  const factory PaperUploadState.initial() = PaperUploadStateInitial;
  const factory PaperUploadState.creating() = PaperUploadStateCreating;
  const factory PaperUploadState.draft({
    required int attemptId,
    required String attemptUuid,
    required String paperName,
    required DateTime examDate,
    required int questionCount,
    required Map<int, int> submittedQuestions, // questionNumber → imageCount
  }) = PaperUploadStateDraft;
  const factory PaperUploadState.submitting() = PaperUploadStateSubmitting;
  const factory PaperUploadState.submitted() = PaperUploadStateSubmitted;
}

/// Extension to add copyWith for draft state.
extension PaperUploadStateDraftExt on PaperUploadStateDraft {
  PaperUploadStateDraft copyWith({
    int? attemptId,
    String? attemptUuid,
    String? paperName,
    DateTime? examDate,
    int? questionCount,
    Map<int, int>? submittedQuestions,
  }) => PaperUploadStateDraft(
    attemptId: attemptId ?? this.attemptId,
    attemptUuid: attemptUuid ?? this.attemptUuid,
    paperName: paperName ?? this.paperName,
    examDate: examDate ?? this.examDate,
    questionCount: questionCount ?? this.questionCount,
    submittedQuestions: submittedQuestions ?? this.submittedQuestions,
  );
}

/// Practice upload flow state (single-step: upload → submit → mark).
@freezed
class PracticeUploadState with _$PracticeUploadState {
  const factory PracticeUploadState.initial() = PracticeUploadStateInitial;
  const factory PracticeUploadState.uploading() = PracticeUploadStateUploading;
  const factory PracticeUploadState.submitting() =
      PracticeUploadStateSubmitting;
  const factory PracticeUploadState.submitted() = PracticeUploadStateSubmitted;
}
