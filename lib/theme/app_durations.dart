/// Duration constants for PaperLab mobile app.
///
/// Centralized timing values for animations, toasts, and interactions.
class AppDurations {
  // Private constructor to prevent instantiation
  AppDurations._();

  /// Toast duration for undo actions - 5 seconds
  /// Long enough to read and act on the undo option
  static const Duration undoToast = Duration(seconds: 5);

  /// Standard toast duration - 3 seconds
  /// For simple confirmation messages
  static const Duration standardToast = Duration(seconds: 3);

  /// Error toast duration - 4 seconds
  /// Slightly longer for error messages that may need reading
  static const Duration errorToast = Duration(seconds: 4);
}
