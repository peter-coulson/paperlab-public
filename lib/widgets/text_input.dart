import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Text input component for form fields.
/// Matches design system specification from SHARED_COMPONENTS.md
/// (lines 351-410).
///
/// Features:
/// - Consistent styling matching AppDropdown pattern
/// - Label above field (not floating)
/// - Three variants: text, email, password
/// - Error state support
/// - Autofill hints for system autofill
/// - TextInputAction support for keyboard submit
///
/// States:
/// - Default: Border color (neutral)
/// - Focus: Primary border color
/// - Error: Error border color, error text below
/// - Disabled: Gray background, tertiary text
///
/// Variants:
/// - text: Standard text input
/// - email: Email keyboard, no autocorrect, autofill support
/// - password: Obscured text, autofill support
class AppTextInput extends StatelessWidget {
  const AppTextInput({
    required this.label,
    required this.controller,
    this.type = AppTextInputType.text,
    this.placeholder,
    this.errorText,
    this.disabled = false,
    this.textInputAction,
    this.onSubmitted,
    this.autofocus = false,
    this.fieldKey,
    super.key,
  });

  /// Label shown above input field
  final String label;

  /// Text editing controller
  final TextEditingController controller;

  /// Input type (text, email, password)
  final AppTextInputType type;

  /// Placeholder text when field is empty
  final String? placeholder;

  /// Error message shown below field
  final String? errorText;

  /// Whether input is disabled
  final bool disabled;

  /// Keyboard action button (next, done, etc.)
  final TextInputAction? textInputAction;

  /// Callback when user submits via keyboard
  final void Function(String)? onSubmitted;

  /// Whether to autofocus this field
  final bool autofocus;

  /// Key for the internal TextField (for flutter_driver targeting).
  ///
  /// Use `ValueKey<String>` for driver automation, e.g.:
  /// `fieldKey: const ValueKey('email_field')`
  final Key? fieldKey;

  @override
  Widget build(BuildContext context) {
    final bool hasError = errorText != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Label above input (uppercase per design system)
        AppTypography.sectionTitle(
          label,
          color: disabled ? AppColors.textTertiary : AppColors.textPrimary,
        ),
        const SizedBox(height: AppSpacing.sm),

        // Text input field
        TextField(
          key: fieldKey,
          controller: controller,
          enabled: !disabled,
          autofocus: autofocus,

          // Input type configuration
          keyboardType: _getKeyboardType(),
          autocorrect: type != AppTextInputType.email,
          obscureText: type == AppTextInputType.password,
          textInputAction: textInputAction,
          onSubmitted: onSubmitted,

          // Autofill hints for system autofill
          autofillHints: _getAutofillHints(),

          // Styling
          style: AppTypography.body.copyWith(
            color: disabled ? AppColors.textTertiary : AppColors.textPrimary,
          ),

          // Decoration
          decoration: InputDecoration(
            // Border styling
            enabledBorder: _buildBorder(
              hasError ? AppColors.error : AppColors.border,
            ),
            focusedBorder: _buildBorder(
              hasError ? AppColors.error : AppColors.primary,
            ),
            disabledBorder: _buildBorder(
              AppColors.border.withValues(alpha: 0.5),
            ),
            errorBorder: _buildBorder(AppColors.error),
            focusedErrorBorder: _buildBorder(AppColors.error),

            // Padding
            contentPadding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: 12,
            ),

            // Background color
            filled: true,
            fillColor: disabled
                ? AppColors.backgroundSecondary
                : AppColors.background,

            // Placeholder text
            hintText: placeholder,
            hintStyle: AppTypography.body.copyWith(
              color: AppColors.textTertiary,
            ),

            // Error text (shown below field)
            errorText: errorText,
            errorStyle: AppTypography.bodySmall.copyWith(
              color: AppColors.error,
            ),

            // Remove default helper text space when no error
            helperText: hasError ? null : '',
            helperStyle: const TextStyle(height: 0),

            // Compact layout
            isDense: false,
          ),
        ),
      ],
    );
  }

  /// Get keyboard type based on input type
  TextInputType _getKeyboardType() {
    switch (type) {
      case AppTextInputType.email:
        return TextInputType.emailAddress;
      case AppTextInputType.text:
      case AppTextInputType.password:
        return TextInputType.text;
    }
  }

  /// Get autofill hints for system autofill
  List<String>? _getAutofillHints() {
    switch (type) {
      case AppTextInputType.email:
        return [AutofillHints.email];
      case AppTextInputType.password:
        return [AutofillHints.password];
      case AppTextInputType.text:
        return null;
    }
  }

  /// Build border configuration for input decoration
  OutlineInputBorder _buildBorder(Color color) => OutlineInputBorder(
    borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
    borderSide: BorderSide(
      color: color,
      width: AppEffects.borderWidth,
      strokeAlign: AppEffects.strokeAlignInside,
    ),
  );
}

/// Input type variants for AppTextInput
enum AppTextInputType {
  /// Standard text input
  text,

  /// Email input (email keyboard, no autocorrect, autofill)
  email,

  /// Password input (obscured text, autofill)
  password,
}
