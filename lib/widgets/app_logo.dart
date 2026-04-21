import 'package:flutter/material.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_typography.dart';

/// App logo widget - PaperLab brand identity.
///
/// Displays the PaperLab wordmark using brand typography and colors.
/// Extracted as reusable component per DRY principle (used 2+ times).
///
/// Used on:
/// - Home Screen (01-home-screen.md)
/// - Login Screen (00-login-screen.md)
///
/// Styling:
/// - Font: IBM Plex Serif, 46px, SemiBold
/// - Color: Primary indigo (#667EEA)
/// - Letter spacing: -0.65
class AppLogo extends StatelessWidget {
  const AppLogo({super.key});

  @override
  Widget build(BuildContext context) => Text(
    'PaperLab',
    style: AppTypography.logo.copyWith(color: AppColors.primary),
  );
}
