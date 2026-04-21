/// Configuration for a dropdown field in selection screens.
///
/// Used to configure generic SelectionScreen widget with different fields.
/// Data-driven approach per CLAUDE.md: "Expand through data, not code".
class SelectionField {
  const SelectionField({
    required this.label,
    required this.options,
    required this.placeholder,
    this.disabled = false,
  });

  /// Label shown above dropdown
  final String label;

  /// List of options: [{value: String, label: String}]
  final List<Map<String, String>> options;

  /// Placeholder text when nothing selected
  final String placeholder;

  /// Whether this field is disabled (for cascading dropdowns)
  final bool disabled;
}
