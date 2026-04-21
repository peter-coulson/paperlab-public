/// Content block within a question part or mark criterion.
/// Can be either text (with optional LaTeX) or a diagram reference.
///
/// Corresponds to SQL tables:
/// - question_content_blocks
/// - mark_criteria_content_blocks
///
/// Examples:
/// - Text: "Write $468000$ in standard form."
/// - Diagram: "A triangle with vertices labeled A, B, and C"
class ContentBlock {
  const ContentBlock({
    required this.blockType,
    this.text,
    this.diagramDescription,
    this.diagramImagePath,
  }) : assert(
         (blockType == 'text' && text != null && diagramDescription == null) ||
             (blockType == 'diagram' &&
                 text == null &&
                 diagramDescription != null),
         'Text blocks must have text, '
         'diagram blocks must have diagramDescription',
       );

  factory ContentBlock.fromJson(Map<String, dynamic> json) => ContentBlock(
    blockType: json['block_type'] as String,
    text: json['text'] as String?,
    diagramDescription: json['diagram_description'] as String?,
    diagramImagePath: json['diagram_image_path'] as String?,
  );

  /// Block type: 'text' or 'diagram'
  final String blockType;

  /// Text content (may contain LaTeX expressions like $468000$ or $$x^2$$)
  /// Only populated for text blocks
  final String? text;

  /// Diagram description (for screen readers and fallback display)
  /// Only populated for diagram blocks
  final String? diagramDescription;

  /// Diagram image path (for M5 mock data: asset path, for M6: presigned URL)
  /// Optional for diagram blocks (if null, show description only)
  final String? diagramImagePath;

  /// Convenience getter for type checking
  bool get isText => blockType == 'text';

  /// Convenience getter for type checking
  bool get isDiagram => blockType == 'diagram';
}
