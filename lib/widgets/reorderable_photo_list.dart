import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:paperlab/widgets/dismissible_list_item.dart';
import 'package:paperlab/widgets/list_items/photo_list_item.dart';

/// Reorderable photo list with drag-to-reorder and swipe-to-delete.
///
/// Features:
/// - Long-press drag to reorder
/// - Swipe right to reveal delete
/// - Tap photo to view fullscreen
/// - Shrink-wrapped for use in scrollable parents
/// - Full image display (no aspect ratio constraint)
///
/// Usage:
/// ```dart
/// ReorderablePhotoList(
///   photos: _photos,
///   photoWidth: constraints.maxWidth,
///   onReorder: (oldIndex, newIndex) { ... },
///   onDelete: (index) { ... },
///   onTap: (index) { ... },
/// )
/// ```
class ReorderablePhotoList extends StatelessWidget {
  const ReorderablePhotoList({
    required this.photos,
    required this.photoWidth,
    required this.onReorder,
    required this.onDelete,
    required this.onTap,
    super.key,
  });

  /// List of photos to display.
  final List<XFile> photos;

  /// Width of each photo (typically full screen width).
  final double photoWidth;

  /// Callback when user drags photo to new position.
  final void Function(int oldIndex, int newIndex) onReorder;

  /// Callback when user deletes photo.
  final void Function(int index) onDelete;

  /// Callback when user taps photo.
  final void Function(int index) onTap;

  @override
  Widget build(BuildContext context) {
    if (photos.isEmpty) {
      return const SizedBox.shrink();
    }

    return ReorderableListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: photos.length,
      onReorder: onReorder,
      buildDefaultDragHandles: false,
      itemBuilder: (context, index) => ReorderableDragStartListener(
        key: ValueKey(photos[index].path),
        index: index,
        child: DismissibleListItem(
          itemKey: ValueKey(photos[index].path),
          onDelete: () => onDelete(index),
          child: PhotoListItem(
            imageFile: photos[index],
            width: photoWidth,
            onTap: () => onTap(index),
          ),
        ),
      ),
    );
  }
}
