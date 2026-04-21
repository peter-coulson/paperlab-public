/// Agent interaction system for AI-driven UI automation.
///
/// Provides service extensions for AI agents to discover and interact with
/// UI elements visually. Agents can query interactive elements, get their
/// screen bounds, and perform gestures (tap, swipe, long press).
///
/// Service extensions (debug mode only):
/// - `ext.flutter.agent.getElements` - Returns JSON list of elements
/// - `ext.flutter.agent.tap` - Tap by element ID or coordinates
/// - `ext.flutter.agent.swipe` - Swipe on element by ID and direction
/// - `ext.flutter.agent.longPress` - Long press by element ID or coordinates
///
/// Usage:
/// 1. Call registerAgentExtensions() after enableFlutterDriverExtension()
/// 2. Connect to the VM service and call extensions via JSON-RPC
///
/// All functionality is tree-shaken in release builds via kDebugMode guards.
library;

import 'dart:convert';
import 'dart:developer';

import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart'
    show
        GestureBinding,
        PointerAddedEvent,
        PointerDeviceKind,
        PointerRemovedEvent;
import 'package:flutter/material.dart';

// Element types for interactive widgets
const String _typeButton = 'button';
const String _typeIconButton = 'icon_button';
const String _typeListItem = 'list_item';
const String _typeTextField = 'text_field';
const String _typeSlidable = 'slidable';
const String _typeInteractive = 'interactive';

// Gesture types
const String _gestureTap = 'tap';
const String _gestureSwipe = 'swipe_left';
const String _gestureSwipeRight = 'swipe_right';
const String _gestureLongPress = 'long_press';

// Swipe configuration
const double _defaultSwipeDistance = 150.0;
const int _swipeSteps = 10;
const Duration _swipeStepDuration = Duration(milliseconds: 16);

// Long press configuration
const Duration _defaultLongPressDuration = Duration(milliseconds: 500);

// Pointer ID counter - auto-increments to avoid conflicts
int _nextPointerId = 1;

/// Model for discovered interactive UI elements.
///
/// Contains all information needed for agents to understand and
/// interact with UI elements visually.
class InteractiveElement {
  /// Creates an interactive element.
  const InteractiveElement({
    required this.id,
    required this.type,
    required this.description,
    required this.bounds,
    required this.gestures,
  });

  /// Unique identifier for this element (sequential, sorted by position).
  final int id;

  /// Widget type category: "button", "list_item", "text_field",
  /// "icon_button", "slidable", "interactive".
  final String type;

  /// Human-readable description extracted from widget content.
  final String description;

  /// Screen bounds (position and size) for visual reference.
  final Rect bounds;

  /// Supported gestures: ["tap"], ["tap", "swipe_left"], etc.
  final List<String> gestures;

  /// Convert to JSON for agent consumption.
  ///
  /// Output is kept concise to minimize token usage.
  Map<String, dynamic> toJson() => {
    'id': id,
    'type': type,
    'desc': description,
    'x': bounds.left.round(),
    'y': bounds.top.round(),
    'w': bounds.width.round(),
    'h': bounds.height.round(),
    'gestures': gestures,
  };
}

