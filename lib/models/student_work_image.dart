/// Student work image reference.
/// Corresponds to SQL table: submission_images
///
/// Images are ordered by sequence and displayed with a counter
/// (e.g., "Image 1 of 3").
class StudentWorkImage {
  const StudentWorkImage({required this.url, required this.sequence})
    : assert(sequence > 0, 'Image sequence must be positive');

  factory StudentWorkImage.fromJson(Map<String, dynamic> json) =>
      StudentWorkImage(
        url: json['url'] as String,
        sequence: json['sequence'] as int,
      );

  /// Presigned URL from backend for viewing the image.
  final String url;

  /// Sequence number (1-indexed, used for display order and counter)
  final int sequence;
}
