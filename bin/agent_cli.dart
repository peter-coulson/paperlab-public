#!/usr/bin/env dart

// CLI tool for agent interaction with a running Flutter app.
//
// Manages app lifecycle and provides UI interaction capabilities.
//
// Usage:
//   dart bin/agent_cli.dart <command> [args]
//
// Lifecycle Commands:
//   launch --project=DIR --device=ID [--target=FILE]  Launch Flutter app
//   stop --pid=PID                                    Stop running app
//   screenshot --pid=PID --output=FILE                Capture window screenshot
//   logs --pid=PID                                    Get app logs
//   hot-reload --uri=URI               Hot reload the app
//   hot-restart --uri=URI              Hot restart (resets state)
//   devices                            List available devices
//
// UI Commands (require --uri):
//   elements              Get all interactive elements
//   tap --id=ID           Tap element by ID
//   tap --x=X --y=Y       Tap at coordinates
//   swipe --id=ID --direction=left|right|up|down
//   longpress --id=ID     Long press element by ID
//
// Example:
//   dart bin/agent_cli.dart launch --project=/path --device=macos
//   dart bin/agent_cli.dart screenshot --pid=12345 --output=screen.png
//   dart bin/agent_cli.dart --uri=ws://127.0.0.1:12345/abc=/ws elements

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:args/args.dart';
import 'package:vm_service/vm_service.dart';
import 'package:vm_service/vm_service_io.dart';

/// Timeout for service extension calls (gestures may wait for animations).
const _serviceCallTimeout = Duration(seconds: 10);

/// Directory for storing app logs.
final _logDir = Directory('/tmp/flutter_ui_test');

/// Timeout for waiting for app to be ready.
const _launchTimeout = Duration(seconds: 60);

Future<void> main(List<String> args) async {
  final parser = ArgParser()
    ..addOption('uri', abbr: 'u', help: 'VM service URI (ws://...)')
    ..addOption('id', help: 'Element ID for tap/swipe')
    ..addOption('x', help: 'X coordinate for tap')
    ..addOption('y', help: 'Y coordinate for tap')
    ..addOption(
      'direction',
      abbr: 'd',
      help: 'Swipe direction',
      defaultsTo: 'left',
    )
    ..addOption('distance', help: 'Swipe distance', defaultsTo: '150')
    // Lifecycle command options
    ..addOption('project', abbr: 'p', help: 'Project root directory')
    ..addOption('device', help: 'Device ID (e.g., macos, chrome)')
    ..addOption('target', abbr: 't', help: 'Target file', defaultsTo: 'lib/main.dart')
    ..addMultiOption('dart-define', help: 'Dart compile-time variable')
    ..addOption('pid', help: 'Process ID for stop/screenshot/logs')
    ..addOption('output', abbr: 'o', help: 'Output file path for screenshot')
    ..addOption('app', help: 'App name for screenshot fallback')
    ..addFlag('help', abbr: 'h', negatable: false);

  final results = parser.parse(args);

  if (results['help'] as bool || results.rest.isEmpty) {
    print('Agent CLI - Flutter app lifecycle and UI interaction\n');
    print('Usage: dart bin/agent_cli.dart <command> [options]\n');
    print('Lifecycle Commands:');
    print('  launch      Launch app (--project, --device, [--target])');
    print('  stop        Stop app (--pid)');
    print('  screenshot  Capture window (--pid, --output)');
    print('  logs        Get app logs (--pid)');
    print('  hot-reload  Hot reload app (--uri)');
    print('  hot-restart Hot restart app, resets state (--uri)');
    print('  devices     List available Flutter devices');
    print('\nUI Commands (require --uri):');
    print('  elements    Get all interactive elements as JSON');
    print('  tap         Tap element (--id=N or --x=X --y=Y)');
    print('  swipe       Swipe element (--id=N --direction=<dir>)');
    print('  longpress   Long press element (--id=N or --x=X --y=Y)');
    print('\n${parser.usage}');
    exit(0);
  }

  final command = results.rest.first;

  // Handle lifecycle commands (don't need VM connection)
  switch (command) {
    case 'launch':
      await _launch(results);
      return;
    case 'stop':
      await _stop(results);
      return;
    case 'screenshot':
      await _screenshot(results);
      return;
    case 'logs':
      await _logs(results);
      return;
    case 'hot-reload':
      await _hotReload(results);
      return;
    case 'hot-restart':
      await _hotRestart(results);
      return;
    case 'devices':
      await _devices();
      return;
  }

  // UI commands need VM connection
  final uri = results['uri'] as String?;
  if (uri == null) {
    stderr.writeln('Error: --uri is required for UI commands');
    exit(1);
  }

  // Validate URI type - must be VM service URI, not DTD URI
  _validateVmServiceUri(uri);

  try {
    final vmService = await vmServiceConnectUri(uri);

    // Find the main isolate
    final vm = await vmService.getVM();
    final isolateRef = vm.isolates?.first;
    if (isolateRef == null) {
      stderr.writeln('Error: No isolate found');
      exit(1);
    }

    final isolateId = isolateRef.id!;

    switch (command) {
      case 'elements':
        await _getElements(vmService, isolateId);
      case 'tap':
        await _tap(vmService, isolateId, results);
      case 'swipe':
        await _swipe(vmService, isolateId, results);
      case 'longpress':
        await _longPress(vmService, isolateId, results);
      default:
        stderr.writeln('Unknown command: $command');
        exit(1);
    }

    await vmService.dispose();
  } catch (e) {
    _handleConnectionError(e, uri);
  }
}

