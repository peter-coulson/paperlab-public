import 'package:flutter/material.dart';
import 'package:paperlab/widgets/dialog.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Service for managing user consent for AI data processing.
///
/// Apple App Store Guideline 5.1.2(i) requires explicit consent before
/// sharing personal data with third-party AI services. This service:
/// - Tracks whether user has consented to AI processing
/// - Shows consent dialog when needed
/// - Persists consent state in SharedPreferences
///
/// Usage:
/// ```dart
/// // Before uploading images for AI marking
/// final hasConsent = await ConsentService.instance.ensureAiConsent(context);
/// if (!hasConsent) {
///   // User declined - don't proceed with upload
///   return;
/// }
/// // Proceed with upload
/// ```
class ConsentService {
  ConsentService._();

  static final ConsentService instance = ConsentService._();

  static const String _aiConsentKey = 'ai_processing_consent_granted';

  /// Check if user has already granted AI processing consent.
  Future<bool> hasAiConsent() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool(_aiConsentKey) ?? false;
    } catch (_) {
      // SharedPreferences failure - assume no consent (safe default)
      return false;
    }
  }

  /// Save AI processing consent state.
  Future<void> setAiConsent({required bool granted}) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_aiConsentKey, granted);
    } catch (_) {
      // SharedPreferences failure - consent won't persist but that's OK
      // User will be asked again next time
    }
  }

  /// Ensure user has consented to AI processing.
  ///
  /// If user hasn't consented yet, shows a dialog explaining:
  /// - Images will be sent to OpenAI/Anthropic/Google for marking
  /// - This is required for the app to function
  /// - User can accept or decline
  ///
  /// Returns true if user consents (or already consented).
  /// Returns false if user declines.
  Future<bool> ensureAiConsent(BuildContext context) async {
    // Check if already consented
    if (await hasAiConsent()) {
      return true;
    }

    // Show consent dialog
    if (!context.mounted) return false;

    final result = await showAppDialog<bool>(
      context: context,
      title: 'AI Processing Consent',
      message:
          'To mark your exam papers, PaperLab sends your uploaded images to '
          'AI services (OpenAI, Anthropic, and Google) for analysis.\n\n'
          'Your images are processed securely and are not used to train AI '
          'models. Data is stored until you delete your account.\n\n'
          'Do you consent to this data processing?',
      buttons: [
        DialogButton(
          text: 'I Consent',
          style: DialogButtonStyle.primary,
          onTap: () => Navigator.pop(context, true),
        ),
        DialogButton(
          text: 'Decline',
          style: DialogButtonStyle.secondary,
          onTap: () => Navigator.pop(context, false),
        ),
      ],
    );

    final consented = result ?? false;

    if (consented) {
      await setAiConsent(granted: true);
    }

    return consented;
  }

  /// Revoke AI processing consent.
  ///
  /// User will be prompted again before next upload.
  Future<void> revokeAiConsent() async {
    await setAiConsent(granted: false);
  }
}
