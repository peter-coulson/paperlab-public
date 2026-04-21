/// State enum for practice question attempts.
/// Derived from JOIN query to marking_attempts table.
/// See specs/STATE-LOGIC.md for complete state derivation logic.
enum QuestionAttemptState {
  /// Marking in progress OR marking failed
  marking,

  /// Marking succeeded, results available
  complete,
}