// ============================================================================
// Lifecycle Commands
// ============================================================================

/// Launch a Flutter app and return PID + URIs.
///
/// Spawns `flutter run --machine`, captures output to a log file,
/// waits for the VM service URI, then returns the connection info.
Future<void> _launch(ArgResults args) async {
  final project = args['project'] as String?;
  final device = args['device'] as String?;
  final target = args['target'] as String;
  final dartDefines = args['dart-define'] as List<String>;

  if (project == null || device == null) {
    stderr.writeln('Error: launch requires --project and --device');
    exit(1);
  }

  // Ensure log directory exists
  if (!_logDir.existsSync()) {
    _logDir.createSync(recursive: true);
  }

  // Start flutter run with machine output
  final flutterArgs = [
    'run',
    '--machine',
    '-d', device,
    '-t', target,
    // Add dart-define arguments
    for (final define in dartDefines) '--dart-define=$define',
  ];

  stderr
    ..writeln('Launching: flutter ${flutterArgs.join(' ')}')
    ..writeln('Working directory: $project');

  // Use detachedWithStdio so flutter continues after we exit
  final process = await Process.start(
    'flutter',
    flutterArgs,
    workingDirectory: project,
    environment: Platform.environment,
    mode: ProcessStartMode.detachedWithStdio,
  );

  final pid = process.pid;
  final logFile = File('${_logDir.path}/flutter_$pid.log');
  final logSink = logFile.openWrite();

  String? vmUri;
  String? dtdUri;
  final completer = Completer<void>();

  // Capture stdout and look for URIs
  process.stdout.transform(utf8.decoder).listen((data) {
    logSink.write(data);

    // Parse each line for events
    for (final line in data.split('\n')) {
      if (line.trim().isEmpty) continue;

      try {
        final decoded = jsonDecode(line);

        // Flutter machine output wraps events in arrays
        final events = decoded is List ? decoded : [decoded];

        for (final item in events) {
          if (item is! Map<String, dynamic>) continue;
          final event = item['event'] as String?;
          final params = item['params'] as Map<String, dynamic>?;

          if (event == 'app.debugPort' && params != null) {
            vmUri = params['wsUri'] as String?;
            stderr.writeln('Found VM URI: $vmUri');
          }

          if (event == 'app.dtd' && params != null) {
            dtdUri = params['uri'] as String?;
            stderr.writeln('Found DTD URI: $dtdUri');
          }

          // App is ready when we have the VM URI
          if (vmUri != null && !completer.isCompleted) {
            completer.complete();
          }
        }
      } catch (_) {
        // Not JSON, ignore
      }
    }
  });

  // Capture stderr
  process.stderr.transform(utf8.decoder).listen((data) {
    logSink.write('[STDERR] $data');
    stderr.write(data);
  });

  // Wait for app to be ready or timeout
  try {
    await completer.future.timeout(_launchTimeout);
  } on TimeoutException {
    stderr.writeln('Error: Timeout waiting for app to start');
    process.kill();
    exit(1);
  }

  // Find the actual app PID (flutter run spawns the app as a child process)
  // On macOS, the app runs as a separate process with a different PID
  final appPid = await _findAppPid(project, device);
  if (appPid != null) {
    stderr.writeln('Found app PID: $appPid');
  } else {
    stderr.writeln('Warning: Could not find app PID, using flutter PID');
  }

  // Output result as JSON
  final result = {
    'flutter_pid': pid,
    'app_pid': appPid,
    'pid': appPid ?? pid, // For backwards compatibility, prefer app_pid
    'vm_uri': vmUri,
    'dtd_uri': dtdUri,
    'log_file': logFile.path,
    'project': project,
    'device': device,
    'target': target,
  };

  print(jsonEncode(result));

  // Exit explicitly - the flutter process continues in background
  exit(0);
}