/// Walks the Element tree to find interactive widgets.
///
/// Returns a list of [InteractiveElement] sorted visually
/// (top-to-bottom, left-to-right) with sequential IDs.
///
/// Only elements that are at least partially visible within the viewport
/// are returned. Off-screen elements (from previous navigation routes)
/// are filtered out.
///
/// Detected widget types:
/// - GestureDetector (with onTap or onLongPress)
/// - Listener (with onPointerDown)
/// - InteractiveEffect (custom app widget)
/// - NetworkAwareInteractive (custom app widget)
/// - Slidable (flutter_slidable package)
/// - TextField, TextFormField
/// - Standard Material buttons (ElevatedButton, TextButton, etc.)
List<InteractiveElement> getInteractiveElements() {
  if (!kDebugMode) return [];

  final elements = <_RawElement>[];
  final rootElement = WidgetsBinding.instance.rootElement;

  if (rootElement == null) return [];

  // Get the viewport bounds for filtering off-screen elements
  final viewportBounds = _getViewportBounds();

  _walkTree(rootElement, elements);

  // Filter out elements that are outside the visible viewport
  // This excludes elements from previous navigation routes that are off-screen
  final visible = elements
      .where((e) => _isVisibleInViewport(e.bounds, viewportBounds))
      .toList();

  // Deduplicate elements with same/similar bounds
  // Keep the one with the best description (most specific type or longest desc)
  final deduped = <_RawElement>[];
  for (final element in visible) {
    final existingIndex = deduped.indexWhere(
      (e) => _boundsOverlap(e.bounds, element.bounds),
    );
    if (existingIndex == -1) {
      deduped.add(element);
    } else {
      // Keep the better one (prefer specific types, then longer description)
      final existing = deduped[existingIndex];
      if (_isBetterElement(element, existing)) {
        deduped[existingIndex] = element;
      }
    }
  }

  // Sort visually: top-to-bottom, then left-to-right
  deduped.sort((a, b) {
    final yDiff = a.bounds.top.compareTo(b.bounds.top);
    if (yDiff != 0) return yDiff;
    return a.bounds.left.compareTo(b.bounds.left);
  });

  // Assign sequential IDs
  return deduped.asMap().entries.map((entry) {
    final raw = entry.value;
    return InteractiveElement(
      id: entry.key,
      type: raw.type,
      description: raw.description,
      bounds: raw.bounds,
      gestures: raw.gestures,
    );
  }).toList();
}

/// Gets the visible viewport bounds (screen size).
Rect _getViewportBounds() {
  final view = WidgetsBinding.instance.platformDispatcher.views.first;
  final size = view.physicalSize / view.devicePixelRatio;
  return Offset.zero & size;
}

/// Checks if an element is visible within the viewport.
///
/// Elements must start within the viewport bounds to be considered visible.
/// This filters out elements from previous navigation routes that are
/// positioned off-screen (e.g., x < 0 from pages that slid left).
bool _isVisibleInViewport(Rect elementBounds, Rect viewportBounds) {
  // Element starts off-screen to the left (e.g., previous page in navigation)
  if (elementBounds.left < 0) return false;

  // Element starts off-screen to the top
  if (elementBounds.top < 0) return false;

  // Element starts off-screen to the right
  if (elementBounds.left >= viewportBounds.width) return false;

  // Element starts off-screen to the bottom
  if (elementBounds.top >= viewportBounds.height) return false;

  // Element starts within viewport
  return true;
}

/// Check if two bounds significantly overlap (same clickable area).
bool _boundsOverlap(Rect a, Rect b) {
  // Check if centers are within 20px
  final centerDist = (a.center - b.center).distance;
  if (centerDist < 20) return true;

  // Check if one contains the other
  if (a.contains(b.center) || b.contains(a.center)) {
    // Same general area - check overlap percentage
    final intersection = a.intersect(b);
    if (intersection.isEmpty) return false;
    final overlapArea = intersection.width * intersection.height;
    final smallerArea = (a.width * a.height).compareTo(b.width * b.height) < 0
        ? a.width * a.height
        : b.width * b.height;
    return overlapArea / smallerArea > 0.7; // 70% overlap
  }

  return false;
}

