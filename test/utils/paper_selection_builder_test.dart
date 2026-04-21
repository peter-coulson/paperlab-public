import 'package:flutter_test/flutter_test.dart';
import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/utils/paper_selection_builder.dart';

void main() {
  group('buildPaperSelectionFields', () {
    test('throws ArgumentError for empty papers list', () {
      expect(
        () => buildPaperSelectionFields(
          papers: [],
          selectedPaperType: null,
        ),
        throwsA(isA<ArgumentError>()),
      );
    });

    test('returns 2 fields when papers have single date', () {
      final papers = [
        const PaperMetadata(
          paperId: 1,
          examBoard: 'pearson-edexcel',
          examLevel: 'gcse',
          subject: 'mathematics',
          paperCode: '1ma1_1h',
          displayName: 'Paper 1 (Non Calculator)',
          year: 2023,
          month: 11,
          totalMarks: 80,
          questionCount: 22,
        ),
        const PaperMetadata(
          paperId: 2,
          examBoard: 'pearson-edexcel',
          examLevel: 'gcse',
          subject: 'mathematics',
          paperCode: '1ma1_2h',
          displayName: 'Paper 2 (Calculator)',
          year: 2023,
          month: 11,
          totalMarks: 80,
          questionCount: 21,
        ),
      ];

      final fields = buildPaperSelectionFields(
        papers: papers,
        selectedPaperType: null,
      );

      // Always returns 2 fields for UI consistency
      // (matches question selection pattern)
      expect(fields.length, equals(2));
      expect(fields[0].label, equals('Paper Type'));
      expect(fields[0].options.length, equals(2));
      expect(fields[1].label, equals('Exam Date'));
      // Exam date should be disabled when no paper type selected
      expect(fields[1].disabled, isTrue);
    });

    test('returns 2 fields when papers have multiple dates', () {
      final papers = [
        const PaperMetadata(
          paperId: 1,
          examBoard: 'pearson-edexcel',
          examLevel: 'gcse',
          subject: 'mathematics',
          paperCode: '1ma1_1h',
          displayName: 'Paper 1 (Non Calculator)',
          year: 2023,
          month: 11,
          totalMarks: 80,
          questionCount: 22,
        ),
        const PaperMetadata(
          paperId: 2,
          examBoard: 'pearson-edexcel',
          examLevel: 'gcse',
          subject: 'mathematics',
          paperCode: '1ma1_1h',
          displayName: 'Paper 1 (Non Calculator)',
          year: 2024,
          month: 6,
          totalMarks: 80,
          questionCount: 20,
        ),
      ];

      final fields = buildPaperSelectionFields(
        papers: papers,
        selectedPaperType: null,
      );

      // 2 fields (Paper Type + Exam Date) when multiple dates exist
      expect(fields.length, equals(2));
      expect(fields[0].label, equals('Paper Type'));
      expect(fields[1].label, equals('Exam Date'));
      // Exam date field should be disabled when no paper type selected
      expect(fields[1].disabled, isTrue);
    });

    test('exam date field is enabled when paper type selected', () {
      final papers = [
        const PaperMetadata(
          paperId: 1,
          examBoard: 'pearson-edexcel',
          examLevel: 'gcse',
          subject: 'mathematics',
          paperCode: '1ma1_1h',
          displayName: 'Paper 1 (Non Calculator)',
          year: 2023,
          month: 11,
          totalMarks: 80,
          questionCount: 22,
        ),
        const PaperMetadata(
          paperId: 2,
          examBoard: 'pearson-edexcel',
          examLevel: 'gcse',
          subject: 'mathematics',
          paperCode: '1ma1_1h',
          displayName: 'Paper 1 (Non Calculator)',
          year: 2024,
          month: 6,
          totalMarks: 80,
          questionCount: 20,
        ),
      ];

      final fields = buildPaperSelectionFields(
        papers: papers,
        selectedPaperType: '1ma1_1h',
      );

      expect(fields.length, equals(2));
      expect(fields[1].disabled, isFalse);
      expect(fields[1].options.length, equals(2));
    });
  });
}
