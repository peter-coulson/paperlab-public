/// State enum for paper attempts.
/// Derived from timestamps: submitted_at and completed_at.
/// See specs/STATE-LOGIC.md for complete state derivation logic.
enum PaperAttemptState {
  /// submitted_at IS NULL - Can modify photos
  draft,

  /// submitted_at NOT NULL, completed_at IS NULL - Photos locked, marking in progress/failed
  marking,

  /// completed_at NOT NULL - Everything immutable
  complete,
}
