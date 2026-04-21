/// Utilities for exam date formatting and sorting.
///
/// Handles exam date display formatting (e.g., "Nov 2023") and sorting
/// logic for date-based dropdowns in selection screens.
library;

import 'package:intl/intl.dart';

/// Month names for date formatting (1-indexed, empty string at index 0)
const _kMonthNames = [
  '', // 1-indexed
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

/// Format exam date for display (e.g., "Nov 2023")
///
/// Throws [RangeError] if month is not in range 1-12.
String formatExamDate(int year, int month) {
  if (month < 1 || month > 12) {
    throw RangeError.range(month, 1, 12, 'month');
  }
  return '${_kMonthNames[month]} $year';
}

/// Format DateTime for display (e.g., "Nov 2023")
///
/// Overload that accepts DateTime instead of year/month integers.
/// Uses intl package for localization support.
///
/// Example:
/// ```dart
/// final date = DateTime(2023, 11, 13);
/// formatExamDateFromDateTime(date); // "Nov 2023"
/// ```
String formatExamDateFromDateTime(DateTime date) =>
    DateFormat('MMM yyyy').format(date);

/// Sort exam date keys in descending order (most recent first)
///
/// Date key format: "YYYY-MM" (e.g., "2023-11")
///
/// Throws [FormatException] if date keys are not in valid "YYYY-MM" format.
int compareExamDatesDescending(String dateKeyA, String dateKeyB) {
  try {
    final aParts = dateKeyA.split('-');
    final bParts = dateKeyB.split('-');

    if (aParts.length != 2 || bParts.length != 2) {
      throw const FormatException('Invalid date format. Expected "YYYY-MM"');
    }

    final aYear = int.parse(aParts[0]);
    final bYear = int.parse(bParts[0]);
    final aMonth = int.parse(aParts[1]);
    final bMonth = int.parse(bParts[1]);

    final yearCmp = bYear.compareTo(aYear); // Recent first
    return yearCmp != 0 ? yearCmp : bMonth.compareTo(aMonth);
  } on FormatException catch (e) {
    throw FormatException(
      'Invalid date key format: ${e.message}. Expected "YYYY-MM".',
    );
  }
}

/// Convert exam dates to sorted option list for dropdowns
///
/// Returns `List<Map<String, String>>` with 'value' and 'label' keys
/// Sorted in descending order (most recent first)
///
/// Throws [FormatException] if any date key is not in valid "YYYY-MM" format.
/// Throws [RangeError] if any month value is not in range 1-12.
List<Map<String, String>> examDateOptionsFromKeys(Set<String> dateKeys) {
  try {
    return dateKeys.map((dateKey) {
      final parts = dateKey.split('-');
      if (parts.length != 2) {
        throw const FormatException('Invalid date format. Expected "YYYY-MM"');
      }
      final year = int.parse(parts[0]);
      final month = int.parse(parts[1]);
      return {'value': dateKey, 'label': formatExamDate(year, month)};
    }).toList()..sort(
      (a, b) => compareExamDatesDescending(a['value']!, b['value']!),
    );
  } on FormatException catch (e) {
    throw FormatException(
      'Invalid date key in set: ${e.message}. Expected "YYYY-MM".',
    );
  }
}
