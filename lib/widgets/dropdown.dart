import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Dropdown component for form selection fields.
/// Matches design system specification from SHARED_COMPONENTS.md
/// (lines 306-348).
///
/// Features:
/// - Form integration via DropdownButtonFormField
/// - Consistent styling matching design system
/// - Label above dropdown (not floating)
/// - Full-width by default
///
/// States:
/// - Default: Border color (neutral)
/// - Focus: Primary border color
/// - Disabled: Gray background, tertiary text
class AppDropdown<T> extends StatelessWidget {
  const AppDropdown({
    required this.label,
    required this.options,
    required this.onChanged,
    this.selectedValue,
    this.placeholder = 'Select...',
    this.disabled = false,
    super.key,
  });

  /// Label shown above dropdown
  final String label;

  /// List of options: [{value: T, label: String}]
  final List<Map<String, dynamic>> options;

  /// Currently selected value
  final T? selectedValue;

  /// Placeholder text when nothing selected
  final String placeholder;

  /// Whether dropdown is disabled
  final bool disabled;

  /// Callback when selection changes
  final void Function(T?) onChanged;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      // Label above dropdown (uppercase per design system)
      AppTypography.sectionTitle(
        label,
        color: disabled ? AppColors.textTertiary : AppColors.textPrimary,
      ),
      const SizedBox(height: AppSpacing.sm),

      // Dropdown field
      DropdownButtonFormField<T>(
        initialValue: selectedValue,
        decoration: InputDecoration(
          // Border styling
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
            borderSide: const BorderSide(
              color: AppColors.border,
              width: AppEffects.borderWidth,
              strokeAlign: AppEffects.strokeAlignInside,
            ),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
            borderSide: const BorderSide(
              color: AppColors.primary,
              width: AppEffects.borderWidth,
              strokeAlign: AppEffects.strokeAlignInside,
            ),
          ),
          disabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
            borderSide: BorderSide(
              color: AppColors.border.withValues(alpha: 0.5),
              width: AppEffects.borderWidth,
              strokeAlign: AppEffects.strokeAlignInside,
            ),
          ),

          // Remove default padding/content padding
          contentPadding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.md,
            vertical: 12,
          ),

          // Background color
          filled: true,
          fillColor: disabled
              ? AppColors.backgroundSecondary
              : AppColors.background,

          // No helper/error text space (keeps height consistent)
          isDense: false,
        ),

        // Dropdown styling
        style: AppTypography.body.copyWith(
          color: disabled ? AppColors.textTertiary : AppColors.textPrimary,
        ),

        // Icon styling
        icon: Icon(
          LucideIcons.chevron_down,
          color: disabled ? AppColors.textTertiary : AppColors.textSecondary,
          size: 20,
        ),

        // Dropdown menu background
        dropdownColor: AppColors.background,

        // Items
        items: options
            .map(
              (option) => DropdownMenuItem<T>(
                value: option['value'] as T,
                child: Text(
                  option['label'] as String,
                  style: AppTypography.body.copyWith(
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
            )
            .toList(),

        // Hint (shown when no selection)
        hint: Text(
          placeholder,
          style: AppTypography.body.copyWith(color: AppColors.textTertiary),
        ),

        // Callbacks
        onChanged: disabled ? null : onChanged,

        // No underline (we're using border via InputDecoration)
        isExpanded: true,
      ),
    ],
  );
}
