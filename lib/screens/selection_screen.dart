import 'package:flutter/material.dart';
import 'package:paperlab/models/selection_field.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/dropdown.dart';
import 'package:paperlab/widgets/primary_button.dart';
import 'package:paperlab/widgets/screen_header.dart';

/// Generic selection screen for configuring papers/questions/entities.
/// Data-driven: "Expand through data, not code" (CLAUDE.md).
///
/// Eliminates duplication between Paper/Question screens via config.
///
/// Features:
/// - ScreenHeader with title only (no buttons, uses native back)
/// - Configurable number of dropdowns
/// - Configurable field labels, options, placeholders
/// - Confirm button (enabled only when all fields selected)
/// - Consistent spacing with all other screens (via universal ScreenHeader)
///
/// Usage:
/// ```dart
/// SelectionScreen(
///   title: 'Select Paper',
///   fields: [
///     SelectionField(
///       label: 'Paper Type',
///       options: [...],
///       placeholder: '...',
///     ),
///     SelectionField(
///       label: 'Exam Session',
///       options: [...],
///       placeholder: '...',
///     ),
///   ],
///   onConfirm: (selections) {
///     // selections[0] = paper type value
///     // selections[1] = exam session value
///   },
/// )
/// ```
class SelectionScreen extends StatefulWidget {
  const SelectionScreen({
    required this.title,
    required this.fieldBuilder,
    required this.onConfirm,
    super.key,
  });

  /// Screen title (e.g., "Select Paper", "Select Question")
  final String title;

  /// Builder function that generates fields based on current selections
  /// Called each time selections change to get updated field list
  final List<SelectionField> Function(List<String?> selections) fieldBuilder;

  /// Callback when user taps Confirm
  /// Receives list of selected values (one per field, in order)
  final void Function(List<String>) onConfirm;

  @override
  State<SelectionScreen> createState() => _SelectionScreenState();
}

class _SelectionScreenState extends State<SelectionScreen> {
  // Track selected value for each field (null = not selected)
  List<String?> _selections = [];

  @override
  void initState() {
    super.initState();
    // Build initial fields to determine count
    final initialFields = widget.fieldBuilder([]);
    _selections = List.filled(initialFields.length, null);
  }

  /// Check if all required fields are selected (and not disabled)
  bool get _isFormValid {
    final fields = widget.fieldBuilder(_selections);
    for (int i = 0; i < _selections.length; i++) {
      // Skip validation for disabled fields
      if (i < fields.length && fields[i].disabled) continue;
      // All non-disabled fields must have a selection
      if (_selections[i] == null) return false;
    }
    return true;
  }

  @override
  Widget build(BuildContext context) {
    // Build fields based on current selections
    final fields = widget.fieldBuilder(_selections);

    // Adjust selections array if field count changed
    if (_selections.length != fields.length) {
      _selections = List.filled(fields.length, null);
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Universal header (no buttons - relies on native back)
            ScreenHeader(title: widget.title),

            // Scrollable content
            Expanded(
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.lg,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Generate dropdowns from field configuration
                      for (int i = 0; i < fields.length; i++) ...[
                        AppDropdown<String>(
                          label: fields[i].label,
                          options: fields[i].options,
                          selectedValue: _selections[i],
                          placeholder: fields[i].placeholder,
                          disabled: fields[i].disabled,
                          onChanged: (value) {
                            setState(() {
                              _selections[i] = value;
                              // Clear subsequent field selections when a field
                              // changes (for cascading dropdowns)
                              for (int j = i + 1; j < _selections.length; j++) {
                                _selections[j] = null;
                              }
                            });
                          },
                        ),
                        if (i < fields.length - 1)
                          const SizedBox(height: AppSpacing.lg),
                      ],

                      const SizedBox(height: AppSpacing.xl),

                      // Confirm button (enabled only when form valid)
                      PrimaryButton(
                        text: 'Confirm',
                        onTap: _isFormValid ? _handleConfirm : null,
                        requiresNetwork: true,
                        disabled: !_isFormValid,
                      ),

                      const SizedBox(height: AppSpacing.lg),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handleConfirm() {
    // Extract non-null values (we know all are non-null because form is valid)
    final selectedValues = _selections.cast<String>();
    widget.onConfirm(selectedValues);
  }
}
