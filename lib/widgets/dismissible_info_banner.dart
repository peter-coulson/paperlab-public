import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/widgets/info_banner.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Info banner with automatic dismissal persistence via SharedPreferences.
///
/// Shows banner on first load, then hides permanently after user dismisses.
/// Returns [SizedBox.shrink] when hidden (no layout impact).
///
/// Usage:
/// ```dart
/// DismissibleInfoBanner(
///   preferenceKey: 'my_feature_tip_dismissed',
///   variant: InfoBannerVariant.info,
///   content: Text('Helpful tip here'),
/// )
/// ```
class DismissibleInfoBanner extends StatefulWidget {
  const DismissibleInfoBanner({
    required this.preferenceKey,
    required this.variant,
    required this.content,
    this.bottomSpacing = AppSpacing.lg,
    super.key,
  });

  /// SharedPreferences key for storing dismissal state.
  /// Use unique key per banner (e.g., 'feature_name_tip_dismissed').
  final String preferenceKey;

  /// Banner variant (info, warning, success).
  final InfoBannerVariant variant;

  /// Banner content widget.
  final Widget content;

  /// Spacing below banner when visible. Defaults to [AppSpacing.lg].
  /// Set to 0 if parent handles spacing.
  final double bottomSpacing;

  @override
  State<DismissibleInfoBanner> createState() => _DismissibleInfoBannerState();
}

class _DismissibleInfoBannerState extends State<DismissibleInfoBanner> {
  bool _isVisible = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDismissalState();
  }

  Future<void> _loadDismissalState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final dismissed = prefs.getBool(widget.preferenceKey) ?? false;

      if (!mounted) return;

      setState(() {
        _isVisible = !dismissed;
        _isLoading = false;
      });
    } catch (_) {
      // SharedPreferences failure - hide banner (safe default)
      if (!mounted) return;

      setState(() {
        _isVisible = false;
        _isLoading = false;
      });
    }
  }

  Future<void> _handleDismiss() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(widget.preferenceKey, true);

      if (!mounted) return;

      setState(() => _isVisible = false);
    } catch (_) {
      // SharedPreferences failure - dismiss banner anyway for UX
      if (!mounted) return;

      setState(() => _isVisible = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Don't show while loading or if dismissed
    if (_isLoading || !_isVisible) {
      return const SizedBox.shrink();
    }

    // Return banner WITH spacing to maintain identical layout behavior
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        InfoBanner(
          variant: widget.variant,
          content: widget.content,
          dismissible: true,
          onDismiss: _handleDismiss,
        ),
        if (widget.bottomSpacing > 0) SizedBox(height: widget.bottomSpacing),
      ],
    );
  }
}
