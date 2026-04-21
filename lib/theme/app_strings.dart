/// UI text constants for PaperLab mobile app.
///
/// Centralized strings for user-facing messages.
/// Prevents duplication and makes text updates easier.
class AppStrings {
  // Private constructor to prevent instantiation
  AppStrings._();

  // Home Screen - Delete/Restore Messages
  /// Message shown when a paper is deleted
  static const String paperDeleted = 'Paper deleted';

  /// Message shown when a question is deleted
  static const String questionDeleted = 'Question deleted';

  /// Prefix for delete error messages
  static const String failedToDelete = 'Failed to delete';

  /// Prefix for restore error messages
  static const String failedToRestore = 'Failed to restore';

  /// Prefix for load error messages
  static const String failedToLoad = 'Failed to load';

  /// Prefix for refresh error messages
  static const String failedToRefresh = 'Failed to refresh';

  /// Label for undo action
  static const String undo = 'Undo';

  /// Label for retry action
  static const String retry = 'Retry';

  // Home Screen - Tab Labels
  /// Label for papers tab
  static const String papers = 'papers';

  /// Label for questions tab
  static const String questions = 'questions';

  // Selection Screen - Field Labels
  /// Label for paper type dropdown
  static const String paperTypeLabel = 'Paper Type';

  /// Label for exam date dropdown
  static const String examDateLabel = 'Exam Date';

  /// Label for question dropdown
  static const String questionLabel = 'Question';

  // Selection Screen - Placeholders
  /// Placeholder for paper type dropdown
  static const String selectPaperType = 'Select paper type';

  /// Placeholder for exam date dropdown
  static const String selectExamDate = 'Select exam date';

  /// Placeholder for question dropdown
  static const String selectQuestion = 'Select question';

  /// Placeholder when paper type must be selected first
  static const String selectPaperTypeFirst = 'Select paper type first';

  /// Placeholder when paper type and exam date must be selected first
  static const String selectPaperTypeAndExamDateFirst =
      'Select paper type and exam date first';

  // Selection Screen - Titles
  /// Title for paper selection screen
  static const String titleSelectPaper = 'Select Paper';

  /// Title for question selection screen
  static const String titleSelectQuestion = 'Select Question';

  // Error Messages
  /// Error message when papers fail to load
  static const String failedToLoadPapers = 'Failed to load papers';

  /// Error message when questions fail to load
  static const String failedToLoadQuestions = 'Failed to load questions';

  /// Label for go back button
  static const String goBack = 'Go Back';
}
