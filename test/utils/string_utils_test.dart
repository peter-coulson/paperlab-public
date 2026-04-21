import 'package:flutter_test/flutter_test.dart';
import 'package:paperlab/utils/string_utils.dart';

void main() {
  group('capitalizeFirst', () {
    test('capitalizes lowercase first letter', () {
      expect(capitalizeFirst('hello world'), equals('Hello world'));
    });

    test('leaves uppercase first letter unchanged', () {
      expect(capitalizeFirst('Hello world'), equals('Hello world'));
    });

    test('returns empty string unchanged', () {
      expect(capitalizeFirst(''), equals(''));
    });

    test('leaves number start unchanged', () {
      expect(capitalizeFirst('123 test'), equals('123 test'));
    });

    test('leaves special character start unchanged', () {
      expect(capitalizeFirst('!hello'), equals('!hello'));
    });
  });

  group('extractPaperType', () {
    test('extracts "Paper 3" from "Paper 3 (Calculator)"', () {
      expect(extractPaperType('Paper 3 (Calculator)'), equals('Paper 3'));
    });

    test('extracts "Paper 2" from "Paper 2 (Non Calculator)"', () {
      expect(extractPaperType('Paper 2 (Non Calculator)'), equals('Paper 2'));
    });

    test('extracts "Paper 1" from "Paper 1 (Non Calculator)"', () {
      expect(extractPaperType('Paper 1 (Non Calculator)'), equals('Paper 1'));
    });

    test('extracts "Paper 1" from "Paper 1H" (suffix ignored)', () {
      // Regex ^(Paper \d+) matches "Paper 1" in "Paper 1H"
      expect(extractPaperType('Paper 1H'), equals('Paper 1'));
    });

    test('returns original string for non-paper format', () {
      expect(extractPaperType('Unit 1'), equals('Unit 1'));
    });
  });
}
