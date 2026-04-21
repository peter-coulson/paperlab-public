import 'package:device_preview/device_preview.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/app_init.dart';
import 'package:paperlab/driver/snackbar_interceptor.dart';
import 'package:paperlab/router.dart';
import 'package:paperlab/theme/app_theme.dart';
import 'package:paperlab/widgets/offline_banner.dart';

/// Enable DevicePreview with: --dart-define=DEVICE_PREVIEW=true
const _devicePreviewEnabled = bool.fromEnvironment(
  'DEVICE_PREVIEW',
  defaultValue: false,
);

void main() async {
  await initializeApp();

  runApp(
    ProviderScope(
      child: DevicePreview(
        enabled: _devicePreviewEnabled && !kReleaseMode,
        builder: (context) =>
            const PaperLabApp(skipDevicePreview: !_devicePreviewEnabled),
      ),
    ),
  );
}

class PaperLabApp extends ConsumerWidget {
  const PaperLabApp({super.key, this.skipDevicePreview = true});

  /// When true, skips DevicePreview wrapping entirely.
  /// Default is true for clean MCP/agentic automation.
  /// Set to false in main.dart for manual testing with DevicePreview.
  final bool skipDevicePreview;

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
    title: 'PaperLab',
    theme: AppTheme.lightTheme,
    debugShowCheckedModeBanner: false,
    // GoRouter configuration for URL-based navigation
    routerConfig: appRouter,
    // DevicePreview configuration - skip when using driver entrypoint
    locale: skipDevicePreview ? null : DevicePreview.locale(context),
    builder: (context, child) {
      final devicePreviewWrapped = skipDevicePreview
          ? (child ?? const SizedBox.shrink())
          : DevicePreview.appBuilder(context, child);

      // Column ensures banner pushes content down (not overlay)
      // Individual screens handle their own SafeArea as needed
      Widget content = Column(
        children: [
          // Offline banner at top (pushes content down when visible)
          const OfflineBanner(),
          // Main app content
          Expanded(child: devicePreviewWrapped),
        ],
      );

      // Wrap with logging snackbar interceptor in debug mode
      // This captures all ScaffoldMessenger.showSnackBar() calls automatically
      if (kDebugMode) {
        content = LoggingScaffoldMessenger(child: content);
      }

      return content;
    },
  );
}
