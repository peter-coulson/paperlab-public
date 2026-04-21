/// Score model for displaying marks awarded vs available.
/// Used in result list items.
class Score {
  const Score({required this.awarded, required this.available});

  final int awarded;
  final int available;
}
