import 'dart:async';
import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:paperlab/config.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Authentication service using Supabase Auth.
///
/// Supports:
/// - Email/password sign up and sign in
/// - Apple Sign-In (native on iOS, web-based on Android)
/// - Google Sign-In (native)
/// - Dev login (development mode only - bypasses Supabase)
///
/// Gracefully handles missing Supabase initialization (for UI testing with
/// SKIP_AUTH=true). Auth methods throw; read-only getters return safe defaults.
///
/// Usage:
/// 1. Initialize Supabase in main.dart before runApp()
/// 2. Access via [AuthService.instance]
/// 3. Use [signInWithApple], [signInWithGoogle], or [signInWithPassword]
/// 4. Access token via [accessToken] for API calls
/// 5. Listen to [authStateChanges] for session updates
class AuthService {
  AuthService._();

  static final instance = AuthService._();

  /// Cached Supabase initialization state (won't change during app runtime).
  bool? _supabaseInitialized;

  /// Check if Supabase is initialized (cached after first check).
  bool get _isSupabaseInitialized {
    if (_supabaseInitialized != null) return _supabaseInitialized!;
    try {
      Supabase.instance;
      _supabaseInitialized = true;
    } catch (_) {
      _supabaseInitialized = false;
    }
    return _supabaseInitialized!;
  }

  SupabaseClient? get _clientOrNull =>
      _isSupabaseInitialized ? Supabase.instance.client : null;
  GoTrueClient? get _authOrNull => _clientOrNull?.auth;

  /// Dev session state (development mode only).
  bool _isDevSession = false;

  /// Stream controller for dev session changes.
  final _devSessionController = StreamController<bool>.broadcast();

  /// Current access token for API calls.
  ///
  /// Returns "dev" for dev sessions, null if Supabase not initialized,
  /// real token otherwise.
  String? get accessToken {
    if (_isDevSession) return 'dev';
    return _authOrNull?.currentSession?.accessToken;
  }

  /// Current user from Supabase.
  User? get currentUser => _authOrNull?.currentUser;

  /// Check if user is authenticated (Supabase or dev session).
  /// In stub mode (Supabase not initialized), returns false.
  bool get isAuthenticated =>
      _isDevSession || (_authOrNull?.currentSession != null);

  /// For compatibility with existing code.
  bool get isLoggedIn => isAuthenticated;

  /// Check if currently in dev session.
  bool get isDevSession => _isDevSession;

  /// Stream of auth state changes (includes dev session).
  /// Returns empty stream if Supabase not initialized.
  Stream<AuthState> get authStateChanges =>
      _authOrNull?.onAuthStateChange ?? const Stream.empty();

  /// Stream of dev session changes (for AuthGate).
  Stream<bool> get devSessionChanges => _devSessionController.stream;

  /// Get auth headers for API requests.
  /// Returns dev token header for dev sessions, empty if not authenticated.
  Map<String, String> get authHeaders {
    if (_isDevSession) {
      return {'Authorization': 'Bearer dev'};
    }
    final token = _authOrNull?.currentSession?.accessToken;
    if (token == null) return {};
    return {'Authorization': 'Bearer $token'};
  }

  /// Sign out and clear session (both Supabase and dev).
  Future<void> signOut() async {
    if (_isDevSession) {
      _isDevSession = false;
      _devSessionController.add(false);
    } else if (_isSupabaseInitialized) {
      await _authOrNull?.signOut();
    }
  }

  /// Alias for signOut() for compatibility.
  Future<void> logout() => signOut();

  // ===========================================================================
  // Dev Login (Development Mode Only)
  // ===========================================================================

  /// Sign in with dev session (development mode only).
  ///
  /// Bypasses Supabase authentication for local testing.
  /// Only available when ENVIRONMENT=development.
  void devLogin() {
    if (AppConfig.environment != 'development') {
      throw StateError('Dev login only available in development mode');
    }
    _isDevSession = true;
    _devSessionController.add(true);
  }

  // ===========================================================================
  // Email/Password Auth
  // ===========================================================================

  /// Throws if Supabase not initialized (stub mode).
  void _requireSupabase() {
    if (!_isSupabaseInitialized) {
      throw const AuthException(
        'Auth not available in stub mode. '
        'Launch app without SKIP_AUTH=true to use authentication.',
      );
    }
  }

  /// Sign up with email and password.
  ///
  /// User will receive confirmation email from Supabase.
  /// Returns AuthResponse with session if email confirmation is disabled,
  /// or without session if confirmation is required.
  /// Throws in stub mode.
  Future<AuthResponse> signUpWithEmail({
    required String email,
    required String password,
  }) async {
    _requireSupabase();
    return _authOrNull!.signUp(email: email, password: password);
  }

  /// Sign in with email and password.
  ///
  /// Throws AuthException if credentials are invalid.
  /// Throws in stub mode.
  Future<AuthResponse> signInWithPassword({
    required String email,
    required String password,
  }) async {
    _requireSupabase();
    return _authOrNull!.signInWithPassword(email: email, password: password);
  }

  /// Send password reset email.
  /// Throws in stub mode.
  Future<void> resetPassword(String email) async {
    _requireSupabase();
    await _authOrNull!.resetPasswordForEmail(email);
  }

