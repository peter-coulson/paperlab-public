import 'dart:async';
import 'dart:io' if (dart.library.html) 'dart:io';

import 'package:easy_image_viewer/easy_image_viewer.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:paperlab/models/question_metadata.dart';
import 'package:paperlab/providers/upload_provider.dart';
import 'package:paperlab/router.dart';
import 'package:paperlab/services/consent_service.dart';
import 'package:paperlab/theme/app_colors.dart';
import 'package:paperlab/theme/app_spacing.dart';
import 'package:paperlab/theme/app_typography.dart';
import 'package:paperlab/utils/error_messages.dart';
import 'package:paperlab/utils/exam_date_utils.dart';
import 'package:paperlab/utils/string_utils.dart';
import 'package:paperlab/widgets/bottom_sheet_menu.dart';
import 'package:paperlab/widgets/dismissible_info_banner.dart';
import 'package:paperlab/widgets/info_banner.dart';
import 'package:paperlab/widgets/list_items/upload_photo_list_item.dart';
import 'package:paperlab/widgets/primary_button.dart';
import 'package:paperlab/widgets/reorderable_photo_list.dart';
import 'package:paperlab/widgets/screen_header.dart';

/// Question Upload Screen - Upload and manage photos for a single question.
/// See specs/wireframes/04-question-upload-screen.md for complete
/// specification.
///
/// Features:
/// - Screen header with question name and \[X\] close button
/// - InfoBanner for first-time users (dismissible, persisted via
///   SharedPreferences)
/// - Empty state: AddButton for selecting photos
/// - Filled state: Vertical ReorderableListView with photos
/// - Photo management: Swipe-to-reveal delete, reorder (long-press drag),
///   fullscreen tap
/// - Confirm button (context-aware navigation)
///
/// Navigation:
/// - Back → Context-aware (paper context: Paper Upload,
///          standalone: Selection)
/// - Tap photo → Fullscreen viewer
/// - Confirm → Context-aware (paper context: return photos,
///             standalone: Marking Progress)
class QuestionUploadScreen extends ConsumerStatefulWidget {
  const QuestionUploadScreen({
    required this.title,
    this.subtitle,
    this.existingPhotos,
    this.question,
    super.key,
  });

  /// Format question title for screen header.
  /// Example: "Question 2"
  static String formatQuestionTitle(int questionNumber) =>
      'Question $questionNumber';

  /// Format paper name for subtitle.
  /// Standard format: "{paper type} {date}"
  /// Example: "Paper 2 Nov 2023"
  static String formatPaperName({
    required String paperName,
    required DateTime examDate,
  }) {
    final paperType = extractPaperType(paperName);
    final formattedDate = formatExamDateFromDateTime(examDate);
    return '$paperType $formattedDate';
  }

  /// Title to display in header (e.g., "Question 5")
  final String title;

  /// Optional subtitle to display in header
  final String? subtitle;

  /// Existing photos to display (for editing in paper context)
  final List<XFile>? existingPhotos;

  /// Question metadata (for standalone practice question context)
  final QuestionMetadata? question;

  @override
  ConsumerState<QuestionUploadScreen> createState() =>
      _QuestionUploadScreenState();
}

