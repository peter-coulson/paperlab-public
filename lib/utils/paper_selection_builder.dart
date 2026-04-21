/// Builds SelectionField configuration for paper selection flow.
///
/// Transforms paper metadata into cascading dropdown configuration
/// for the SelectionScreen. Handles Paper Type and optional Exam Date fields.
library;

import 'package:paperlab/models/paper_metadata.dart';
import 'package:paperlab/models/selection_field.dart';
import 'package:paperlab/theme/app_strings.dart';
import 'package:paperlab/utils/exam_date_utils.dart';

/// Build SelectionField list for paper selection.
///
/// Handles cascading dropdowns:
/// - Field 1: Paper Type (always enabled)
/// - Field 2: Exam Date (enabled only when paper type selected)
///
/// Always returns 2 fields (matches question selection pattern).
///
/// Throws [ArgumentError] if papers list is empty.
///
/// Usage:
/// ```dart
/// final fields = buildPaperSelectionFields(
///   papers: papers,
///   selectedPaperType: selections.isNotEmpty ? selections[0] : null,
/// );
/// ```
List<SelectionField> buildPaperSelectionFields({
  required List<PaperMetadata> papers,
  required String? selectedPaperType,
}) {
  if (papers.isEmpty) {
    throw ArgumentError.value(papers, 'papers', 'Cannot be empty');
  }

  // Extract unique paper types
  final paperTypes = papers.map((p) => p.paperCode).toSet().toList()..sort();

  return [
    // Field 1: Paper Type (always present)
    SelectionField(
      label: AppStrings.paperTypeLabel,
      options: paperTypes
          .map(
            (code) => {
              'value': code,
              'label': papers
                  .firstWhere((p) => p.paperCode == code)
                  .displayName,
            },
          )
          .toList(),
      placeholder: AppStrings.selectPaperType,
    ),
    // Field 2: Exam Date (always present, matches question selection pattern)
    _buildPaperExamDateField(papers, selectedPaperType),
  ];
}

/// Build Exam Date field (filtered by selected paper type)
SelectionField _buildPaperExamDateField(
  List<PaperMetadata> papers,
  String? selectedPaperType,
) {
  final List<Map<String, String>> examDates;
  final bool isDisabled;

  if (selectedPaperType != null) {
    // Filter papers by selected type
    final filteredPapers = papers
        .where((p) => p.paperCode == selectedPaperType)
        .toList();

    // Extract unique date keys
    final uniqueDateKeys = filteredPapers
        .map((p) => '${p.year}-${p.month}')
        .toSet();

    // Convert to sorted options using utility
    examDates = examDateOptionsFromKeys(uniqueDateKeys);
    isDisabled = false;
  } else {
    // No paper type selected - show placeholder with disabled state
    examDates = [];
    isDisabled = true;
  }

  return SelectionField(
    label: AppStrings.examDateLabel,
    options: examDates,
    placeholder: isDisabled
        ? AppStrings.selectPaperTypeFirst
        : AppStrings.selectExamDate,
    disabled: isDisabled,
  );
}
