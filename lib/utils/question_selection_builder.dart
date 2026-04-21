/// Builds SelectionField configuration for question selection flow.
///
/// Transforms question metadata into cascading dropdown configuration
/// for the SelectionScreen. Handles Paper Type, Exam Date, and Question fields.
library;

import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/models/question_metadata.dart';
import 'package:paperlab/models/selection_field.dart';
import 'package:paperlab/theme/app_strings.dart';
import 'package:paperlab/utils/exam_date_utils.dart';

/// Build SelectionField list for question selection.
///
/// Handles cascading dropdowns:
/// - Field 1: Paper Type (always enabled)
/// - Field 2: Exam Date (enabled when paper type selected)
/// - Field 3: Question (enabled when both paper type and exam date selected)
///
/// Always returns 3 fields (Paper Type, Exam Date, Question).
/// Fields 2-3 may be disabled based on prior selections.
///
/// Throws [ArgumentError] if questions or papers list is empty.
///
/// Usage:
/// ```dart
/// final fields = buildQuestionSelectionFields(
///   questions: questions,
///   papers: papers,
///   selectedPaperDisplayName: selections.isNotEmpty ? selections[0] : null,
///   selectedExamDate: selections.length > 1 ? selections[1] : null,
/// );
/// ```
List<SelectionField> buildQuestionSelectionFields({
  required List<QuestionMetadata> questions,
  required List<PaperMetadata> papers,
  required String? selectedPaperDisplayName,
  required String? selectedExamDate,
}) {
  if (questions.isEmpty) {
    throw ArgumentError.value(questions, 'questions', 'Cannot be empty');
  }
  if (papers.isEmpty) {
    throw ArgumentError.value(papers, 'papers', 'Cannot be empty');
  }

  // Build paper map for efficient lookup
  final paperMap = _buildQuestionPaperMap(papers);

  return [
    _buildQuestionPaperTypeField(questions),
    _buildQuestionExamDateField(questions, paperMap, selectedPaperDisplayName),
    _buildQuestionFieldFromFilters(
      questions,
      paperMap,
      selectedPaperDisplayName,
      selectedExamDate,
    ),
  ];
}

/// Build paper map (paper_id → PaperMetadata) for efficient lookup
Map<int, PaperMetadata> _buildQuestionPaperMap(List<PaperMetadata> papers) {
  final paperMap = <int, PaperMetadata>{};
  for (final paper in papers) {
    paperMap[paper.paperId] = paper;
  }
  return paperMap;
}

/// Field 1: Paper Type (using full display name)
SelectionField _buildQuestionPaperTypeField(List<QuestionMetadata> questions) {
  final paperDisplayNames = questions.map((q) => q.paperName).toSet().toList()
    ..sort();

  return SelectionField(
    label: AppStrings.paperTypeLabel,
    options: paperDisplayNames
        .map((name) => <String, String>{'value': name, 'label': name})
        .toList(),
    placeholder: AppStrings.selectPaperType,
  );
}

/// Field 2: Exam Date (filtered by paper display name)
SelectionField _buildQuestionExamDateField(
  List<QuestionMetadata> questions,
  Map<int, PaperMetadata> paperMap,
  String? selectedPaperDisplayName,
) {
  final List<Map<String, String>> examDates;
  final bool examDateDisabled;

  if (selectedPaperDisplayName != null) {
    // Filter questions by paper display name
    final questionsForType = questions
        .where((q) => q.paperName == selectedPaperDisplayName)
        .toList();

    // Extract unique exam dates directly from questions
    final examDateSet = <String>{};
    for (final q in questionsForType) {
      // Format: YYYY-MM from DateTime
      final year = q.examDate.year;
      final month = q.examDate.month.toString().padLeft(2, '0');
      examDateSet.add('$year-$month');
    }

    // Convert to sorted options using utility
    examDates = examDateOptionsFromKeys(examDateSet);
    examDateDisabled = false;
  } else {
    examDates = [];
    examDateDisabled = true;
  }

  return SelectionField(
    label: AppStrings.examDateLabel,
    options: examDates,
    placeholder: examDateDisabled
        ? AppStrings.selectPaperTypeFirst
        : AppStrings.selectExamDate,
    disabled: examDateDisabled,
  );
}

/// Field 3: Question (filtered by paper display name AND exam date)
SelectionField _buildQuestionFieldFromFilters(
  List<QuestionMetadata> questions,
  Map<int, PaperMetadata> paperMap,
  String? selectedPaperDisplayName,
  String? selectedExamDate,
) {
  List<Map<String, String>> questionOptions;
  bool questionDisabled;

  if (selectedPaperDisplayName != null && selectedExamDate != null) {
    try {
      final examDateParts = selectedExamDate.split('-');
      if (examDateParts.length != 2) {
        throw const FormatException('Invalid date format. Expected "YYYY-MM"');
      }

      final selectedYear = int.parse(examDateParts[0]);
      final selectedMonth = int.parse(examDateParts[1]);

      // Filter questions by both paper display name and exam date
      final filteredQuestions = questions.where((q) {
        if (q.paperName != selectedPaperDisplayName) return false;

        // Match exam date directly from question
        return q.examDate.year == selectedYear &&
            q.examDate.month == selectedMonth;
      }).toList()..sort((a, b) => a.questionNumber.compareTo(b.questionNumber));

      questionOptions = filteredQuestions
          .map(
            (q) => {
              'value': q.questionId.toString(),
              'label': 'Q${q.questionNumber} (${q.totalMarks}m)',
            },
          )
          .toList();

      questionDisabled = false;
    } on FormatException {
      // Invalid date format - show disabled field with error placeholder
      questionOptions = [];
      questionDisabled = true;
    }
  } else {
    questionOptions = [];
    questionDisabled = true;
  }

  return SelectionField(
    label: AppStrings.questionLabel,
    options: questionOptions,
    placeholder: questionDisabled
        ? AppStrings.selectPaperTypeAndExamDateFirst
        : AppStrings.selectQuestion,
    disabled: questionDisabled,
  );
}