/// Determine if newElement is better than existing for deduplication.
bool _isBetterElement(_RawElement newElement, _RawElement existing) {
  // Prefer smaller elements - they're more specific targets
  // A child element is almost always better than its container
  final newArea = newElement.bounds.width * newElement.bounds.height;
  final existingArea = existing.bounds.width * existing.bounds.height;

  // If one is significantly smaller (less than 50% area), prefer it
  if (newArea < existingArea * 0.5) return true;
  if (existingArea < newArea * 0.5) return false;

  // Prefer specific types over generic "interactive"
  const typeRank = {
    'button': 5,
    'icon_button': 5,
    'text_field': 5,
    'slidable': 4,
    'list_item': 3,
    'interactive': 1,
  };

  final newRank = typeRank[newElement.type] ?? 0;
  final existingRank = typeRank[existing.type] ?? 0;

  if (newRank != existingRank) {
    return newRank > existingRank;
  }

  // Prefer more gestures
  if (newElement.gestures.length != existing.gestures.length) {
    return newElement.gestures.length > existing.gestures.length;
  }

  // Prefer longer/more specific descriptions
  return newElement.description.length > existing.description.length;
}

/// Internal representation before ID assignment.
class _RawElement {
  _RawElement({
    required this.type,
    required this.description,
    required this.bounds,
    required this.gestures,
  });

  final String type;
  final String description;
  final Rect bounds;
  final List<String> gestures;
}

/// Recursively walks the widget tree to find interactive elements.
void _walkTree(Element element, List<_RawElement> results) {
  final widget = element.widget;

  // Find the nearest RenderBox for this element
  RenderBox? renderBox;
  RenderObject? ro = element.renderObject;
  while (ro != null && ro is! RenderBox) {
    ro = ro.parent;
  }
  if (ro is RenderBox && ro.hasSize && ro.attached) {
    renderBox = ro;
  }

  // Check if element has valid, reasonably-sized bounds
  Rect? bounds;
  if (renderBox != null) {
    try {
      final transform = renderBox.getTransformTo(null);
      final translation = transform.getTranslation();
      bounds = Offset(translation.x, translation.y) & renderBox.size;

      // Skip elements that are too small
      if (bounds.width < 10 || bounds.height < 10) {
        bounds = null;
      }
      // Skip elements that are too large (likely containers, not buttons)
      // Individual interactive elements are typically constrained in at least
      // one dimension (e.g., wide button is short, tall list item is narrow)
      if (bounds != null) {
        // Elements that are both wide AND tall are containers, not buttons
        // Max reasonable: 500 wide OR 150 tall, but not both large
        final isTooWide = bounds.width > 500;
        final isTooTall = bounds.height > 150;
        if (isTooWide && isTooTall) {
          bounds = null;
        }
      }
    } catch (_) {
      bounds = null;
    }
  }

  // Try to detect interactive widget
  if (bounds != null) {
    final rawElement = _detectInteractiveWidget(element, widget, bounds);
    if (rawElement != null) {
      results.add(rawElement);
      // Still recurse to find nested elements (e.g., icons in buttons)
    }
  }

  // Always continue walking children
  element.visitChildren((child) => _walkTree(child, results));
}

