import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:paperlab/screens/home_screen.dart';
import 'package:paperlab/screens/login_screen.dart';
import 'package:paperlab/screens/marking_in_progress_screen.dart';
import 'package:paperlab/screens/paper_results_screen.dart';
import 'package:paperlab/screens/paper_selection_screen.dart';
import 'package:paperlab/screens/paper_upload_screen.dart';
import 'package:paperlab/screens/question_results_screen.dart';
import 'package:paperlab/screens/question_selection_screen.dart';
import 'package:paperlab/screens/question_upload_screen.dart';
import 'package:paperlab/screens/settings_screen.dart';
import 'package:paperlab/services/auth_service.dart';

/// Creates a page with no transition on web to avoid Safari swipe-back bug.
/// See: https://github.com/flutter/flutter/issues/114324
///
/// Uses CustomTransitionPage with explicit zero durations for both forward
/// and reverse transitions, which is more reliable than NoTransitionPage.
Page<T> _buildPage<T>(Widget child, GoRouterState state) {
  if (kIsWeb) {
    return CustomTransitionPage<T>(
      key: state.pageKey,
      child: child,
      transitionDuration: Duration.zero,
      reverseTransitionDuration: Duration.zero,
      transitionsBuilder: (context, animation, secondaryAnimation, child) =>
          child,
    );
  }
  return MaterialPage<T>(key: state.pageKey, child: child);
}

/// Route paths as constants for type-safe navigation.
class AppRoutes {
  static const home = '/';
  static const login = '/login';
  static const settings = '/settings';

  // Paper routes
  static const paperSelect = '/papers/select';
  static const paperUpload = '/papers/upload';
  static String paperMarking(int id) => '/papers/$id/marking';
  static String paperResults(int id) => '/papers/$id/results';

  // Paper question upload (for paper context)
  static String paperQuestionUpload(int questionNumber) =>
      '/papers/upload/question/$questionNumber';

  // Question routes
  static const questionSelect = '/questions/select';
  static String questionUpload(int questionId) =>
      '/questions/$questionId/upload';
  static String questionMarking(int id) => '/questions/$id/marking';
  static String questionResults(int id) => '/questions/$id/results';
  static String questionResultsFromPaper(int paperId, int questionId) =>
      '/papers/$paperId/questions/$questionId/results';

  // Auth callback for web OAuth
  static const authCallback = '/auth/callback';
}

