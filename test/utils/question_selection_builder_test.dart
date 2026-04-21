import 'package:flutter_test/flutter_test.dart';
import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/models/question_metadata.dart';
import 'package:paperlab/utils/question_selection_builder.dart';

void main() {
  group('buildQuestionSelectionFields', () {
    final mockPapers = [
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
    ];

    final mockQuestions = [
      QuestionMetadata(
        questionId: 1,
        paperId: 1,
        paperName: 'Paper 1 (Non Calculator)',
        examDate: DateTime(2023, 11, 8),
        questionNumber: 1,
        totalMarks: 3,
      ),
      QuestionMetadata(
        questionId: 2,
        paperId: 1,
        paperName: 'Paper 1 (Non Calculator)',
        examDate: DateTime(2023, 11, 8),
        questionNumber: 2,
        totalMarks: 5,
      ),
    ];

    test('throws ArgumentError for empty questions list', () {
      expect(
        () => buildQuestionSelectionFields(
          questions: [],
          papers: mockPapers,
          selectedPaperDisplayName: null,
          selectedExamDate: null,
        ),
        throwsA(isA<ArgumentError>()),
      );
    });

    test('throws ArgumentError for empty papers list', () {
      expect(
        () => buildQuestionSelectionFields(
          questions: mockQuestions,
          papers: [],
          selectedPaperDisplayName: null,
          selectedExamDate: null,
        ),
        throwsA(isA<ArgumentError>()),
      );
    });

    test('returns 3 fields (Paper Type, Exam Date, Question)', () {
      final fields = buildQuestionSelectionFields(
        questions: mockQuestions,
        papers: mockPapers,
        selectedPaperDisplayName: null,
        selectedExamDate: null,
      );

      expect(fields.length, equals(3));
      expect(fields[0].label, equals('Paper Type'));
      expect(fields[1].label, equals('Exam Date'));
      expect(fields[2].label, equals('Question'));
    });

    test('exam date and question fields disabled when no selection', () {
      final fields = buildQuestionSelectionFields(
        questions: mockQuestions,
        papers: mockPapers,
        selectedPaperDisplayName: null,
        selectedExamDate: null,
      );

      expect(fields[0].disabled, isFalse); // Paper Type enabled
      expect(fields[1].disabled, isTrue); // Exam Date disabled
      expect(fields[2].disabled, isTrue); // Question disabled
    });

    test('exam date enabled when paper type selected', () {
      final fields = buildQuestionSelectionFields(
        questions: mockQuestions,
        papers: mockPapers,
        selectedPaperDisplayName: 'Paper 1 (Non Calculator)',
        selectedExamDate: null,
      );

      expect(fields[1].disabled, isFalse); // Exam Date enabled
      expect(fields[2].disabled, isTrue); // Question still disabled
    });

    test('question field enabled when both paper and date selected', () {
      final fields = buildQuestionSelectionFields(
        questions: mockQuestions,
        papers: mockPapers,
        selectedPaperDisplayName: 'Paper 1 (Non Calculator)',
        selectedExamDate: '2023-11',
      );

      expect(fields[2].disabled, isFalse); // Question enabled
      expect(fields[2].options.length, equals(2)); // 2 questions
      expect(fields[2].options[0]['label'], equals('Q1 (3m)'));
      expect(fields[2].options[1]['label'], equals('Q2 (5m)'));
    });
  });
}