/// Detects if a widget is interactive and extracts its properties.
_RawElement? _detectInteractiveWidget(
  Element element,
  Widget widget,
  Rect bounds,
) {
  final typeName = widget.runtimeType.toString();

  // InteractiveEffect (custom app widget)
  if (typeName == 'InteractiveEffect') {
    return _RawElement(
      type: _typeInteractive,
      description: _findDescription(element) ?? 'Interactive element',
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // NetworkAwareInteractive (custom app widget)
  if (typeName == 'NetworkAwareInteractive') {
    return _RawElement(
      type: _typeInteractive,
      description: _findDescription(element) ?? 'Network-aware element',
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // Slidable (flutter_slidable package)
  if (typeName.contains('Slidable')) {
    return _RawElement(
      type: _typeSlidable,
      description: _findDescription(element) ?? 'Slidable item',
      bounds: bounds,
      gestures: [_gestureTap, _gestureSwipe, _gestureSwipeRight],
    );
  }

  // TextField / TextFormField
  if (widget is TextField || widget is TextFormField) {
    String hint = 'Text field';
    if (widget is TextField && widget.decoration?.hintText != null) {
      hint = widget.decoration!.hintText!;
    }
    // TextFormField doesn't expose decoration directly
    return _RawElement(
      type: _typeTextField,
      description: hint,
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // Material buttons
  if (widget is ElevatedButton ||
      widget is TextButton ||
      widget is OutlinedButton ||
      widget is FilledButton) {
    return _RawElement(
      type: _typeButton,
      description: _findDescription(element) ?? 'Button',
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // IconButton
  if (widget is IconButton) {
    final tooltip = widget.tooltip;
    final description =
        tooltip ?? _findIconDescription(element) ?? 'Icon button';
    return _RawElement(
      type: _typeIconButton,
      description: description,
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // FloatingActionButton
  if (widget is FloatingActionButton) {
    final tooltip = widget.tooltip;
    return _RawElement(
      type: _typeButton,
      description: tooltip ?? _findDescription(element) ?? 'Floating button',
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // GestureDetector with tap or long press
  if (widget is GestureDetector) {
    final hasOnTap = widget.onTap != null;
    final hasOnLongPress = widget.onLongPress != null;

    if (hasOnTap || hasOnLongPress) {
      final gestures = <String>[];
      if (hasOnTap) gestures.add(_gestureTap);
      if (hasOnLongPress) gestures.add(_gestureLongPress);

      return _RawElement(
        type: _typeInteractive,
        description: _findDescription(element) ?? 'Gesture detector',
        bounds: bounds,
        gestures: gestures,
      );
    }
  }

  // Listener with pointer down
  if (widget is Listener && widget.onPointerDown != null) {
    return _RawElement(
      type: _typeInteractive,
      description: _findDescription(element) ?? 'Listener',
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // InkWell / InkResponse
  if (widget is InkWell && widget.onTap != null) {
    final gestures = <String>[_gestureTap];
    if (widget.onLongPress != null) gestures.add(_gestureLongPress);

    return _RawElement(
      type: _typeListItem,
      description: _findDescription(element) ?? 'Ink well',
      bounds: bounds,
      gestures: gestures,
    );
  }

  if (widget is InkResponse && widget.onTap != null) {
    return _RawElement(
      type: _typeInteractive,
      description: _findDescription(element) ?? 'Ink response',
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  // ListTile
  if (widget is ListTile && widget.onTap != null) {
    final title = widget.title;
    String desc = 'List tile';
    if (title is Text && title.data != null) {
      desc = title.data!;
    }
    return _RawElement(
      type: _typeListItem,
      description: desc,
      bounds: bounds,
      gestures: [_gestureTap],
    );
  }

  return null;
}

/// Finds a text description by searching the element's subtree.
String? _findDescription(Element element) {
  String? found;

  void visit(Element child) {
    if (found != null) return;

    final widget = child.widget;

    // Check for Text widget
    if (widget is Text && widget.data != null && widget.data!.isNotEmpty) {
      found = widget.data;
      return;
    }

    // Check for Icon
    if (widget is Icon) {
      found = _getIconDescription(widget);
      return;
    }

    child.visitChildren(visit);
  }

  element.visitChildren(visit);
  return found;
}

/// Finds an icon description in the element's subtree.
String? _findIconDescription(Element element) {
  String? found;

  void visit(Element child) {
    if (found != null) return;

    final widget = child.widget;
    if (widget is Icon) {
      found = _getIconDescription(widget);
      return;
    }

    child.visitChildren(visit);
  }

  element.visitChildren(visit);
  return found;
}

/// Gets a description for an Icon widget.
///
/// Attempts to identify common Material icons by codepoint,
/// falls back to semantic label or "Icon".
String _getIconDescription(Icon icon) {
  // Use semantic label if available
  if (icon.semanticLabel != null) {
    return icon.semanticLabel!;
  }

  // Try to identify common icons by codepoint
  final iconData = icon.icon;
  if (iconData != null) {
    final codePoint = iconData.codePoint;

    // Common Material Design icons
    const iconNames = <int, String>{
      0xe145: 'Add',
      0xe15b: 'Remove',
      0xe872: 'Delete',
      0xe5cd: 'Close',
      0xe5c4: 'Back',
      0xe5c8: 'Forward',
      0xe8b8: 'Settings',
      0xe88a: 'Home',
      0xe8b6: 'Search',
      0xe7fd: 'Person',
      0xe8e5: 'Edit',
      0xe161: 'Send',
      0xe2c7: 'Refresh',
      0xe876: 'Check',
      0xe5ca: 'Done',
      0xe5ce: 'Error',
      0xe002: 'Info',
      0xe924: 'Menu',
      0xe5d2: 'More',
    };

    final name = iconNames[codePoint];
    if (name != null) return '$name icon';
  }

  return 'Icon';
}

// ============================================================================
// Gesture Functions
// ============================================================================

/// Simulates a tap at the given screen coordinates.
///
/// Uses proper pointer event lifecycle with timestamps to ensure
/// gesture recognition works correctly with GestureDetector widgets.
///
/// Key fixes for gesture arena stability:
/// 1. Auto-incrementing pointer IDs to avoid conflicts
/// 2. Full pointer lifecycle (Added -> Down -> Up -> Removed)
/// 3. Explicit device kind and ID for proper routing
/// 4. Frame synchronization using endOfFrame
/// 5. Force gesture arena sweep after completion
/// 6. Animation settlement wait
Future<void> tapAt(double x, double y) async {
  if (!kDebugMode) return;

  final binding = WidgetsBinding.instance;
  final position = Offset(x, y);

  // Use strictly auto-incrementing pointer ID to avoid conflicts.
  final pointer = _nextPointerId++;

  // Use a consistent device ID for all synthetic events
  const device = 0;

  final now = DateTime.now().millisecondsSinceEpoch;

  // Step 1: Add the pointer (simulates device connection)
  // This is important for proper pointer routing setup
  binding.handlePointerEvent(
    PointerAddedEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now),
    ),
  );

  // Step 2: Pointer down - starts the gesture
  binding.handlePointerEvent(
    PointerDownEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now + 1),
      pressure: 1.0,
      pressureMax: 1.0,
    ),
  );

  // Wait for the down event to be fully processed (with timeout fallback)
  await Future.any([
    binding.endOfFrame,
    Future<void>.delayed(const Duration(milliseconds: 100)),
  ]);

  // Small delay to simulate realistic tap timing
  await Future<void>.delayed(const Duration(milliseconds: 50));

  // Step 3: Pointer up - completes the gesture
  binding.handlePointerEvent(
    PointerUpEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now + 51),
    ),
  );

  // Step 4: Remove the pointer (simulates device disconnection)
  // This ensures clean pointer state for next gesture
  binding.handlePointerEvent(
    PointerRemovedEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now + 52),
    ),
  );

  // Step 5: Force the gesture arena to sweep and resolve any pending gestures
  // This prevents the arena from getting stuck waiting for gesture resolution
  GestureBinding.instance.gestureArena.sweep(pointer);

  // Step 6: Wait for animations to settle
  await _waitForAnimationsToSettle();
}

/// Waits for animations to settle after a gesture.
///
/// Uses a timeout on endOfFrame to prevent hanging when the app isn't
/// actively rendering frames (e.g., minimized, unfocused).
Future<void> _waitForAnimationsToSettle() async {
  final binding = WidgetsBinding.instance;
  const frameTimeout = Duration(milliseconds: 500);

  // Wait for up to 3 frames, with timeout fallback
  for (var i = 0; i < 3; i++) {
    await Future.any([binding.endOfFrame, Future<void>.delayed(frameTimeout)]);
  }

  // Brief delay for UI to stabilize
  await Future<void>.delayed(const Duration(milliseconds: 50));
}

/// Simulates a swipe gesture from the given coordinates.
///
/// [direction] should be "left", "right", "up", or "down".
/// [distance] is the swipe distance in logical pixels (default: 150).
Future<void> swipeAt(
  double x,
  double y,
  String direction, {
  double distance = _defaultSwipeDistance,
}) async {
  if (!kDebugMode) return;

  final binding = WidgetsBinding.instance;
  final start = Offset(x, y);

  final pointer = _nextPointerId++;
  const device = 0;
  final now = DateTime.now().millisecondsSinceEpoch;

  // Calculate end position based on direction
  final Offset delta;
  switch (direction.toLowerCase()) {
    case 'left':
      delta = Offset(-distance, 0);
    case 'right':
      delta = Offset(distance, 0);
    case 'up':
      delta = Offset(0, -distance);
    case 'down':
      delta = Offset(0, distance);
    default:
      delta = Offset(-distance, 0);
  }

  // Add pointer
  binding.handlePointerEvent(
    PointerAddedEvent(
      position: start,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now),
    ),
  );

  // Start the swipe
  binding.handlePointerEvent(
    PointerDownEvent(
      position: start,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now + 1),
      pressure: 1.0,
      pressureMax: 1.0,
    ),
  );

  // Animate through steps
  for (var i = 1; i <= _swipeSteps; i++) {
    await Future<void>.delayed(_swipeStepDuration);
    final progress = i / _swipeSteps;
    final current = start + delta * progress;
    binding.handlePointerEvent(
      PointerMoveEvent(
        position: current,
        pointer: pointer,
        device: device,
        kind: PointerDeviceKind.touch,
        delta: delta / _swipeSteps.toDouble(),
        timeStamp: Duration(milliseconds: now + 1 + (16 * i)),
        pressure: 1.0,
        pressureMax: 1.0,
      ),
    );
  }

  final endTime = now + 1 + (16 * (_swipeSteps + 1));

  // End the swipe
  binding.handlePointerEvent(
    PointerUpEvent(
      position: start + delta,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: endTime),
    ),
  );

  // Remove pointer
  binding.handlePointerEvent(
    PointerRemovedEvent(
      position: start + delta,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: endTime + 1),
    ),
  );

  // Force arena sweep
  GestureBinding.instance.gestureArena.sweep(pointer);

  await _waitForAnimationsToSettle();
}

/// Simulates a long press at the given screen coordinates.
///
/// [duration] is the press duration (default: 500ms).
Future<void> longPressAt(
  double x,
  double y, {
  Duration duration = _defaultLongPressDuration,
}) async {
  if (!kDebugMode) return;

  final binding = WidgetsBinding.instance;
  final position = Offset(x, y);

  final pointer = _nextPointerId++;
  const device = 0;
  final now = DateTime.now().millisecondsSinceEpoch;

  // Add pointer
  binding.handlePointerEvent(
    PointerAddedEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now),
    ),
  );

  // Down event
  binding.handlePointerEvent(
    PointerDownEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: now + 1),
      pressure: 1.0,
      pressureMax: 1.0,
    ),
  );

  await Future<void>.delayed(duration);

  final endTime = now + 1 + duration.inMilliseconds;

  // Up event
  binding.handlePointerEvent(
    PointerUpEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: endTime),
    ),
  );

  // Remove pointer
  binding.handlePointerEvent(
    PointerRemovedEvent(
      position: position,
      pointer: pointer,
      device: device,
      kind: PointerDeviceKind.touch,
      timeStamp: Duration(milliseconds: endTime + 1),
    ),
  );

  // Force arena sweep
  GestureBinding.instance.gestureArena.sweep(pointer);

  await _waitForAnimationsToSettle();
}