/// Find the actual app PID after flutter run launches it.
///
/// On macOS, flutter run spawns the app as a child process with a different
/// PID. We search for the app by looking for the macOS app bundle in the
/// process list.
Future<int?> _findAppPid(String project, String device) async {
  // Give the app a moment to start
  await Future<void>.delayed(const Duration(milliseconds: 500));

  if (device == 'macos') {
    // For macOS, look for app bundle in build/macos/Build/Products/Debug/
    final appName = project.split('/').last;
    final appBundlePath =
        '$project/build/macos/Build/Products/Debug/$appName.app';

    // Use pgrep to find processes matching the app bundle path
    final result = await Process.run('pgrep', ['-f', appBundlePath]);
    if (result.exitCode == 0) {
      final pids = (result.stdout as String)
          .trim()
          .split('\n')
          .where((s) => s.isNotEmpty)
          .map(int.tryParse)
          .whereType<int>()
          .toList();

      if (pids.isNotEmpty) {
        // Return the first matching PID (should be the app)
        return pids.first;
      }
    }

    // Fallback: try to find by app name only
    final fallbackResult = await Process.run('pgrep', ['-x', appName]);
    if (fallbackResult.exitCode == 0) {
      final pids = (fallbackResult.stdout as String)
          .trim()
          .split('\n')
          .where((s) => s.isNotEmpty)
          .map(int.tryParse)
          .whereType<int>()
          .toList();

      if (pids.isNotEmpty) {
        return pids.first;
      }
    }
  }

  // For other platforms or if macOS detection failed, return null
  return null;
}

/// Stop a running Flutter app by PID (with app name fallback for macOS).
Future<void> _stop(ArgResults args) async {
  final pidStr = args['pid'] as String?;
  final appName = args['app'] as String?;

  if (pidStr == null) {
    stderr.writeln('Error: stop requires --pid');
    exit(1);
  }

  final pid = int.tryParse(pidStr);
  if (pid == null) {
    stderr.writeln('Error: --pid must be a number');
    exit(1);
  }

  // Try to kill the process
  var killed = Process.killPid(pid, ProcessSignal.sigterm);

  // If that didn't work and we have an app name, try to find and kill by name
  if (!killed && appName != null) {
    // Use pkill to kill by app name
    final pkillResult = await Process.run('pkill', ['-f', appName]);
    killed = pkillResult.exitCode == 0;
  }

  // Clean up log file
  final logFile = File('${_logDir.path}/flutter_$pid.log');
  if (logFile.existsSync()) {
    try {
      logFile.deleteSync();
    } catch (_) {
      // Ignore cleanup errors
    }
  }

  final result = {
    'pid': pid,
    'killed': killed,
  };

  print(jsonEncode(result));
}

