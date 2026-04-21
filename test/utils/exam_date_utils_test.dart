import 'package:flutter_test/flutter_test.dart';
import 'package:paperlab/utils/exam_date_utils.dart';

void main() {
  group('formatExamDate', () {
    test('formats valid month 1 (January) correctly', () {
      expect(formatExamDate(2023, 1), equals('Jan 2023'));
    });

    test('formats valid month 6 (June) correctly', () {
      expect(formatExamDate(2023, 6), equals('Jun 2023'));
    });

    test('formats valid month 12 (December) correctly', () {
      expect(formatExamDate(2023, 12), equals('Dec 2023'));
    });

    test('throws RangeError for month 0', () {
      expect(
        () => formatExamDate(2023, 0),
        throwsA(isA<RangeError>()),
      );
    });

    test('throws RangeError for month 13', () {
      expect(
        () => formatExamDate(2023, 13),
        throwsA(isA<RangeError>()),
      );
    });
  });

  group('formatExamDateFromDateTime', () {
    test('formats DateTime to "MMM yyyy" format', () {
      final date = DateTime(2023, 11, 13);
      expect(formatExamDateFromDateTime(date), equals('Nov 2023'));
    });

    test('formats DateTime with single-digit month correctly', () {
      final date = DateTime(2024, 1, 5);
      expect(formatExamDateFromDateTime(date), equals('Jan 2024'));
    });
  });

  group('compareExamDatesDescending', () {
    test('sorts same year different months correctly (descending)', () {
      // Nov should come before Jun (descending = recent first)
      expect(compareExamDatesDescending('2023-06', '2023-11'), greaterThan(0));
      expect(compareExamDatesDescending('2023-11', '2023-06'), lessThan(0));
    });

    test('sorts different years correctly (descending)', () {
      // 2024 should come before 2023 (descending = recent first)
      expect(compareExamDatesDescending('2023-11', '2024-06'), greaterThan(0));
      expect(compareExamDatesDescending('2024-06', '2023-11'), lessThan(0));
    });

    test('returns 0 for equal dates', () {
      expect(compareExamDatesDescending('2023-11', '2023-11'), equals(0));
    });

    test('throws FormatException for invalid format "invalid"', () {
      expect(
        () => compareExamDatesDescending('invalid', '2023-11'),
        throwsA(isA<FormatException>()),
      );
    });

    test('throws FormatException for format missing month "2023"', () {
      expect(
        () => compareExamDatesDescending('2023', '2023-11'),
        throwsA(isA<FormatException>()),
      );
    });
  });

  group('examDateOptionsFromKeys', () {
    test('returns sorted descending options for multiple dates', () {
      final dateKeys = {'2023-06', '2023-11', '2024-01'};
      final result = examDateOptionsFromKeys(dateKeys);

      expect(result.length, equals(3));
      // Most recent first (descending)
      expect(result[0]['value'], equals('2024-01'));
      expect(result[0]['label'], equals('Jan 2024'));
      expect(result[1]['value'], equals('2023-11'));
      expect(result[1]['label'], equals('Nov 2023'));
      expect(result[2]['value'], equals('2023-06'));
      expect(result[2]['label'], equals('Jun 2023'));
    });

    test('returns empty list for empty set', () {
      final result = examDateOptionsFromKeys(<String>{});
      expect(result, isEmpty);
    });

    test('throws FormatException for invalid key format', () {
      expect(
        () => examDateOptionsFromKeys({'invalid-key'}),
        throwsA(isA<FormatException>()),
      );
    });

    test('throws RangeError for invalid month in key', () {
      expect(
        () => examDateOptionsFromKeys({'2023-13'}),
        throwsA(isA<RangeError>()),
      );
    });
  });
}
