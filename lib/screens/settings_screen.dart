import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:paperlab/exceptions/network_exceptions.dart';
import 'package:paperlab/providers/providers.dart';
import 'package:paperlab/router.dart';
import 'package:paperlab/services/auth_service.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_effects.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/widgets/dialog.dart';
import 'package:paperlab/widgets/primary_button.dart';
import 'package:paperlab/widgets/screen_header.dart';
import 'package:url_launcher/url_launcher.dart';

/// Settings Screen - User settings and account management.
///
/// Features:
/// - Legal links (Privacy Policy, Terms of Service)
/// - Delete account option (for App Store compliance)
/// - Logout functionality
///
/// Navigation:
/// - Back button -> Returns to Home Screen
/// - Delete Account -> Confirmation dialog -> Sign out -> Login Screen
/// - Logout -> AuthGate redirects to Login Screen (via Supabase auth state)
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
    backgroundColor: AppColors.background,
    // Prevent keyboard from pushing up content (causes overflow with Spacer)
    resizeToAvoidBottomInset: false,
    body: SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header (has built-in padding - no wrapper needed)
          const ScreenHeader(title: 'Settings'),

          // Legal section
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.screenHorizontalMargin,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppTypography.sectionTitle('Legal'),
                const SizedBox(height: AppSpacing.md),
                const _LegalLinkTile(
                  title: 'Privacy Policy',
                  url: 'https://mypaperlab.com/privacy',
                ),
                const SizedBox(height: AppSpacing.sm),
                const _LegalLinkTile(
                  title: 'Terms of Service',
                  url: 'https://mypaperlab.com/terms',
                ),
              ],
            ),
          ),

          const SizedBox(height: AppSpacing.xl),

          // Account section
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.screenHorizontalMargin,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppTypography.sectionTitle('Account'),
                const SizedBox(height: AppSpacing.md),
                const _RequestPaperTile(),
                const SizedBox(height: AppSpacing.sm),
                _DeleteAccountTile(
                  onDeleteConfirmed: () => _handleDeleteAccount(context, ref),
                ),
              ],
            ),
          ),

          // Spacer pushes logout to bottom
          const Spacer(),

          // Logout button at bottom
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: PrimaryButton(
              text: 'Logout',
              onTap: () => _handleLogout(context),
              requiresNetwork: false,
            ),
          ),
        ],
      ),
    ),
  );

  /// Handle logout action.
  ///
  /// Signs out via Supabase - router redirect will automatically
  /// redirect to Login Screen when auth state changes.
  ///
  /// No confirmation dialog (per spec):
  /// - Logout is immediate (no confirmation) - users can log back in easily
  /// - Rationale: Logout is not destructive (no data loss)
  Future<void> _handleLogout(BuildContext context) async {
    // Sign out via Supabase - router redirect handles navigation
    await AuthService.instance.signOut();

    // Navigate to home - router will redirect to login since not authenticated
    if (context.mounted) {
      context.go(AppRoutes.home);
    }
  }

  /// Handle delete account action after user confirmation.
  ///
  /// Steps:
  /// 1. Delete all user data from backend (images, attempts, results)
  /// 2. Sign out (clears local session)
  /// 3. Navigate to login screen
  ///
  /// Note: Supabase account deletion requires admin API and should be
  /// handled by the backend as part of the /api/account DELETE endpoint.
  Future<void> _handleDeleteAccount(BuildContext context, WidgetRef ref) async {
    final accountRepository = ref.read(accountRepositoryProvider);

    try {
      // Delete all user data from backend
      await accountRepository.deleteAccount();

      // Sign out locally
      await AuthService.instance.signOut();

      // Navigate to login screen
      if (context.mounted) {
        context.go(AppRoutes.login);
      }
    } on NetworkException catch (e) {
      // Show error dialog
      if (context.mounted) {
        await showAppDialog(
          context: context,
          title: 'Unable to Delete Account',
          message: e.message,
          buttons: [
            DialogButton(
              text: 'OK',
              style: DialogButtonStyle.primary,
              onTap: () => Navigator.pop(context),
            ),
          ],
        );
      }
    }
  }
}

/// Tappable tile for legal links (Privacy Policy, Terms of Service).
///
/// Opens the URL in the device's default browser.
/// Styled to match app design patterns with:
/// - InteractiveEffect for press feedback
/// - Standard card styling with border and shadow
/// - External link icon to indicate navigation away from app
class _LegalLinkTile extends StatelessWidget {
  const _LegalLinkTile({required this.title, required this.url});

  final String title;
  final String url;

