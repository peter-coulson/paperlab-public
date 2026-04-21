import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Generic dialog component for confirmations and alerts.
/// See specs/SHARED_COMPONENTS.md (lines 413-494) for complete specification.
///
/// Features:
/// - Single or two-button layouts
/// - Optional message body
/// - Three button styles: primary, secondary, destructive
/// - Modal overlay (requires button press, no tap-outside dismiss)
///
/// Usage:
/// ```dart
/// // Two-button confirmation
/// final result = await showAppDialog(
///   context: context,
///   title: 'Save to drafts?',
///   buttons: [
///     DialogButton(
///       text: 'Yes',
///       style: DialogButtonStyle.primary,
///       onTap: () => Navigator.pop(context, true),
///     ),
///     DialogButton(
///       text: 'No',
///       style: DialogButtonStyle.secondary,
///       onTap: () => Navigator.pop(context, false),
///     ),
///   ],
/// );
///
/// // Single-button alert
/// await showAppDialog(
///   context: context,
///   title: 'Email/Password incorrect',
///   buttons: [
///     DialogButton(
///       text: 'OK',
///       style: DialogButtonStyle.primary,
///       onTap: () => Navigator.pop(context),
///     ),
///   ],
/// );
/// ```
class AppDialog extends StatelessWidget {
  const AppDialog({
    required this.title,
    required this.buttons,
    this.message,
    super.key,
  });

  /// Dialog title (e.g., "Save to drafts?", "Delete completed paper?")
  final String title;

  /// Optional body text (explanation/warning)
  final String? message;

  /// Button configurations (1-2 buttons)
  final List<DialogButton> buttons;

  @override
  Widget build(BuildContext context) => AlertDialog(
    backgroundColor: AppColors.background,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    contentPadding: const EdgeInsets.all(AppSpacing.lg),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Title
        Text(
          title,
          style: AppTypography.h2.copyWith(color: AppColors.textPrimary),
          textAlign: TextAlign.center,
        ),

        // Optional message
        if (message != null) ...[
          const SizedBox(height: AppSpacing.md),
          Text(
            message!,
            style: AppTypography.body.copyWith(color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
        ],

        const SizedBox(height: AppSpacing.lg),

        // Button layout (horizontal for 2 buttons, right-aligned for 1)
        if (buttons.length == 2)
          _buildTwoButtonLayout()
        else
          _buildSingleButtonLayout(),
      ],
    ),
  );

  Widget _buildTwoButtonLayout() => Row(
    children: [
      Expanded(child: _buildButton(buttons[0])),
      const SizedBox(width: AppSpacing.md),
      Expanded(child: _buildButton(buttons[1])),
    ],
  );

  Widget _buildSingleButtonLayout() =>
      Align(alignment: Alignment.centerRight, child: _buildButton(buttons[0]));

  Widget _buildButton(DialogButton button) {
    final Color backgroundColor;
    final Color textColor;
    final Color? borderColor;

    switch (button.style) {
      case DialogButtonStyle.primary:
        backgroundColor = AppColors.primary;
        textColor = Colors.white;
        borderColor = null;
        break;
      case DialogButtonStyle.secondary:
        backgroundColor = Colors.transparent;
        textColor = AppColors.primary;
        borderColor = AppColors.border;
        break;
      case DialogButtonStyle.destructive:
        backgroundColor = AppColors.destructive;
        textColor = Colors.white;
        borderColor = null;
        break;
    }

    return TextButton(
      onPressed: button.onTap,
      style: TextButton.styleFrom(
        backgroundColor: backgroundColor,
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: 12,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
          side: borderColor != null
              ? BorderSide(color: borderColor)
              : BorderSide.none,
        ),
        minimumSize: const Size(0, 48),
      ),
      child: Text(
        button.text,
        style: AppTypography.body.copyWith(
          color: textColor,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

/// Configuration for a dialog button.
class DialogButton {
  const DialogButton({
    required this.text,
    required this.style,
    required this.onTap,
  });

  final String text;
  final DialogButtonStyle style;
  final VoidCallback onTap;
}

/// Button style variants for dialogs.
enum DialogButtonStyle {
  /// Primary action (indigo background, white text)
  primary,

  /// Secondary action (outlined, primary text)
  secondary,

  /// Destructive action (red background, white text)
  destructive,
}

/// Show a dialog using the AppDialog component.
/// Returns the value passed to Navigator.pop() in button callbacks.
Future<T?> showAppDialog<T>({
  required BuildContext context,
  required String title,
  required List<DialogButton> buttons,
  String? message,
}) => showDialog<T>(
  context: context,
  barrierDismissible: false, // Require button press (no tap outside)
  builder: (context) =>
      AppDialog(title: title, message: message, buttons: buttons),
);
