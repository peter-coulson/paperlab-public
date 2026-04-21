// Driver-enabled entrypoint for MCP-based UI automation and screenshots.
//
// Use this entrypoint when launching via MCP tools that need flutter_driver
// capabilities (screenshots, tap, scroll, enter_text, etc.).
//
// Launch with: `flutter run --target=lib/driver_main.dart`
// Or via MCP: `launch_app(root, device, target="lib/driver_main.dart")`
//
// NOTE: This entrypoint intentionally excludes DevicePreview for cleaner
// agentic automation:
// - Screenshots capture only app UI (no phone bezels or settings panels)
// - Simpler widget tree for flutter_driver navigation
// - No risk of DevicePreview intercepting input events
//
// For manual testing with DevicePreview, use main.dart instead.
//
// AGENTIC LOGGING:
// This entrypoint includes DriverStateWidget for agentic UI testing.
// Query app state via: driver.getText(find.byValueKey('driver_state'))
// See lib/driver/ for logging infrastructure.
//
// SKIP_AUTH MODE:
// Pass --dart-define=SKIP_AUTH=true to skip Supabase initialization.
// Useful for UI automation testing without requiring backend/auth setup.
// The app will show the login screen but auth operations won't work.
//
// ignore_for_file: depend_on_referenced_packages

import 'package:flutter/material.dart';
import 'package:flutter_driver/driver_extension.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/app_init.dart';
import 'package:paperlab/driver/agent_interaction.dart';
import 'package:paperlab/driver/driver_state_widget.dart';
import 'package:paperlab/main.dart';

/// Skip Supabase initialization for UI testing without backend.
const _skipAuth = bool.fromEnvironment('SKIP_AUTH', defaultValue: false);

void main() async {
  // CRITICAL: Enable Flutter Driver extension FIRST, before any other binding.
  // enableFlutterDriverExtension() creates a special _DriverBinding that must
  // be the first binding created, otherwise service extensions won't work.
  enableFlutterDriverExtension();

  // Register agent interaction extensions immediately after driver extension.
  // Must be registered before async work so they're available when external
  // tools connect to the VM service.
  registerAgentExtensions();

  // Now initialize app (Supabase, etc.) - binding already exists.
  // SKIP_AUTH mode allows UI testing without requiring backend connectivity.
  if (!_skipAuth) {
    await initializeApp();
  } else {
    debugPrint('[Driver] SKIP_AUTH mode: Supabase initialization skipped');
  }

  // Clean widget tree without DevicePreview for optimal agentic automation
  runApp(
    const ProviderScope(
      child: Stack(
        textDirection: TextDirection.ltr,
        children: [
          PaperLabApp(skipDevicePreview: true),
          // Hidden widget exposing app state for driver queries.
          // Query via: driver.getText(find.byValueKey('driver_state'))
          // Wrapped in Directionality because Text widgets require it,
          // and Stack's textDirection doesn't provide an InheritedWidget.
          Directionality(
            textDirection: TextDirection.ltr,
            child: DriverStateWidget(),
          ),
        ],
      ),
    ),
  );
}