// ============================================================================
// Service Extension Registration
// ============================================================================

/// Cached list of elements for gesture operations.
List<InteractiveElement>? _cachedElements;

/// Gets the center point of an element by ID.
Offset? _getElementCenter(int id) {
  _cachedElements ??= getInteractiveElements();
  if (id < 0 || id >= _cachedElements!.length) return null;
  return _cachedElements![id].bounds.center;
}

/// Registers service extensions for agent interaction.
///
/// Must be called in debug mode after enableFlutterDriverExtension().
///
/// Extensions:
/// - `ext.flutter.agent.getElements` - Get all interactive elements as JSON
/// - `ext.flutter.agent.tap` - Tap by {id} or {x, y}
/// - `ext.flutter.agent.swipe` - Swipe by {id, direction} or {x, y, direction}
/// - `ext.flutter.agent.longPress` - Long press by {id} or {x, y}
void registerAgentExtensions() {
  if (!kDebugMode) return;

  // Get interactive elements
  registerExtension('ext.flutter.agent.getElements', (method, params) async {
    _cachedElements = getInteractiveElements();
    final json = _cachedElements!.map((e) => e.toJson()).toList();
    return ServiceExtensionResponse.result(jsonEncode({'elements': json}));
  });

  // Tap gesture
  registerExtension('ext.flutter.agent.tap', (method, params) async {
    double? x;
    double? y;

    // Support tap by ID
    if (params.containsKey('id')) {
      final id = int.tryParse(params['id'] ?? '');
      if (id != null) {
        final center = _getElementCenter(id);
        if (center != null) {
          x = center.dx;
          y = center.dy;
        }
      }
    }

    // Support tap by coordinates
    x ??= double.tryParse(params['x'] ?? '');
    y ??= double.tryParse(params['y'] ?? '');

    if (x == null || y == null) {
      return ServiceExtensionResponse.error(
        ServiceExtensionResponse.invalidParams,
        'Missing required parameters: id or (x, y)',
      );
    }

    await tapAt(x, y);
    // Clear cache after interaction (UI may have changed)
    _cachedElements = null;
    return ServiceExtensionResponse.result(jsonEncode({'success': true}));
  });

  // Swipe gesture
  registerExtension('ext.flutter.agent.swipe', (method, params) async {
    double? x;
    double? y;
    final direction = params['direction'] ?? 'left';

    // Support swipe by ID
    if (params.containsKey('id')) {
      final id = int.tryParse(params['id'] ?? '');
      if (id != null) {
        final center = _getElementCenter(id);
        if (center != null) {
          x = center.dx;
          y = center.dy;
        }
      }
    }

    // Support swipe by coordinates
    x ??= double.tryParse(params['x'] ?? '');
    y ??= double.tryParse(params['y'] ?? '');

    if (x == null || y == null) {
      return ServiceExtensionResponse.error(
        ServiceExtensionResponse.invalidParams,
        'Missing required parameters: id or (x, y)',
      );
    }

    final distance =
        double.tryParse(params['distance'] ?? '') ?? _defaultSwipeDistance;
    await swipeAt(x, y, direction, distance: distance);
    // Clear cache after interaction (UI may have changed)
    _cachedElements = null;
    return ServiceExtensionResponse.result(jsonEncode({'success': true}));
  });

  // Long press gesture
  registerExtension('ext.flutter.agent.longPress', (method, params) async {
    double? x;
    double? y;

    // Support long press by ID
    if (params.containsKey('id')) {
      final id = int.tryParse(params['id'] ?? '');
      if (id != null) {
        final center = _getElementCenter(id);
        if (center != null) {
          x = center.dx;
          y = center.dy;
        }
      }
    }

    // Support long press by coordinates
    x ??= double.tryParse(params['x'] ?? '');
    y ??= double.tryParse(params['y'] ?? '');

    if (x == null || y == null) {
      return ServiceExtensionResponse.error(
        ServiceExtensionResponse.invalidParams,
        'Missing required parameters: id or (x, y)',
      );
    }

    final durationMs = int.tryParse(params['duration'] ?? '');
    final duration = durationMs != null
        ? Duration(milliseconds: durationMs)
        : _defaultLongPressDuration;

    await longPressAt(x, y, duration: duration);
    // Clear cache after interaction (UI may have changed)
    _cachedElements = null;
    return ServiceExtensionResponse.result(jsonEncode({'success': true}));
  });

  debugPrint('[Agent] Registered agent interaction extensions');
}
