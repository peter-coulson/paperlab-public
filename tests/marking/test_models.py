"""Tests for marking domain models.

Long-term tests only - validates critical field behavior.
"""

from paperlab.marking.models import MarkingCriterionResult


class TestMarkingCriterionResult:
    """Tests for MarkingCriterionResult Pydantic model."""

    def test_observation_defaults_to_empty(self) -> None:
        """Observation defaults to empty string if not provided.

        This is a backwards compatibility test. When parsing LLM responses
        from before the observation field was added, or when LLM doesn't
        provide observation, it should default to empty string.
        """
        result = MarkingCriterionResult(
            criterion_id=1,
            marks_awarded=1,
            feedback="Correct",
            confidence_score=0.90,
        )

        assert result.observation == ""
