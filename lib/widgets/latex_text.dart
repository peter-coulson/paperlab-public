import 'package:flutter/material.dart';
import 'package:flutter_math_fork/flutter_math.dart';

/// Parses and renders text containing LaTeX and markdown formatting.
///
/// Supports:
/// - Inline math: $...$ (e.g., "Write $468000$ in standard form")
/// - Display math: $$...$$ (e.g., "$$x^2 + y^2 = z^2$$")
/// - Bold text: **...** (e.g., "This is **bold** text")
/// - Italic text: *...* (e.g., "This is *italic* text")
///
/// Implementation:
/// - Uses regex to find LaTeX delimiters and markdown syntax
/// - Splits text into plain text, formatted text, and math segments
/// - Renders using Text.rich with TextSpan and WidgetSpan
/// - Math.tex widgets embedded via WidgetSpan
/// - Markdown formatting applied via TextStyle
///
/// Usage:
/// ```dart
/// LatexText(
///   'The formula is $E = mc^2$ where c is the speed of light **or** $3 \times 10^8$ m/s.',
///   style: AppTypography.body,
/// )
/// ```
class LatexText extends StatelessWidget {
  const LatexText(this.text, {this.style, this.textAlign, super.key});

  /// Text containing LaTeX expressions and markdown formatting
  /// Examples:
  /// - "Write $468000$ in standard form."
  /// - "Correct use of formula $a + b = c$"
  /// - "Display equation: $$x^2 + y^2 = z^2$$"
  /// - "Use the quadratic formula **or** factorization"
  /// - "The *gradient* at $x = 2$ is $4$"
  final String text;

  /// Text style applied to plain text and Math widgets
  final TextStyle? style;

  /// Text alignment (default: start)
  final TextAlign? textAlign;

  @override
  Widget build(BuildContext context) {
    final spans = _parseLatex(
      text,
      style ?? DefaultTextStyle.of(context).style,
    );

    // If no LaTeX found, return simple Text widget
    if (spans.length == 1 && spans.first is TextSpan) {
      return Text(text, style: style, textAlign: textAlign);
    }

    // Mixed content: use Text.rich
    return Text.rich(TextSpan(children: spans), textAlign: textAlign);
  }

  /// Parse text and split into TextSpan and WidgetSpan segments.
  ///
  /// Algorithm:
  /// 1. Find all LaTeX ($...$ and $$...$$) and markdown (**bold**, *italic*)
  /// 2. Split text into segments
  /// 3. Create TextSpan for plain text with markdown, WidgetSpan for math
  List<InlineSpan> _parseLatex(String text, TextStyle style) {
    final spans = <InlineSpan>[];

    // Regex pattern for LaTeX delimiters and markdown
    // Matches:
    // - $$...$$ (display math)
    // - $...$ (inline math)
    // - **...** (bold)
    // - *...* (italic)
    // Non-greedy to handle multiple expressions in one string
    final combinedRegex = RegExp(
      r'\$\$(.+?)\$\$|\$(.+?)\$|\*\*(.+?)\*\*|\*(.+?)\*',
    );

    int lastIndex = 0;

    for (final match in combinedRegex.allMatches(text)) {
      // Add plain text before this match
      if (match.start > lastIndex) {
        final plainText = text.substring(lastIndex, match.start);
        spans.add(TextSpan(text: plainText, style: style));
      }

      // Determine match type and handle accordingly
      if (match.group(1) != null || match.group(2) != null) {
        // LaTeX expression
        final isDisplay = match.group(1) != null;
        final mathContent = match.group(1) ?? match.group(2)!;

        // Add math expression
        spans.add(
          WidgetSpan(
            // Baseline alignment for inline math (looks natural in text)
            // Display math uses middle alignment (centered on its own line)
            alignment: isDisplay
                ? PlaceholderAlignment.middle
                : PlaceholderAlignment.baseline,
            baseline: TextBaseline.alphabetic,
            child: Math.tex(
              mathContent,
              mathStyle: isDisplay ? MathStyle.display : MathStyle.text,
              textStyle: style,
              // Options for compatibility with surrounding text
              options: MathOptions(
                fontSize: style.fontSize ?? 16.0,
                color: style.color ?? Colors.black,
              ),
            ),
          ),
        );
      } else if (match.group(3) != null) {
        // Bold text (**text**)
        final boldText = match.group(3)!;
        spans.add(
          TextSpan(
            text: boldText,
            style: style.copyWith(fontWeight: FontWeight.bold),
          ),
        );
      } else if (match.group(4) != null) {
        // Italic text (*text*)
        final italicText = match.group(4)!;
        spans.add(
          TextSpan(
            text: italicText,
            style: style.copyWith(fontStyle: FontStyle.italic),
          ),
        );
      }

      lastIndex = match.end;
    }

    // Add remaining plain text after last match
    if (lastIndex < text.length) {
      final remainingText = text.substring(lastIndex);
      spans.add(TextSpan(text: remainingText, style: style));
    }

    // If no LaTeX or markdown found, return original text as single TextSpan
    if (spans.isEmpty) {
      spans.add(TextSpan(text: text, style: style));
    }

    return spans;
  }
}
