/// Integration tests for the agent interaction system.
///
/// These tests verify that the agent interaction extensions can:
/// 1. Discover interactive elements on screen
/// 2. Execute tap gestures by element ID
/// 3. Execute swipe gestures on slidable elements
///
/// Run with: fvm flutter test integration_test/agent_interaction_test.dart
library;
// ignore_for_file: avoid_print

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:paperlab/driver/agent_interaction.dart';
import 'package:paperlab/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Agent Interaction System', () {
    testWidgets('discovers interactive elements on home screen', (
      tester,
    ) async {
      // Launch the app
      await tester.pumpWidget(const ProviderScope(child: PaperLabApp()));

      // Wait for app to settle (loading, network calls, etc.)
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Get interactive elements
      final elements = getInteractiveElements();

      // Print discovered elements for debugging
      print('\n=== Discovered ${elements.length} interactive elements ===');
      for (final element in elements) {
        print(
          '  [${element.id}] ${element.type}: "${element.description}" '
          'at (${element.bounds.left.round()}, ${element.bounds.top.round()}) '
          'gestures: ${element.gestures}',
        );
      }
      print('=== End of elements ===\n');

      // Verify we found some elements
      expect(elements, isNotEmpty, reason: 'Should find interactive elements');

      // Verify element structure
      for (final element in elements) {
        expect(element.id, greaterThanOrEqualTo(0));
        expect(element.type, isNotEmpty);
        expect(element.description, isNotEmpty);
        expect(element.bounds.width, greaterThan(0));
        expect(element.bounds.height, greaterThan(0));
        expect(element.gestures, isNotEmpty);
      }

      // Verify we have expected element types on home screen
      final types = elements.map((e) => e.type).toSet();
      print('Element types found: $types');

      // Should have at least buttons or interactive elements
      expect(
        types.intersection({
          'button',
          'icon_button',
          'interactive',
          'list_item',
          'slidable',
        }).isNotEmpty,
        isTrue,
        reason: 'Should find at least one button or interactive element',
      );
    });

    testWidgets('elements are sorted visually (top-to-bottom, left-to-right)', (
      tester,
    ) async {
      await tester.pumpWidget(const ProviderScope(child: PaperLabApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      final elements = getInteractiveElements();

      // Verify sorting: each element should be below or right of previous
      for (var i = 1; i < elements.length; i++) {
        final prev = elements[i - 1];
        final curr = elements[i];

        // Either same row (within 20px) and to the right, or below
        final sameRow = (curr.bounds.top - prev.bounds.top).abs() < 20;
        if (sameRow) {
          expect(
            curr.bounds.left,
            greaterThanOrEqualTo(prev.bounds.left - 1), // Allow 1px tolerance
            reason:
                'Element $i should be to the right of element ${i - 1} '
                'on same row',
          );
        } else {
          expect(
            curr.bounds.top,
            greaterThanOrEqualTo(prev.bounds.top),
            reason: 'Element $i should be below element ${i - 1}',
          );
        }
      }
    });

    testWidgets('tapAt simulates tap gesture', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: PaperLabApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      final elements = getInteractiveElements();
      expect(elements, isNotEmpty);

      // Find a tappable element (prefer a button or interactive element)
      final tappable = elements.firstWhere(
        (e) => e.gestures.contains('tap'),
        orElse: () => elements.first,
      );

      print(
        'Tapping element: ${tappable.description} at ${tappable.bounds.center}',
      );

      // Tap at the center of the element
      await tapAt(tappable.bounds.center.dx, tappable.bounds.center.dy);

      // Allow time for tap to be processed
      await tester.pump(const Duration(milliseconds: 100));
      await tester.pumpAndSettle();

      // The tap was executed without throwing
      // (actual navigation/state change depends on which element was tapped)
      print('Tap executed successfully');
    });

    testWidgets('swipeAt simulates swipe gesture', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: PaperLabApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      final elements = getInteractiveElements();

      // Find a slidable element
      final slidable = elements.where((e) => e.gestures.contains('swipe_left'));

      if (slidable.isEmpty) {
        print('No slidable elements found, skipping swipe test');
        return;
      }

      final element = slidable.first;
      print('Swiping left on: ${element.description}');

      // Perform swipe
      await swipeAt(
        element.bounds.center.dx,
        element.bounds.center.dy,
        'left',
        distance: 100,
      );

      // Allow time for swipe animation
      await tester.pump(const Duration(milliseconds: 200));
      await tester.pumpAndSettle();

      print('Swipe executed successfully');
    });

    testWidgets('JSON output is concise and complete', (tester) async {
      await tester.pumpWidget(const ProviderScope(child: PaperLabApp()));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      final elements = getInteractiveElements();
      expect(elements, isNotEmpty);

      // Test JSON serialization
      final element = elements.first;
      final json = element.toJson();

      print('Sample JSON output: $json');

      // Verify JSON structure
      expect(json['id'], isA<int>());
      expect(json['type'], isA<String>());
      expect(json['desc'], isA<String>());
      expect(json['x'], isA<int>());
      expect(json['y'], isA<int>());
      expect(json['w'], isA<int>());
      expect(json['h'], isA<int>());
      expect(json['gestures'], isA<List>());

      // Verify concise key names
      expect(
        json.containsKey('desc'),
        isTrue,
        reason: 'Should use short key "desc"',
      );
      expect(
        json.containsKey('description'),
        isFalse,
        reason: 'Should not use long key',
      );
    });
  });
}