  // ===========================================================================
  // Apple Sign-In
  // ===========================================================================

  /// Sign in with Apple.
  ///
  /// On web: Uses Supabase OAuth redirect flow (PKCE).
  /// On native (iOS/macOS): Uses native Sign in with Apple SDK.
  ///
  /// Throws AuthException if sign-in fails or is cancelled.
  /// Throws in stub mode.
  ///
  /// Note: On web, this triggers a full page redirect. The method returns
  /// a placeholder AuthResponse but the actual auth completion happens
  /// when the user is redirected back to /auth/callback.
  Future<AuthResponse> signInWithApple() async {
    _requireSupabase();

    // Web: Use Supabase OAuth redirect flow
    if (kIsWeb) {
      return _signInWithAppleWeb();
    }

    // Native: Use native Apple Sign-In SDK
    return _signInWithAppleNative();
  }

  /// Web-based Apple Sign-In using Supabase OAuth redirect.
  ///
  /// Triggers a full page redirect to Apple's OAuth page.
  /// After authentication, redirects back to /auth/callback.
  Future<AuthResponse> _signInWithAppleWeb() async {
    final success = await _authOrNull!.signInWithOAuth(
      OAuthProvider.apple,
      redirectTo: AppConfig.webAuthCallbackUrl,
    );

    if (!success) {
      throw const AuthException('Apple Sign-In failed to initiate');
    }

    // On web, signInWithOAuth triggers a redirect, so we won't reach here.
    // Return empty response as placeholder (redirect happens before this).
    return AuthResponse(session: null, user: null);
  }

  /// Native Apple Sign-In using the sign_in_with_apple package.
  Future<AuthResponse> _signInWithAppleNative() async {
    // Generate secure nonce for Apple
    final rawNonce = _authOrNull!.generateRawNonce();
    final hashedNonce = sha256.convert(utf8.encode(rawNonce)).toString();

    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
        nonce: hashedNonce,
      );

      final idToken = credential.identityToken;
      if (idToken == null) {
        throw const AuthException('Apple Sign-In failed: no ID token received');
      }

      return _authOrNull!.signInWithIdToken(
        provider: OAuthProvider.apple,
        idToken: idToken,
        nonce: rawNonce,
      );
    } on SignInWithAppleAuthorizationException catch (e) {
      if (e.code == AuthorizationErrorCode.canceled) {
        throw const AuthException('Apple Sign-In was cancelled');
      }
      throw AuthException('Apple Sign-In failed: ${e.message}');
    }
  }

  // ===========================================================================
  // Google Sign-In
  // ===========================================================================

  /// Sign in with Google.
  ///
  /// On web: Uses Supabase OAuth redirect flow (PKCE).
  /// On native (iOS/Android): Uses native Google Sign-In SDK.
  ///
  /// Throws AuthException if sign-in fails or is cancelled.
  /// Throws in stub mode.
  Future<AuthResponse> signInWithGoogle() async {
    _requireSupabase();

    if (kIsWeb) {
      return _signInWithGoogleWeb();
    }
    return _signInWithGoogleNative();
  }

  /// Web-based Google Sign-In using Supabase OAuth redirect.
  Future<AuthResponse> _signInWithGoogleWeb() async {
    final success = await _authOrNull!.signInWithOAuth(
      OAuthProvider.google,
      redirectTo: AppConfig.webAuthCallbackUrl,
    );

    if (!success) {
      throw const AuthException('Google Sign-In failed to initiate');
    }

    return AuthResponse(session: null, user: null);
  }

  /// Native Google Sign-In using the google_sign_in package.
  Future<AuthResponse> _signInWithGoogleNative() async {
    // Web client ID required as serverClientId for Supabase verification
    const webClientId =
        '967650195782-nerh4q33vlfmcatc1rhqn80eju82ba0u'
        '.apps.googleusercontent.com';
    // iOS client ID for native sign-in
    const iosClientId =
        '967650195782-t1orinpdkev7lpgvnu1cbvt497de6lh2'
        '.apps.googleusercontent.com';

    final googleSignIn = GoogleSignIn(
      clientId: iosClientId,
      serverClientId: webClientId,
    );

    final googleUser = await googleSignIn.signIn();
    if (googleUser == null) {
      throw const AuthException('Google Sign-In was cancelled');
    }

    final googleAuth = await googleUser.authentication;
    final idToken = googleAuth.idToken;
    final accessToken = googleAuth.accessToken;

    if (idToken == null) {
      throw const AuthException('Google Sign-In failed: no ID token received');
    }

    if (accessToken == null) {
      throw const AuthException(
        'Google Sign-In failed: no access token received',
      );
    }

    return _authOrNull!.signInWithIdToken(
      provider: OAuthProvider.google,
      idToken: idToken,
      accessToken: accessToken,
    );
  }

  // ===========================================================================
  // Session Management
  // ===========================================================================

  /// Refresh current session.
  ///
  /// Called automatically by supabase_flutter when token expires.
  /// Can be called manually if needed.
  /// Throws in stub mode.
  Future<AuthResponse> refreshSession() async {
    _requireSupabase();
    return _authOrNull!.refreshSession();
  }

  /// Get current session, refreshing if expired.
  /// Returns null in stub mode.
  Future<Session?> getSession() async => _authOrNull?.currentSession;
}