/// Take a screenshot of the app window by PID.
///
/// Uses pre-compiled window_helper binary for fast window ID lookup,
/// then uses screencapture to capture that specific window.
Future<void> _screenshot(ArgResults args) async {
  final pidStr = args['pid'] as String?;
  final output = args['output'] as String?;

  if (pidStr == null || output == null) {
    stderr.writeln('Error: screenshot requires --pid and --output');
    exit(1);
  }

  final pid = int.tryParse(pidStr);
  if (pid == null) {
    stderr.writeln('Error: --pid must be a number');
    exit(1);
  }

  // Get app name for fallback window search
  final appName = args['app'] as String? ?? 'paperlab';

  // Find window_helper binary (in same directory as this script)
  final scriptDir = Platform.script.toFilePath();
  final binDir = scriptDir.endsWith('.dart')
      ? File(scriptDir).parent.path
      : File(scriptDir).parent.path;
  final windowHelper = '$binDir/window_helper';

  ProcessResult windowResult;

  // Prefer pre-compiled helper for ~3x faster execution
  if (File(windowHelper).existsSync()) {
    windowResult = await Process.run(windowHelper, [pidStr, appName]);
  } else {
    // Fallback to Swift JIT (slower but always available)
    final swiftCode = '''
import Cocoa
let targetPid = $pid
let appName = "$appName"
let options = CGWindowListOption(arrayLiteral: .optionAll)
guard let windowList = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else { exit(1) }
for window in windowList {
    if let wPid = window[kCGWindowOwnerPID as String] as? Int,
       let wid = window[kCGWindowNumber as String] as? Int,
       let layer = window[kCGWindowLayer as String] as? Int,
       wPid == targetPid && layer == 0 {
        let bounds = window[kCGWindowBounds as String] as? [String: Any] ?? [:]
        let w = bounds["Width"] as? Int ?? 0
        let h = bounds["Height"] as? Int ?? 0
        if w > 100 && h > 100 { print(wid); exit(0) }
    }
}
for window in windowList {
    if let name = window[kCGWindowOwnerName as String] as? String,
       let wid = window[kCGWindowNumber as String] as? Int,
       let layer = window[kCGWindowLayer as String] as? Int,
       name.lowercased() == appName.lowercased() && layer == 0 {
        let bounds = window[kCGWindowBounds as String] as? [String: Any] ?? [:]
        let w = bounds["Width"] as? Int ?? 0
        let h = bounds["Height"] as? Int ?? 0
        if w > 100 && h > 100 { print(wid); exit(0) }
    }
}
exit(1)
''';
    windowResult = await Process.run('swift', ['-e', swiftCode]);
  }

  if (windowResult.exitCode != 0) {
    stderr
      ..writeln('Error: Could not find window for PID $pid')
      ..writeln('The app may not be running or have a visible window.');
    exit(1);
  }

  final windowId = windowResult.stdout.toString().trim();

  // Take screenshot of that window
  final screencapResult = await Process.run(
    'screencapture',
    ['-l', windowId, '-x', output],
  );

  if (screencapResult.exitCode != 0) {
    stderr
      ..writeln('Error: screencapture failed')
      ..writeln(screencapResult.stderr);
    exit(1);
  }

  // Resize to reduce token cost (~44% savings, still readable for UI analysis)
  await Process.run('sips', ['-Z', '1000', output]);

  final result = {
    'pid': pid,
    'window_id': int.parse(windowId),
    'output': output,
    'success': true,
  };

  print(jsonEncode(result));
}

/// Get logs for a running app by PID.
Future<void> _logs(ArgResults args) async {
  final pidStr = args['pid'] as String?;
  if (pidStr == null) {
    stderr.writeln('Error: logs requires --pid');
    exit(1);
  }

  final pid = int.tryParse(pidStr);
  if (pid == null) {
    stderr.writeln('Error: --pid must be a number');
    exit(1);
  }

  final logFile = File('${_logDir.path}/flutter_$pid.log');
  if (!logFile.existsSync()) {
    stderr.writeln('Error: No log file found for PID $pid');
    exit(1);
  }

  final logs = logFile.readAsStringSync();
  final result = {
    'pid': pid,
    'log_file': logFile.path,
    'logs': logs,
  };

  print(jsonEncode(result));
}

/// Hot reload the app via VM service.
Future<void> _hotReload(ArgResults args) async {
  final uri = args['uri'] as String?;
  if (uri == null) {
    stderr.writeln('Error: hot-reload requires --uri');
    exit(1);
  }

  _validateVmServiceUri(uri);

  try {
    final vmService = await vmServiceConnectUri(uri);

    // Find the main isolate
    final vm = await vmService.getVM();
    final isolateRef = vm.isolates?.first;
    if (isolateRef == null) {
      stderr.writeln('Error: No isolate found');
      exit(1);
    }

    // Trigger hot reload
    final report = await vmService.reloadSources(isolateRef.id!);

    await vmService.dispose();

    // ReloadReport.success is false when no sources changed, true when
    // reloaded. Either way, if we get here without exception, the operation
    // succeeded. We return true to indicate the command executed.
    final hadChanges = report.success == true;

    final result = {
      'success': true, // Command succeeded
      'reloaded': hadChanges, // Whether sources actually changed
    };

    print(jsonEncode(result));
  } catch (e) {
    _handleConnectionError(e, uri);
  }
}

