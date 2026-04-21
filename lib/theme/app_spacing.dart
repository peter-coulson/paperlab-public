/// Spacing system for PaperLab mobile app.
///
/// Based on design system specification:
/// context/frontend/DESIGN_SYSTEM.md
///
/// 4px base increment spacing scale.
class AppSpacing {
  // Private constructor to prevent instantiation
  AppSpacing._();

  /// Extra small - 4px - Tight spacing within components
  static const double xs = 4;

  /// Small - 8px - Related elements
  static const double sm = 8;

  /// Medium - 16px - Default spacing between elements
  static const double md = 16;

  /// Large - 24px - Sections within a screen
  static const double lg = 24;

  /// Extra large - 32px - Major sections
  static const double xl = 32;

  /// Layout extra large - 40px - Hero element spacing
  /// (optically balanced for large typography)
  static const double layoutXl = 40;

  /// Extra extra large - 48px - Screen padding
  static const double xxl = 48;

  // Layout standards
  /// Standard horizontal screen margin - 24px
  /// This is the consistent left/right edge margin used throughout the app.
  /// Use this for:
  /// - ScreenHeader horizontal padding
  /// - ListView/ScrollView content padding
  /// - Screen-level content wrappers
  /// - Any content that should align to the standard vertical grid
  static const double screenHorizontalMargin = lg;

  // Border radius constants
  /// Standard border radius - 8px - Used for buttons, cards, inputs,
  /// and all rounded UI elements
  static const double borderRadius = 8;

  /// Diagram border radius - 12px - Used for diagram images and
  /// placeholders (slightly larger for image content)
  static const double diagramBorderRadius = 12;

  // Component-specific spacing
  /// Button vertical padding - 12px - Used to achieve 48dp touch target
  /// Calculation: 12px (top) + 24px (line-height) + 12px (bottom) = 48px
  static const double buttonVerticalPadding = 12;

  /// Diagram placeholder height - 200px - Default height for diagram
  /// error placeholders when image fails to load
  static const double diagramPlaceholderHeight = 200;

  // Icon sizes
  /// Small icon size - 24px - Used for standard UI icons
  static const double iconSizeSmall = 24;

  /// Large icon size - 48px - Used for placeholder/error state icons
  static const double iconSizeLarge = 48;

  /// Error icon size - 64px - Used for error state icons on full screens
  static const double iconSizeError = 64;

  // Visual accent elements
  /// Accent strip width - 4px - Used for colored vertical strips on cards
  /// (e.g., mark criterion cards)
  static const double accentStripWidth = 4;

  /// Divider thickness - 1.5px - Used for emphasized dividers
  /// (e.g., separating mark scheme from feedback)
  static const double dividerThickness = 1.5;
}
