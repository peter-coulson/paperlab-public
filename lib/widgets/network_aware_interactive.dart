import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/services/connectivity_service.dart';
import 'package:paperlab/theme/app_effects.dart';

/// Network-aware wrapper for interactive elements.
///
/// Provides single source of truth for connectivity-based interaction control.
/// All buttons, list items, and interactive elements use this to enforce
/// network requirements consistently.
///
/// Features:
/// - Checks connectivity when requiresNetwork is true
/// - Auto-disables interaction when offline
/// - Uses AbsorbPointer to block touches when disabled
/// - Applies reduced opacity to disabled children
/// - Maintains InteractiveEffect behavior when enabled
///
/// DRY Principle:
/// This widget extracts connectivity checking logic into one place.
/// All interactive components (PrimaryButton, SecondaryButton,
/// ListItemContainer, AddButton) use this instead of duplicating checks.
///
/// Usage:
/// ```dart
/// NetworkAwareInteractive(
///   requiresNetwork: true,  // Required parameter
///   onTap: _handleSubmit,
///   child: Container(...),
/// )
/// ```
class NetworkAwareInteractive extends ConsumerWidget {
  const NetworkAwareInteractive({
    required this.requiresNetwork,
    required this.onTap,
    required this.child,
    this.disabled = false,
    super.key,
  });

  /// Whether this interaction requires network connectivity.
  /// REQUIRED parameter - must be explicitly set for every interactive element.
  /// - true: Auto-disables when offline (e.g., upload, submit, API calls)
  /// - false: Always enabled (e.g., navigation, local actions)
  final bool requiresNetwork;

  /// Callback when element is tapped (null also disables)
  final VoidCallback? onTap;

  /// Additional disabled state (independent of network)
  final bool disabled;

  /// Child widget to wrap with interactive effects
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Check connectivity if required
    final bool isOffline =
        requiresNetwork && !ref.read(connectivityServiceProvider).isOnline;

    // Determine final disabled state
    final bool isDisabled = disabled || onTap == null || isOffline;

    // Disabled state - block interaction and reduce opacity
    if (isDisabled) {
      return Opacity(opacity: 0.5, child: AbsorbPointer(child: child));
    }

    // Enabled state - wrap with InteractiveEffect
    return InteractiveEffect(onTap: onTap!, child: child);
  }
}