/// Hot restart the app via VM service (resets app state).
Future<void> _hotRestart(ArgResults args) async {
  final uri = args['uri'] as String?;
  if (uri == null) {
    stderr.writeln('Error: hot-restart requires --uri');
    exit(1);
  }

  _validateVmServiceUri(uri);

  try {
    final vmService = await vmServiceConnectUri(uri);

    // Find the main isolate
    final vm = await vmService.getVM();
    final isolateRef = vm.isolates?.first;
    if (isolateRef == null) {
      stderr.writeln('Error: No isolate found');
      exit(1);
    }

    // Trigger hot restart using the Flutter-specific service extension
    final response = await vmService.callServiceExtension(
      'ext.flutter.reassemble',
      isolateId: isolateRef.id!,
    );

    await vmService.dispose();

    final result = {
      'success': response.json != null,
    };

    print(jsonEncode(result));
  } catch (e) {
    _handleConnectionError(e, uri);
  }
}

/// List available Flutter devices.
Future<void> _devices() async {
  try {
    final result = await Process.run(
      'flutter',
      ['devices', '--machine'],
      environment: Platform.environment,
    );

    if (result.exitCode != 0) {
      stderr
        ..writeln('Error: flutter devices failed')
        ..writeln(result.stderr);
      exit(1);
    }

    // Parse the JSON output from flutter devices --machine
    final devicesJson = result.stdout.toString().trim();
    final devices = jsonDecode(devicesJson) as List<dynamic>;

    // Format the output
    final formattedDevices = devices.map((d) {
      final device = d as Map<String, dynamic>;
      return {
        'id': device['id'],
        'name': device['name'],
        'platform': device['targetPlatform'],
        'available': device['isSupported'] ?? true,
      };
    }).toList();

    final output = {
      'devices': formattedDevices,
    };

    print(jsonEncode(output));
  } catch (e) {
    stderr.writeln('Error listing devices: $e');
    exit(1);
  }
}

// ============================================================================
// Error Handling
// ============================================================================

/// Handles connection errors with actionable recovery instructions.
///
/// Detects the type of failure and provides specific recovery steps.
Never _handleConnectionError(Object error, String uri) {
  final errorStr = error.toString();

  // Connection refused - app not running or wrong port
  if (errorStr.contains('Connection refused') ||
      errorStr.contains('SocketException')) {
    stderr
      ..writeln('CONNECTION_REFUSED: Cannot connect to VM service')
      ..writeln('')
      ..writeln('The app may not be running or the URI is wrong.')
      ..writeln('')
      ..writeln('RECOVERY:')
      ..writeln('1. Check status: python ui.py status')
      ..writeln('2. If app crashed, relaunch: python ui.py launch')
      ..writeln('3. If URI stale, get logs: python ui.py logs')
      ..writeln('')
      ..writeln('DO NOT launch a new app if one is already running!');
    exit(2);
  }

  // WebSocket closed - URI is stale (app restarted or hot restarted)
  if (errorStr.contains('WebSocketChannelException') ||
      errorStr.contains('Connection closed') ||
      errorStr.contains('closed before')) {
    stderr
      ..writeln('CONNECTION_STALE: WebSocket connection closed')
      ..writeln('')
      ..writeln('The VM service URI is stale. The app may have restarted.')
      ..writeln('')
      ..writeln('RECOVERY:')
      ..writeln('1. Check logs for fresh URI: python ui.py logs')
      ..writeln('2. Update state: python ui.py reconnect')
      ..writeln('3. Or restart: python ui.py stop && python ui.py launch')
      ..writeln('')
      ..writeln('The app is likely still running - just need fresh URIs.');
    exit(3);
  }

  // Generic error - provide full details
  stderr
    ..writeln('CONNECTION_ERROR: $error')
    ..writeln('')
    ..writeln('URI used: $uri')
    ..writeln('')
    ..writeln('RECOVERY:')
    ..writeln('1. Check status: python ui.py status')
    ..writeln('2. Check logs: python ui.py logs')
    ..writeln('3. Restart if needed: python ui.py stop && python ui.py launch');
  exit(1);
}

/// Calls a service extension with timeout to prevent hanging.
Future<Response> _callWithTimeout(
  VmService vmService,
  String method,
  String isolateId, {
  Map<String, String>? args,
}) async {
  try {
    return await vmService
        .callServiceExtension(method, isolateId: isolateId, args: args)
        .timeout(_serviceCallTimeout);
  } on TimeoutException {
    stderr
      ..writeln('TIMEOUT: Service call timed out after $_serviceCallTimeout')
      ..writeln('')
      ..writeln('The app is connected but not responding.')
      ..writeln('Causes: app minimized, window unfocused, or in background.')
      ..writeln('')
      ..writeln('RECOVERY:')
      ..writeln('1. Focus the app window (bring to foreground)')
      ..writeln('2. If still failing, hot reload: python ui.py hot-reload')
      ..writeln('3. Or restart: python ui.py stop && python ui.py launch');
    exit(4);
  }
}