class _QuestionUploadScreenState extends ConsumerState<QuestionUploadScreen> {
  final ImagePicker _picker = ImagePicker();
  late List<XFile> _photos;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _photos = widget.existingPhotos?.toList() ?? [];
  }

  /// Show bottom sheet to choose photo source (camera or library)
  Future<void> _handleAddPhotos() async {
    await showBottomSheetMenu(
      context: context,
      items: [
        BottomSheetMenuItem(
          icon: LucideIcons.camera,
          label: 'Take Photo',
          onTap: () {
            Navigator.pop(context); // Close bottom sheet
            _handleCameraCapture();
          },
        ),
        BottomSheetMenuItem(
          icon: LucideIcons.image,
          label: 'Choose from Library',
          onTap: () {
            Navigator.pop(context); // Close bottom sheet
            _handleGallerySelection();
          },
        ),
      ],
    );
  }

  /// Handle capturing photo with camera (single photo)
  Future<void> _handleCameraCapture() async {
    try {
      final XFile? xFile = await _picker.pickImage(source: ImageSource.camera);
      if (!mounted) return;

      if (xFile != null) {
        setState(() => _photos.add(xFile));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Failed to capture photo: $e')));
      }
    }
  }

  /// Handle selecting photos from library (multiple photos)
  Future<void> _handleGallerySelection() async {
    try {
      final List<XFile> xFiles = await _picker.pickMultiImage();
      if (!mounted) return;

      if (xFiles.isNotEmpty) {
        setState(() => _photos.addAll(xFiles));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Failed to select photos: $e')));
      }
    }
  }

  /// Delete photo at index
  void _handleDeletePhoto(int index) {
    setState(() => _photos.removeAt(index));
  }

  /// Reorder photos (drag and drop)
  void _handleReorder(int oldIndex, int newIndex) {
    setState(() {
      // Adjust newIndex if dragging downwards
      if (newIndex > oldIndex) {
        newIndex--;
      }
      final photo = _photos.removeAt(oldIndex);
      _photos.insert(newIndex, photo);
    });
  }

  /// Open fullscreen viewer for photo at index
  Future<void> _handlePhotoTap(int index) async {
    // Convert XFile list to ImageProvider list (platform-specific)
    final List<ImageProvider> imageProviders;

    if (kIsWeb) {
      // Web: Use MemoryImage with bytes (File not supported)
      final futures = _photos.map((p) => p.readAsBytes()).toList();
      final bytes = await Future.wait(futures);
      imageProviders = bytes.map((b) => MemoryImage(b)).toList();
    } else {
      // Mobile/Desktop: Use FileImage
      imageProviders = _photos
          .map((photo) => FileImage(File(photo.path)))
          .toList();
    }

    if (!mounted) return;

    unawaited(
      showImageViewerPager(
        context,
        MultiImageProvider(imageProviders, initialIndex: index),
        swipeDismissible: true,
        doubleTapZoomable: true,
        backgroundColor: Colors.black,
        closeButtonColor: Colors.white,
      ),
    );
  }

  /// Handle confirm button
  Future<void> _handleConfirm() async {
    if (_photos.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please add at least one photo')),
      );
      return;
    }

    // Prevent multiple submissions - set flag synchronously before async work
    if (_isSubmitting) return;
    _isSubmitting = true;

    // Context-aware navigation
    // Paper context (question == null): Return photos to Paper Upload Screen
    // Standalone context (question != null): Submit via provider
    if (widget.question == null) {
      // Paper context: Return photos to Paper Upload Screen
      if (!mounted) return;
      Navigator.of(context).pop(_photos);
    } else {
      // Standalone practice context: Submit via provider
      // Check AI consent before uploading (App Store requirement)
      final hasConsent = await ConsentService.instance.ensureAiConsent(context);
      if (!hasConsent) {
        // User declined consent - reset state and don't upload
        _isSubmitting = false;
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'AI consent is required to mark your work. '
                'You can grant consent when you next submit.',
              ),
              duration: Duration(seconds: 4),
            ),
          );
        }
        return;
      }

      setState(() {}); // Trigger UI rebuild to show loading state

      try {
        // Reset provider state in case previous upload left it non-initial
        ref.read(practiceUploadFlowProvider.notifier).reset();

        final attemptId = await ref
            .read(practiceUploadFlowProvider.notifier)
            .submit(question: widget.question!, images: _photos);

        // Check mounted right before using context
        if (!mounted) return;

        // Navigate to marking screen with subtitle as query param
        final subtitle = QuestionUploadScreen.formatPaperName(
          paperName: widget.question!.paperName,
          examDate: widget.question!.examDate,
        );
        final encodedSubtitle = Uri.encodeComponent(subtitle);
        final path = AppRoutes.questionMarking(attemptId);
        context.go('$path?subtitle=$encodedSubtitle');
      } catch (e) {
        // Error occurred - reset state and show user-friendly message
        if (!mounted) return;
        setState(() => _isSubmitting = false);

        // Get user-friendly error message
        final errorMessage = ErrorMessages.getUserMessage(e);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
            backgroundColor: AppColors.error,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.background,
    body: SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header with question information
          ScreenHeader(title: widget.title, subtitle: widget.subtitle),

          // Scrollable content
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Dismissible info banner (handles its own persistence)
                  DismissibleInfoBanner(
                    preferenceKey: 'question_upload_tip_dismissed',
                    variant: InfoBannerVariant.info,
                    content: _buildBannerContent(),
                  ),

                  // Photo display area
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final double photoWidth = constraints.maxWidth;

                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Photos list (if any)
                          // Note: DismissibleListItem already adds
                          // AppSpacing.md bottom padding to each photo
                          ReorderablePhotoList(
                            photos: _photos,
                            photoWidth: photoWidth,
                            onReorder: _handleReorder,
                            onDelete: _handleDeletePhoto,
                            onTap: _handlePhotoTap,
                          ),

                          // Upload button (always visible)
                          // Spacing matches photo-to-photo gap
                          // (AppSpacing.md from last photo's bottom padding)
                          UploadPhotoListItem(
                            onTap: _handleAddPhotos,
                            width: photoWidth,
                            aspectRatio: 15 / 7,
                          ),
                        ],
                      );
                    },
                  ),

                  const SizedBox(height: AppSpacing.lg),
                ],
              ),
            ),
          ),

          // Bottom action: Confirm button
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: PrimaryButton(
              text: _isSubmitting ? 'Submitting...' : 'Confirm',
              onTap: _photos.isNotEmpty && !_isSubmitting
                  ? _handleConfirm
                  : null,
              requiresNetwork: true,
              disabled: _photos.isEmpty || _isSubmitting,
            ),
          ),
        ],
      ),
    ),
  );

  Widget _buildBannerContent() {
    final textStyle = AppTypography.body.copyWith(color: AppColors.textPrimary);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Tip: For best results, ensure photos are:', style: textStyle),
        const SizedBox(height: AppSpacing.xs),
        Text('• In order (page 1, then page 2, etc.)', style: textStyle),
        Text('• Clear and in focus', style: textStyle),
        Text('• Cropped to show just the question', style: textStyle),
      ],
    );
  }
}
