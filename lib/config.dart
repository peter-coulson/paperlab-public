import 'package:flutter/foundation.dart' show kIsWeb;

/// App configuration with environment-based settings.
///
/// Supports two environments: development, production.
/// Environment selected via --dart-define flags at build time.
///
/// Example build commands:
/// - Production (default): fvm flutter run (Railway backend)
/// - Development (local): fvm flutter run --dart-define=ENVIRONMENT=development
///
/// Note: M7 is Professional Beta, not public launch.
/// M9 is true production launch.
/// Environment naming reflects infrastructure (development vs deployed),
/// not release stage.
class AppConfig {
  AppConfig._();

  /// Current environment (development or production).
  /// Defaults to production (TestFlight/App Store safe).
  /// Pass --dart-define=ENVIRONMENT=development for local backend testing.
  static const String environment = String.fromEnvironment(
    'ENVIRONMENT',
    defaultValue: 'production',
  );

  /// Auto-login for development (bypasses auth on startup).
  /// Pass --dart-define=AUTO_LOGIN=true for hands-free local development.
  /// Only effective when ENVIRONMENT=development.
  static const bool autoLogin = bool.fromEnvironment(
    'AUTO_LOGIN',
    defaultValue: false,
  );

  /// Base URL for API requests.
  ///
  /// Selected based on ENVIRONMENT value:
  /// - development: http://localhost:8000 (local backend)
  /// - production: https://paperlab-production.up.railway.app (Railway deployment)
  static const String apiBaseUrl = environment == 'production'
      ? 'https://paperlab-production.up.railway.app'
      : 'http://localhost:8000';

  /// Health check endpoint for real connectivity verification.
  /// Used to verify internet access beyond device connectivity status.
  static const String healthCheckPath = '/health';

  /// Cloudflare R2 storage domain.
  /// Requests to this domain bypass auth headers (presigned URLs).
  static const String r2Domain = 'r2.cloudflarestorage.com';

  /// Connectivity check debounce duration.
  /// Prevents rapid banner flickering during brief disconnections.
  static const Duration connectivityDebounce = Duration(milliseconds: 500);

  /// Real connectivity check timeout.
  /// How long to wait for health check response before assuming offline.
  static const Duration connectivityCheckTimeout = Duration(seconds: 5);

  // =========================================================================
  // Supabase Authentication Configuration
  // =========================================================================

  /// Supabase project URL.
  /// Get from: Supabase Dashboard > Settings > API > Project URL
  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://yxapcpvkkpoqfasvujlw.supabase.co',
  );

  /// Supabase anon/public key (safe to include in client apps).
  /// Get from: Supabase Dashboard > Settings > API > Publishable key
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue: 'sb_publishable_rRTm_mXbOiVCktQllXDhiw_nu4Fsxbw',
  );

  /// Deep link scheme for OAuth callbacks.
  /// Must match iOS Info.plist CFBundleURLSchemes and Android intent filter.
  static const String deepLinkScheme = 'com.mypaperlab.paperlab';

  /// Deep link host for auth callbacks.
  static const String deepLinkHost = 'login-callback';

  /// Full auth callback URL for OAuth providers (native deep link).
  static String get authCallbackUrl => '$deepLinkScheme://$deepLinkHost';

  // =========================================================================
  // Web OAuth Configuration
  // =========================================================================

  /// Web OAuth callback URL for development (localhost).
  /// Uses port 8080 which is the default for `fvm flutter run -d chrome`.
  static const String _webAuthCallbackUrlDev =
      'http://localhost:8080/auth/callback';

  /// Web OAuth callback URL for production.
  static const String _webAuthCallbackUrlProd =
      'https://app.mypaperlab.com/auth/callback';

  /// Get the appropriate OAuth callback URL based on platform.
  ///
  /// On web, uses redirect-based OAuth flow with HTTP URLs.
  /// On native platforms, uses deep links for native OAuth SDKs.
  static String get webAuthCallbackUrl {
    if (!kIsWeb) {
      // Native platforms use deep links
      return authCallbackUrl;
    }
    // Web uses HTTP redirect URLs
    return environment == 'production'
        ? _webAuthCallbackUrlProd
        : _webAuthCallbackUrlDev;
  }
}