Future<void> _getElements(VmService vmService, String isolateId) async {
  final response = await _callWithTimeout(
    vmService,
    'ext.flutter.agent.getElements',
    isolateId,
  );
  // Service extension returns result directly in json
  final result = response.json;
  if (result != null) {
    // The result might be the direct JSON or wrapped in 'result'
    if (result.containsKey('result')) {
      print(result['result']);
    } else {
      print(jsonEncode(result));
    }
  } else {
    print('{}');
  }
}

Future<void> _tap(
  VmService vmService,
  String isolateId,
  ArgResults args,
) async {
  final params = <String, String>{};

  final id = args['id'] as String?;
  final x = args['x'] as String?;
  final y = args['y'] as String?;

  if (id != null) {
    params['id'] = id;
  } else if (x != null && y != null) {
    params['x'] = x;
    params['y'] = y;
  } else {
    stderr.writeln('Error: tap requires --id or (--x and --y)');
    exit(1);
  }

  final response = await _callWithTimeout(
    vmService,
    'ext.flutter.agent.tap',
    isolateId,
    args: params,
  );
  print(response.json?['result'] ?? '{"success": true}');
}

Future<void> _swipe(
  VmService vmService,
  String isolateId,
  ArgResults args,
) async {
  final id = args['id'] as String?;
  if (id == null) {
    stderr.writeln('Error: swipe requires --id');
    exit(1);
  }

  final params = <String, String>{
    'id': id,
    'direction': args['direction'] as String,
    'distance': args['distance'] as String,
  };

  final response = await _callWithTimeout(
    vmService,
    'ext.flutter.agent.swipe',
    isolateId,
    args: params,
  );
  print(response.json?['result'] ?? '{"success": true}');
}

Future<void> _longPress(
  VmService vmService,
  String isolateId,
  ArgResults args,
) async {
  final params = <String, String>{};

  final id = args['id'] as String?;
  final x = args['x'] as String?;
  final y = args['y'] as String?;

  if (id != null) {
    params['id'] = id;
  } else if (x != null && y != null) {
    params['x'] = x;
    params['y'] = y;
  } else {
    stderr.writeln('Error: longpress requires --id or (--x and --y)');
    exit(1);
  }

  final response = await _callWithTimeout(
    vmService,
    'ext.flutter.agent.longPress',
    isolateId,
    args: params,
  );
  print(response.json?['result'] ?? '{"success": true}');
}

/// Validates that the provided URI is a VM service URI, not a DTD URI.
///
/// VM service URIs end with `/ws` (e.g., `ws://127.0.0.1:52251/abc=/ws`)
/// DTD URIs do not have the `/ws` suffix (e.g., `ws://127.0.0.1:52250/abc=`)
///
/// The MCP `launch_app` tool returns the DTD URI directly, but this CLI
/// requires the VM service URI which comes from the `app.debugPort` event
/// in the app logs.
void _validateVmServiceUri(String uri) {
  // VM service URIs must end with /ws
  if (!uri.endsWith('/ws')) {
    stderr
      ..writeln('Error: Invalid URI type - expected VM service URI')
      ..writeln('')
      ..writeln(
        'You provided what appears to be a DTD (Dart Tooling Daemon) URI:',
      )
      ..writeln('  $uri')
      ..writeln('')
      ..writeln('This CLI requires the VM service URI, which:')
      ..writeln('  - Ends with /ws')
      ..writeln('  - Comes from the app.debugPort event in logs')
      ..writeln('  - Example: ws://127.0.0.1:52251/abc123=/ws')
      ..writeln('')
      ..writeln('To find the VM service URI:')
      ..writeln('  1. Check the app logs for "app.debugPort" event')
      ..writeln('  2. Look for a URI ending with /ws')
      ..writeln('  3. Or use: mcp__dart__get_app_logs to retrieve logs');
    exit(1);
  }

  // Basic websocket URI validation
  if (!uri.startsWith('ws://') && !uri.startsWith('wss://')) {
    stderr.writeln('Error: URI must start with ws:// or wss://');
    exit(1);
  }
}