  @override
  Widget build(BuildContext context) => InteractiveEffect(
    onTap: () => _launchUrl(),
    child: Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.background,
        border: Border.all(
          color: AppColors.border,
          width: AppEffects.borderWidth,
        ),
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        boxShadow: AppEffects.shadow,
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              title,
              style: AppTypography.body.copyWith(color: AppColors.textPrimary),
            ),
          ),
          const Icon(
            LucideIcons.external_link,
            size: AppSpacing.iconSizeSmall,
            color: AppColors.textSecondary,
          ),
        ],
      ),
    ),
  );

  Future<void> _launchUrl() async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}

/// Delete account tile with confirmation flow.
///
/// Requires user to type "DELETE" to confirm, per Apple App Store
/// guidelines (5.1.1(v)) for account deletion.
///
/// Flow:
/// 1. User taps "Delete Account" tile
/// 2. Confirmation dialog appears with warning text
/// 3. User must type "DELETE" in text field
/// 4. Delete button only enabled when "DELETE" is typed correctly
/// 5. On confirm, callback is invoked to perform deletion
class _DeleteAccountTile extends StatefulWidget {
  const _DeleteAccountTile({required this.onDeleteConfirmed});

  /// Callback invoked when user confirms deletion by typing "DELETE"
  final VoidCallback onDeleteConfirmed;

  @override
  State<_DeleteAccountTile> createState() => _DeleteAccountTileState();
}

class _DeleteAccountTileState extends State<_DeleteAccountTile> {
  bool _isDeleting = false;

  @override
  Widget build(BuildContext context) {
    final tile = Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.background,
        border: Border.all(
          color: AppColors.destructive.withValues(alpha: 0.3),
          width: AppEffects.borderWidth,
        ),
        borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
        boxShadow: AppEffects.shadow,
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              'Delete Account',
              style: AppTypography.body.copyWith(color: AppColors.destructive),
            ),
          ),
          if (_isDeleting)
            const SizedBox(
              width: AppSpacing.iconSizeSmall,
              height: AppSpacing.iconSizeSmall,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: AppColors.destructive,
              ),
            )
          else
            const Icon(
              LucideIcons.trash_2,
              size: AppSpacing.iconSizeSmall,
              color: AppColors.destructive,
            ),
        ],
      ),
    );

    // When deleting, don't wrap in InteractiveEffect
    if (_isDeleting) {
      return tile;
    }

    return InteractiveEffect(
      onTap: () => _showDeleteConfirmation(context),
      child: tile,
    );
  }

  /// Show confirmation dialog with "DELETE" text input requirement.
  Future<void> _showDeleteConfirmation(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => const _DeleteConfirmationDialog(),
    );

    if (confirmed == true && mounted) {
      // Show loading state
      setState(() {
        _isDeleting = true;
      });

      // Perform deletion
      widget.onDeleteConfirmed();
    }
  }
}

/// Separate StatefulWidget for delete confirmation dialog.
///
/// This ensures the TextEditingController is properly managed by the widget
/// lifecycle and disposed only after all animations complete.
class _DeleteConfirmationDialog extends StatefulWidget {
  const _DeleteConfirmationDialog();

  @override
  State<_DeleteConfirmationDialog> createState() =>
      _DeleteConfirmationDialogState();
}

