import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:paperlab/config.dart';
import 'package:paperlab/services/auth_service.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/app_logo.dart';
import 'package:paperlab/widgets/primary_button.dart';
import 'package:paperlab/widgets/text_input.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Login Screen - Authentication entry point.
///
/// Features:
/// - Apple Sign-In (native on iOS, web-based on Android)
/// - Google Sign-In (native)
/// - Email/password sign in (expandable form)
/// - Email/password sign up
/// - Loading states for each auth method
/// - Error handling with snackbar messages
///
/// Auth is handled by Supabase - no local JWT storage needed.
/// The AuthGate in main.dart listens to auth state changes and
/// navigates to HomeScreen when authenticated.
class LoginScreen extends StatefulWidget {
  /// Creates a login screen.
  ///
  /// [authService] can be injected for testing.
  /// Defaults to [AuthService.instance].
  const LoginScreen({super.key, AuthService? authService})
    : _authService = authService;

  final AuthService? _authService;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  late final AuthService _auth;
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;
  bool _showEmailForm = false;
  String? _activeMethod; // 'apple', 'google', or 'email'

  @override
  void initState() {
    super.initState();
    _auth = widget._authService ?? AuthService.instance;
    // Debug: verify _showEmailForm starts as false on fresh mount
    debugPrint('LoginScreen initState: _showEmailForm=$_showEmailForm');
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: SingleChildScrollView(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 600),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: AppSpacing.xxl),

                  // Logo
                  const Center(child: AppLogo()),

                  const SizedBox(height: AppSpacing.xxl + AppSpacing.lg),

                  // Apple Sign-In button
                  _SocialSignInButton(
                    text: 'Continue with Apple',
                    icon: LucideIcons.apple,
                    isLoading: _isLoading && _activeMethod == 'apple',
                    onTap: _isLoading ? null : _handleAppleSignIn,
                  ),

                  const SizedBox(height: AppSpacing.md),
                  _SocialSignInButton(
                    text: 'Continue with Google',
                    icon: Icons.g_mobiledata,
                    isLoading: _isLoading && _activeMethod == 'google',
                    onTap: _isLoading ? null : _handleGoogleSignIn,
                  ),
                  const SizedBox(height: AppSpacing.lg),

                  // Divider
                  const Row(
                    children: [
                      Expanded(child: Divider()),
                      Padding(
                        padding: EdgeInsets.symmetric(
                          horizontal: AppSpacing.md,
                        ),
                        child: Text(
                          'or',
                          style: TextStyle(color: AppColors.textSecondary),
                        ),
                      ),
                      Expanded(child: Divider()),
                    ],
                  ),

                  const SizedBox(height: AppSpacing.lg),

