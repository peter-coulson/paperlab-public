import 'package:flutter/widgets.dart';
import 'package:paperlab/config.dart';
import 'package:paperlab/services/auth_service.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Shared app initialization logic.
///
/// Called by both main.dart and driver_main.dart to ensure
/// consistent startup behavior across entrypoints.
Future<void> initializeApp() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Set up custom error handler to catch widget build errors
  FlutterError.onError = (details) {
    // Always log to console with clear marker
    debugPrint('');
    debugPrint('╔══════════════════════════════════════════════════════════╗');
    debugPrint('║  FLUTTER ERROR CAUGHT                                    ║');
    debugPrint('╚══════════════════════════════════════════════════════════╝');
    debugPrint('Exception: ${details.exception}');
    debugPrint('Context: ${details.context}');
    debugPrint('Stack trace:');
    debugPrint('${details.stack}');
    debugPrint('════════════════════════════════════════════════════════════');
    debugPrint('');

    // Still show the red error screen in debug mode
    FlutterError.presentError(details);
  };

  await Supabase.initialize(
    url: AppConfig.supabaseUrl,
    anonKey: AppConfig.supabaseAnonKey,
  );

  // Auto-login for frictionless local development
  if (AppConfig.autoLogin && AppConfig.environment == 'development') {
    AuthService.instance.devLogin();
  }
}
