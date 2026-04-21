/// String utility functions for text formatting.
library;

/// Capitalize first character if it's a lowercase letter.
///
/// Examples:
/// - "hello world" → "Hello world"
/// - "Hello world" → "Hello world" (unchanged)
/// - "123 test" → "123 test" (unchanged, doesn't start with letter)
/// - "" → "" (empty string unchanged)
String capitalizeFirst(String text) {
  if (text.isEmpty) return text;
  final firstChar = text[0];
  if (RegExp(r'[a-z]').hasMatch(firstChar)) {
    return firstChar.toUpperCase() + text.substring(1);
  }
  return text;
}

/// Extract paper type from full paper name.
///
/// Removes parenthetical qualifiers like "(Calculator)" or "(Non Calculator)"
/// and returns just the paper type (e.g., "Paper 3").
///
/// Returns original string if pattern doesn't match.
///
/// Examples:
/// - "Paper 3 (Calculator)" → "Paper 3"
/// - "Paper 2 (Non Calculator)" → "Paper 2"
/// - "Paper 1H" → "Paper 1H" (no match, returned as-is)
String extractPaperType(String paperName) {
  final match = RegExp(r'^(Paper \d+)').firstMatch(paperName);
  return match?.group(1) ?? paperName;
}