/// App router configuration with auth-aware redirects.
///
/// Uses GoRouter for URL-based navigation supporting:
/// - Deep linking and shareable URLs
/// - Browser back/forward navigation
/// - Auth state-based redirects
final GoRouter appRouter = GoRouter(
  initialLocation: AppRoutes.home,
  debugLogDiagnostics: kDebugMode,
  refreshListenable: _AuthNotifier(),
  redirect: _handleRedirect,
  routes: [
    // Login screen
    GoRoute(
      path: AppRoutes.login,
      name: 'login',
      pageBuilder: (context, state) => _buildPage(const LoginScreen(), state),
    ),

    // Home screen (authenticated users)
    GoRoute(
      path: AppRoutes.home,
      name: 'home',
      pageBuilder: (context, state) {
        // Pass extra data (e.g., selection results) to HomeScreen
        final extra = state.extra as Map<String, dynamic>?;
        return _buildPage(HomeScreen(extra: extra), state);
      },
    ),

    // Settings
    GoRoute(
      path: AppRoutes.settings,
      name: 'settings',
      pageBuilder: (context, state) =>
          _buildPage(const SettingsScreen(), state),
    ),

    // Paper selection
    GoRoute(
      path: AppRoutes.paperSelect,
      name: 'paperSelect',
      pageBuilder: (context, state) => _buildPage(
        PaperSelectionScreen(
          onConfirm: (selections) {
            // Store selections in extra and navigate to upload
            // The home screen will handle creating the draft
            context.go(AppRoutes.home, extra: {'paperSelections': selections});
          },
        ),
        state,
      ),
    ),

    // Paper upload (draft editing)
    GoRoute(
      path: AppRoutes.paperUpload,
      name: 'paperUpload',
      pageBuilder: (context, state) =>
          _buildPage(const PaperUploadScreen(), state),
    ),

    // Paper marking in progress
    GoRoute(
      path: '/papers/:id/marking',
      name: 'paperMarking',
      pageBuilder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        final subtitle = state.uri.queryParameters['subtitle'];
        return _buildPage(
          MarkingInProgressScreen(
            attemptId: id,
            isPaper: true,
            subtitle: subtitle,
          ),
          state,
        );
      },
    ),

    // Paper results
    GoRoute(
      path: '/papers/:id/results',
      name: 'paperResults',
      pageBuilder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return _buildPage(PaperResultsScreen(attemptId: id), state);
      },
    ),

    // Paper question upload (paper context)
    GoRoute(
      path: '/papers/upload/question/:questionNumber',
      name: 'paperQuestionUpload',
      pageBuilder: (context, state) {
        final questionNumber = int.parse(
          state.pathParameters['questionNumber']!,
        );
        final extra = state.extra as Map<String, dynamic>?;
        return _buildPage(
          QuestionUploadScreen(
            title: extra?['title'] ?? 'Question $questionNumber',
            subtitle: extra?['subtitle'],
            existingPhotos: extra?['existingPhotos'] ?? [],
          ),
          state,
        );
      },
    ),

    // Question selection
    GoRoute(
      path: AppRoutes.questionSelect,
      name: 'questionSelect',
      pageBuilder: (context, state) => _buildPage(
        QuestionSelectionScreen(
          onConfirm: (selections) {
            // Store selections and navigate back to home
            context.go(
              AppRoutes.home,
              extra: {'questionSelections': selections},
            );
          },
        ),
        state,
      ),
    ),

    // Question upload (standalone practice)
    GoRoute(
      path: '/questions/:id/upload',
      name: 'questionUpload',
      pageBuilder: (context, state) {
        final extra = state.extra as Map<String, dynamic>?;
        return _buildPage(
          QuestionUploadScreen(
            title: extra?['title'] ?? 'Question',
            subtitle: extra?['subtitle'],
            question: extra?['question'],
          ),
          state,
        );
      },
    ),

    // Question marking in progress
    GoRoute(
      path: '/questions/:id/marking',
      name: 'questionMarking',
      pageBuilder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        final subtitle = state.uri.queryParameters['subtitle'];
        return _buildPage(
          MarkingInProgressScreen(
            attemptId: id,
            isPaper: false,
            subtitle: subtitle,
          ),
          state,
        );
      },
    ),

    // Question results (standalone practice)
    GoRoute(
      path: '/questions/:id/results',
      name: 'questionResults',
      pageBuilder: (context, state) {
        final id = int.parse(state.pathParameters['id']!);
        return _buildPage(
          QuestionResultsScreen.fromPractice(practiceAttemptId: id),
          state,
        );
      },
    ),

    // Question results from paper context
    GoRoute(
      path: '/papers/:paperId/questions/:questionId/results',
      name: 'questionResultsFromPaper',
      pageBuilder: (context, state) {
        final paperId = int.parse(state.pathParameters['paperId']!);
        final questionId = int.parse(state.pathParameters['questionId']!);
        return _buildPage(
          QuestionResultsScreen.fromPaper(
            paperAttemptId: paperId,
            questionAttemptId: questionId,
          ),
          state,
        );
      },
    ),

    // Auth callback for web OAuth redirects
    GoRoute(
      path: AppRoutes.authCallback,
      name: 'authCallback',
      pageBuilder: (context, state) =>
          _buildPage(const _AuthCallbackScreen(), state),
    ),
  ],
  errorBuilder: (context, state) => Scaffold(
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('Page not found'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.go(AppRoutes.home),
            child: const Text('Go Home'),
          ),
        ],
      ),
    ),
  ),
);

/// Handle auth-based redirects.
String? _handleRedirect(BuildContext context, GoRouterState state) {
  final isAuthenticated = AuthService.instance.isAuthenticated;
  final isLoggingIn = state.matchedLocation == AppRoutes.login;
  final isAuthCallback = state.matchedLocation == AppRoutes.authCallback;

  // Allow auth callback to proceed without redirect
  if (isAuthCallback) return null;

  // If not authenticated, redirect to login (except if already on login)
  if (!isAuthenticated && !isLoggingIn) {
    return AppRoutes.login;
  }

  // If authenticated and on login page, redirect to home
  if (isAuthenticated && isLoggingIn) {
    return AppRoutes.home;
  }

  // No redirect needed
  return null;
}

/// Listenable that notifies when auth state changes.
class _AuthNotifier extends ChangeNotifier {
  _AuthNotifier() {
    // Listen to Supabase auth changes
    AuthService.instance.authStateChanges.listen((_) => notifyListeners());
    // Listen to dev session changes
    AuthService.instance.devSessionChanges.listen((_) => notifyListeners());
  }
}

/// Placeholder screen for handling OAuth callbacks on web.
///
/// This screen is shown briefly during OAuth redirect flow.
/// Supabase handles the actual token extraction and session creation.
class _AuthCallbackScreen extends StatefulWidget {
  const _AuthCallbackScreen();

  @override
  State<_AuthCallbackScreen> createState() => _AuthCallbackScreenState();
}

class _AuthCallbackScreenState extends State<_AuthCallbackScreen> {
  @override
  void initState() {
    super.initState();
    // On web, Supabase automatically handles the OAuth callback
    // and updates the auth state. We just need to wait for it.
    // The router's refreshListenable will trigger a redirect to home
    // once the auth state changes.
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted && !AuthService.instance.isAuthenticated) {
        // If still not authenticated after delay, something went wrong
        context.go(AppRoutes.login);
      }
    });
  }

  @override
  Widget build(BuildContext context) => const Scaffold(
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 16),
          Text('Completing sign in...'),
        ],
      ),
    ),
  );
}