                  // Email/password toggle or form
                  if (!_showEmailForm)
                    TextButton(
                      onPressed: _isLoading
                          ? null
                          : () => setState(() => _showEmailForm = true),
                      child: const Text('Continue with email'),
                    )
                  else ...[
                    // Email form
                    AutofillGroup(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          AppTextInput(
                            label: 'Email',
                            controller: _emailController,
                            type: AppTextInputType.email,
                            placeholder: 'your.email@example.com',
                            textInputAction: TextInputAction.next,
                            disabled: _isLoading,
                            autofocus: true,
                            fieldKey: const ValueKey('email_field'),
                          ),
                          const SizedBox(height: AppSpacing.md),
                          AppTextInput(
                            label: 'Password',
                            controller: _passwordController,
                            type: AppTextInputType.password,
                            placeholder: '',
                            textInputAction: TextInputAction.done,
                            onSubmitted: (_) => _handleEmailSignIn(),
                            disabled: _isLoading,
                            fieldKey: const ValueKey('password_field'),
                          ),
                          const SizedBox(height: AppSpacing.lg),
                          PrimaryButton(
                            key: const ValueKey('login_button'),
                            text: _isLoading && _activeMethod == 'email'
                                ? 'Signing in...'
                                : 'Sign In',
                            onTap: _isLoading ? null : _handleEmailSignIn,
                            requiresNetwork: false,
                            disabled: _isLoading,
                          ),
                          const SizedBox(height: AppSpacing.sm),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              TextButton(
                                onPressed: _isLoading
                                    ? null
                                    : _handleEmailSignUp,
                                child: const Text('Create account'),
                              ),
                              const Text(
                                '|',
                                style: TextStyle(
                                  color: AppColors.textSecondary,
                                ),
                              ),
                              TextButton(
                                onPressed: _isLoading
                                    ? null
                                    : _handleForgotPassword,
                                child: const Text('Forgot password?'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],

                  const SizedBox(height: AppSpacing.xxl),

                  // Dev login button (development mode only)
                  if (AppConfig.environment == 'development') ...[
                    const Divider(),
                    const SizedBox(height: AppSpacing.md),
                    TextButton.icon(
                      onPressed: _isLoading ? null : _handleDevLogin,
                      icon: const Icon(LucideIcons.bug, size: 18),
                      label: const Text('Dev Login (Skip Auth)'),
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );

  void _handleDevLogin() {
    _auth.devLogin();
    // AuthGate will automatically navigate to HomeScreen
  }

  Future<void> _handleAppleSignIn() async {
    setState(() {
      _isLoading = true;
      _activeMethod = 'apple';
    });

    try {
      await _auth.signInWithApple();
      // AuthGate will handle navigation on auth state change
    } on AuthException catch (e) {
      if (mounted) _showError(e.message);
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _activeMethod = null;
        });
      }
    }
  }

  Future<void> _handleGoogleSignIn() async {
    setState(() {
      _isLoading = true;
      _activeMethod = 'google';
    });

    try {
      await _auth.signInWithGoogle();
      // Router will handle navigation on auth state change
    } on AuthException catch (e) {
      if (mounted) _showError(e.message);
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _activeMethod = null;
        });
      }
    }
  }

  Future<void> _handleEmailSignIn() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      _showError('Please enter email and password');
      return;
    }

    setState(() {
      _isLoading = true;
      _activeMethod = 'email';
    });

    try {
      await _auth.signInWithPassword(email: email, password: password);
      // AuthGate will handle navigation on auth state change
    } on AuthException catch (e) {
      if (mounted) _showError(e.message);
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _activeMethod = null;
        });
      }
    }
  }

  Future<void> _handleEmailSignUp() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      _showError('Please enter email and password');
      return;
    }

    if (password.length < 6) {
      _showError('Password must be at least 6 characters');
      return;
    }

    setState(() {
      _isLoading = true;
      _activeMethod = 'email';
    });

    try {
      final response = await _auth.signUpWithEmail(
        email: email,
        password: password,
      );

      if (mounted) {
        if (response.session != null) {
          // Email confirmation disabled - user is signed in
          _showMessage('Account created successfully');
        } else {
          // Email confirmation required
          _showMessage('Check your email to confirm your account');
        }
      }
    } on AuthException catch (e) {
      if (mounted) _showError(e.message);
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _activeMethod = null;
        });
      }
    }
  }

  Future<void> _handleForgotPassword() async {
    final email = _emailController.text.trim();

    if (email.isEmpty) {
      _showError('Please enter your email address');
      return;
    }

    setState(() {
      _isLoading = true;
      _activeMethod = 'email';
    });

    try {
      await _auth.resetPassword(email);
      if (mounted) _showMessage('Password reset email sent');
    } on AuthException catch (e) {
      if (mounted) _showError(e.message);
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _activeMethod = null;
        });
      }
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 4),
      ),
    );
  }
}

/// Social sign-in button with consistent styling.
class _SocialSignInButton extends StatelessWidget {
  const _SocialSignInButton({
    required this.text,
    required this.icon,
    required this.onTap,
    this.isLoading = false,
  });

  final String text;
  final IconData icon;
  final VoidCallback? onTap;
  final bool isLoading;

  @override
  Widget build(BuildContext context) => OutlinedButton(
    onPressed: onTap,
    style: OutlinedButton.styleFrom(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.md,
        horizontal: AppSpacing.lg,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppSpacing.sm),
      ),
      side: const BorderSide(color: AppColors.border),
    ),
    child: isLoading
        ? const SizedBox(
            height: 24,
            width: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        : Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 24),
              const SizedBox(width: AppSpacing.md),
              Text(text),
            ],
          ),
  );
}
