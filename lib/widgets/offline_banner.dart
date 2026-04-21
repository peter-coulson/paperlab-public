import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:paperlab/services/connectivity_service.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';

/// Global offline banner shown at top of screen when no connectivity.
/// Appears/disappears automatically based on connectivity changes.
/// Non-dismissible - only disappears when connectivity is restored.
///
/// Design: Warning status indicator (matches InfoBanner warning variant)
/// - Subtle amber background with opacity (10% background, 20% border)
/// - Lucide icons following design system
/// - Proper spacing and typography
/// - Amber warning colors (attention needed, fixable)
class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final connectivityStream = ref.watch(connectivityStatusProvider);

    return connectivityStream.when(
      data: (isOnline) {
        // Show banner when offline
        if (!isOnline) {
          return Container(
            width: double.infinity,
            decoration: const BoxDecoration(
              // Solid amber background
              color: AppColors.error,
            ),
            child: SafeArea(
              // Industry standard: 8px padding for compact offline banners
              // On devices with notches, SafeArea uses larger top padding
              minimum: const EdgeInsets.all(AppSpacing.sm),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    LucideIcons.wifi_off,
                    color: Colors.white,
                    size: 18,
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Text(
                    'No internet connection',
                    style: AppTypography.bodySmall.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        // Hide banner when online
        return const SizedBox.shrink();
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }
}