class _DeleteConfirmationDialogState extends State<_DeleteConfirmationDialog> {
  final _controller = TextEditingController();
  bool _isDeleteEnabled = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    backgroundColor: AppColors.background,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    contentPadding: const EdgeInsets.all(AppSpacing.lg),
    content: ConstrainedBox(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.6,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Scrollable content area
          Flexible(
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Title
                  Text(
                    'Delete Account?',
                    style: AppTypography.h2.copyWith(
                      color: AppColors.textPrimary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.md),
                  // Warning message
                  Text(
                    'This will permanently delete all your data '
                    'including:\n\n'
                    '\u2022 All paper attempts and results\n'
                    '\u2022 All practice question attempts\n'
                    '\u2022 All uploaded images\n\n'
                    'This action cannot be undone.',
                    style: AppTypography.body.copyWith(
                      color: AppColors.textSecondary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  // Instruction
                  Text(
                    'Type DELETE to confirm:',
                    style: AppTypography.bodySmall.copyWith(
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  // Text input for "DELETE"
                  TextField(
                    controller: _controller,
                    autocorrect: false,
                    textCapitalization: TextCapitalization.characters,
                    textAlign: TextAlign.center,
                    style: AppTypography.body.copyWith(
                      color: AppColors.textPrimary,
                      letterSpacing: 2,
                    ),
                    decoration: InputDecoration(
                      hintText: 'DELETE',
                      hintStyle: AppTypography.body.copyWith(
                        color: AppColors.textTertiary,
                        letterSpacing: 2,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.md,
                        vertical: 12,
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(
                          AppSpacing.borderRadius,
                        ),
                        borderSide: BorderSide(
                          color: _isDeleteEnabled
                              ? AppColors.destructive
                              : AppColors.border,
                          width: AppEffects.borderWidth,
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(
                          AppSpacing.borderRadius,
                        ),
                        borderSide: BorderSide(
                          color: _isDeleteEnabled
                              ? AppColors.destructive
                              : AppColors.primary,
                          width: AppEffects.borderWidth,
                        ),
                      ),
                    ),
                    onChanged: (value) {
                      final shouldEnable = value.toUpperCase() == 'DELETE';
                      if (shouldEnable != _isDeleteEnabled) {
                        setState(() {
                          _isDeleteEnabled = shouldEnable;
                        });
                      }
                    },
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          // Buttons (outside scroll area)
          Row(
            children: [
              // Cancel button
              Expanded(
                child: TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  style: TextButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.lg,
                      vertical: 12,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(
                        AppSpacing.borderRadius,
                      ),
                      side: const BorderSide(color: AppColors.border),
                    ),
                    minimumSize: const Size(0, 48),
                  ),
                  child: Text(
                    'Cancel',
                    style: AppTypography.body.copyWith(
                      color: AppColors.primary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              // Delete button (only enabled when DELETE is typed)
              Expanded(
                child: TextButton(
                  onPressed: _isDeleteEnabled
                      ? () => Navigator.pop(context, true)
                      : null,
                  style: TextButton.styleFrom(
                    backgroundColor: _isDeleteEnabled
                        ? AppColors.destructive
                        : AppColors.textTertiary,
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.lg,
                      vertical: 12,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(
                        AppSpacing.borderRadius,
                      ),
                    ),
                    minimumSize: const Size(0, 48),
                  ),
                  child: Text(
                    'Delete',
                    style: AppTypography.body.copyWith(
                      color: _isDeleteEnabled
                          ? Colors.white
                          : Colors.white.withValues(alpha: 0.7),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  );
}

/// Tappable tile for requesting a past paper.
///
/// Opens a dialog where users can fill in paper details,
/// then opens the native email client with pre-populated content.
class _RequestPaperTile extends StatelessWidget {
  const _RequestPaperTile();

  @override
  Widget build(BuildContext context) => InteractiveEffect(
        onTap: () => _showRequestDialog(context),
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: BoxDecoration(
            color: AppColors.background,
            border: Border.all(
              color: AppColors.border,
              width: AppEffects.borderWidth,
            ),
            borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
            boxShadow: AppEffects.shadow,
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'Request a Paper',
                  style: AppTypography.body.copyWith(
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
              const Icon(
                LucideIcons.mail,
                size: AppSpacing.iconSizeSmall,
                color: AppColors.textSecondary,
              ),
            ],
          ),
        ),
      );

  Future<void> _showRequestDialog(BuildContext context) async {
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => const _RequestPaperDialog(),
    );
  }
}

/// Dialog for entering paper request details.
///
/// Collects paper name, exam board, year, and optional notes.
/// On submit, opens the native email client with pre-populated
/// subject and body targeting support@mypaperlab.com.
class _RequestPaperDialog extends StatefulWidget {
  const _RequestPaperDialog();

  @override
  State<_RequestPaperDialog> createState() => _RequestPaperDialogState();
}

class _RequestPaperDialogState extends State<_RequestPaperDialog> {
  final _paperNameController = TextEditingController();
  final _examBoardController = TextEditingController();
  final _yearController = TextEditingController();
  final _notesController = TextEditingController();

  bool _isSubmitEnabled = false;

  @override
  void initState() {
    super.initState();
    _paperNameController.addListener(_validateForm);
    _examBoardController.addListener(_validateForm);
    _yearController.addListener(_validateForm);
  }

  @override
  void dispose() {
    _paperNameController.dispose();
    _examBoardController.dispose();
    _yearController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  void _validateForm() {
    final isValid = _paperNameController.text.trim().isNotEmpty &&
        _examBoardController.text.trim().isNotEmpty &&
        _yearController.text.trim().isNotEmpty;
    if (isValid != _isSubmitEnabled) {
      setState(() {
        _isSubmitEnabled = isValid;
      });
    }
  }

  Future<void> _submitRequest() async {
    final paperName = _paperNameController.text.trim();
    final examBoard = _examBoardController.text.trim();
    final year = _yearController.text.trim();
    final notes = _notesController.text.trim();

    final emailBody = '''
Please send me the following paper:

Paper: $paperName
Exam Board: $examBoard
Year: $year
${notes.isNotEmpty ? '\nAdditional Notes:\n$notes' : ''}

Thank you!''';

    final uri = Uri(
      scheme: 'mailto',
      path: 'support@mypaperlab.com',
      query: _encodeMailtoQuery({
        'subject': 'Paper Request: $paperName ($year)',
        'body': emailBody,
      }),
    );

    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (mounted) {
        Navigator.pop(context);
      }
    } else {
      // Fallback: show error if no email client
      if (mounted) {
        await showAppDialog(
          context: context,
          title: 'No Email App Found',
          message: 'Please email support@mypaperlab.com manually '
              'with your paper request.',
          buttons: [
            DialogButton(
              text: 'OK',
              style: DialogButtonStyle.primary,
              onTap: () => Navigator.pop(context),
            ),
          ],
        );
      }
    }
  }

  /// Encodes query parameters for mailto URI.
  /// Standard Uri.queryParameters encoding replaces spaces with +
  /// which some email clients don't handle correctly.
  String _encodeMailtoQuery(Map<String, String> params) => params.entries
      .map((e) =>
          '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}')
      .join('&');

  @override
  Widget build(BuildContext context) => AlertDialog(
        backgroundColor: AppColors.background,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.all(AppSpacing.lg),
        content: ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(context).size.height * 0.7,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Title
              Text(
                'Request a Paper',
                style: AppTypography.h2.copyWith(color: AppColors.textPrimary),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(
                "Can't find a paper? Let us know and we'll add it.",
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.lg),

              // Scrollable form area
              Flexible(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _buildTextField(
                        controller: _paperNameController,
                        label: 'Paper Name',
                        placeholder: 'e.g., Biology Paper 1',
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _buildTextField(
                        controller: _examBoardController,
                        label: 'Exam Board',
                        placeholder: 'e.g., AQA, Edexcel, OCR',
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _buildTextField(
                        controller: _yearController,
                        label: 'Year',
                        placeholder: 'e.g., 2024',
                        keyboardType: TextInputType.number,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _buildTextField(
                        controller: _notesController,
                        label: 'Additional Notes (Optional)',
                        placeholder: 'Any other details...',
                        maxLines: 3,
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppSpacing.lg),

              // Buttons
              Row(
                children: [
                  // Cancel button
                  Expanded(
                    child: TextButton(
                      onPressed: () => Navigator.pop(context),
                      style: TextButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.lg,
                          vertical: 12,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(
                            AppSpacing.borderRadius,
                          ),
                          side: const BorderSide(color: AppColors.border),
                        ),
                        minimumSize: const Size(0, 48),
                      ),
                      child: Text(
                        'Cancel',
                        style: AppTypography.body.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  // Submit button
                  Expanded(
                    child: TextButton(
                      onPressed: _isSubmitEnabled ? _submitRequest : null,
                      style: TextButton.styleFrom(
                        backgroundColor: _isSubmitEnabled
                            ? AppColors.primary
                            : AppColors.textTertiary,
                        padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.lg,
                          vertical: 12,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(
                            AppSpacing.borderRadius,
                          ),
                        ),
                        minimumSize: const Size(0, 48),
                      ),
                      child: Text(
                        'Send Request',
                        style: AppTypography.body.copyWith(
                          color: _isSubmitEnabled
                              ? Colors.white
                              : Colors.white.withValues(alpha: 0.7),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required String placeholder,
    TextInputType keyboardType = TextInputType.text,
    int maxLines = 1,
  }) =>
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppTypography.sectionTitle(label),
          const SizedBox(height: AppSpacing.sm),
          TextField(
            controller: controller,
            keyboardType: keyboardType,
            maxLines: maxLines,
            style: AppTypography.body.copyWith(color: AppColors.textPrimary),
            decoration: InputDecoration(
              hintText: placeholder,
              hintStyle: AppTypography.body.copyWith(
                color: AppColors.textTertiary,
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: 12,
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
                borderSide: const BorderSide(
                  color: AppColors.border,
                  width: AppEffects.borderWidth,
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppSpacing.borderRadius),
                borderSide: const BorderSide(
                  color: AppColors.primary,
                  width: AppEffects.borderWidth,
                ),
              ),
            ),
          ),
        ],
      );
}
