import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Shared interaction effects for buttons, cards, and interactive elements.
///
/// Mobile-first design: consistent press feedback and static shadows
/// across the app. When effects need to change, update here and all
/// components stay synchronized.
class AppEffects {
  // Private constructor to prevent instantiation
  AppEffects._();
  // Animation durations
  /// Duration for press/active state transitions (scale animations)
  static const Duration pressDuration = Duration(milliseconds: 100);

  /// Duration for delete animations (slide-out, fade, collapse)
  static const Duration deleteDuration = Duration(milliseconds: 300);

  /// Duration for undo snackbar display (time user has to undo deletion)
  static const Duration undoDuration = Duration(seconds: 5);

  /// Animation curve for smooth, professional transitions
  static const Curve animationCurve = Curves.easeOut;

  // Interaction states
  /// Scale factor when element is pressed (0.98 = 98% of original size)
  static const double pressedScale = 0.98;

  // Border configuration
  /// Standard border width for all interactive elements
  /// (buttons, cards, list items)
  /// Using 1px creates clean, refined appearance without visual heaviness
  static const double borderWidth = 1.0;

  /// Stroke alignment for borders - ensures borders draw inside element bounds
  /// Prevents layout shifts and maintains consistent sizing
  static const double strokeAlignInside = BorderSide.strokeAlignInside;

  // Shadow configuration - consistent depth and color across all components
  // Multi-layer shadows create premium depth following real-world physics
  // Two shadows: sharp close shadow + soft far shadow = natural elevation

  /// Multi-layer neutral shadows for all interactive elements
  /// (list items, buttons, cards)
  /// Uses two-shadow system for richer depth:
  /// - Primary shadow: Sharp, close (defines edge)
  /// - Secondary shadow: Soft, far (creates ambient depth)
  ///
  /// Static shadows - no animation on mobile for performance
  /// and simplicity
  static List<BoxShadow> get shadow => [
    // Primary shadow - sharp, close to surface
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.08),
      blurRadius: 6.0,
      offset: const Offset(0, 2),
    ),
    // Secondary shadow - soft, farther from surface
    BoxShadow(
      color: Colors.black.withValues(alpha: 0.04),
      blurRadius: 12.0,
      offset: const Offset(0, 4),
    ),
  ];
}

/// Wrapper widget that applies consistent press feedback to interactive
/// elements.
///
/// Mobile-first design philosophy:
/// - Immediate visual + haptic feedback (Listener + HapticFeedback)
/// - Scale animation on press (AnimatedScale)
/// - Clean, minimal interactions without Material Design ripples
/// - Matches modern mobile aesthetics (Gmail, iOS Mail, Telegram)
///
/// Implementation:
/// - Listener: Detects raw pointer events for instant feedback (no gesture
///   disambiguation delay)
/// - HapticFeedback: Provides tactile response on touch down
/// - GestureDetector: Handles tap action after gesture disambiguation
/// - AnimatedScale: Provides visual press feedback
///
/// This architecture ensures instant visual/haptic response even when
/// wrapped in gesture-competing widgets like Slidable, while still
/// properly handling tap actions after disambiguation.
///
/// Shadows and decorations should be applied directly to child widgets,
/// not animated, for optimal performance and to prevent clipping issues.
///
/// Use this to wrap interactive elements that need press feedback.
class InteractiveEffect extends StatefulWidget {
  const InteractiveEffect({
    required this.onTap,
    required this.child,
    super.key,
  });

  final VoidCallback onTap;
  final Widget child;

  @override
  State<InteractiveEffect> createState() => _InteractiveEffectState();
}

class _InteractiveEffectState extends State<InteractiveEffect> {
  bool _isPressed = false;
  DateTime? _lastTapTime;

  // Debounce duration to prevent double-taps (especially during navigation)
  static const _debounceDuration = Duration(milliseconds: 500);

  void _handleTap() {
    final now = DateTime.now();

    // Ignore taps that occur too quickly after the previous tap
    if (_lastTapTime != null &&
        now.difference(_lastTapTime!) < _debounceDuration) {
      return;
    }

    _lastTapTime = now;
    widget.onTap();
  }

  @override
  Widget build(BuildContext context) => Listener(
    // Listener callbacks fire immediately on raw pointer events
    // (before gesture disambiguation), ensuring instant visual + haptic
    // feedback
    onPointerDown: (_) {
      // Haptic feedback provides tactile response (works on iOS/Android,
      // silently fails on web)
      HapticFeedback.lightImpact();
      setState(() => _isPressed = true);
    },
    onPointerUp: (_) => setState(() => _isPressed = false),
    onPointerCancel: (_) => setState(() => _isPressed = false),
    child: GestureDetector(
      // GestureDetector handles the tap action after disambiguation
      // (e.g., when competing with Slidable's horizontal drag)
      // Debounced to prevent double-taps during navigation
      onTap: _handleTap,
      child: AnimatedScale(
        scale: _isPressed ? AppEffects.pressedScale : 1.0,
        duration: AppEffects.pressDuration,
        curve: AppEffects.animationCurve,
        child: widget.child,
      ),
    ),
  );
}
