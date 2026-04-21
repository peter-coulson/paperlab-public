"""Tests for DELETE /api/account endpoint.

Tests account deletion behavior per Apple App Store Guideline 5.1.1(v):
- Successful deletion returns 204, removes all user data from DB
- Deletion cascades to all related data (attempts, submissions, etc.)
- Unauthenticated request returns 401/403
- After deletion, user's data is no longer in database
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


@contextmanager
def mock_supabase_deletion() -> Generator[None, None, None]:
    """Mock Supabase settings and HTTP call for account deletion tests.

    Provides fake credentials to pass the pre-flight check, and mocks the
    httpx.AsyncClient to avoid actual API calls.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 204

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.delete.return_value = mock_response

    with (
        patch("paperlab.api.main.settings.supabase_url", "https://fake.supabase.co"),
        patch("paperlab.api.main.settings.supabase_service_role_key", "fake-key"),
        patch("httpx.AsyncClient", return_value=mock_client),
    ):
        yield


class TestDeleteAccountEndpoint:
    """Tests for DELETE /api/account endpoint."""

    def test_delete_account_unauthenticated_returns_403(self, client: TestClient) -> None:
        """Unauthenticated request returns 403 (HTTPBearer missing credentials)."""
        response = client.delete("/api/account")

        # FastAPI's HTTPBearer returns 403 when Authorization header is missing
        assert response.status_code == 403

    def test_delete_account_invalid_token_returns_401(self, client: TestClient) -> None:
        """Invalid token returns 401."""
        response = client.delete("/api/account", headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

    def test_delete_account_success_returns_204(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        api_test_conn: sqlite3.Connection,
    ) -> None:
        """Successful account deletion returns 204 No Content."""
        # Mock settings to skip Supabase API call (external service)
        # When supabase_url is None, the endpoint skips the external API call
        with mock_supabase_deletion():
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_account_removes_student_record(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        api_test_conn: sqlite3.Connection,
    ) -> None:
        """After deletion, student record is removed from database."""
        # Verify student exists before deletion
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM students WHERE id = 1")
        assert cursor.fetchone()[0] == 1

        # Mock settings to skip Supabase API call
        with mock_supabase_deletion():
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 204

        # Verify student is deleted
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM students WHERE id = 1")
        assert cursor.fetchone()[0] == 0

    def test_delete_account_removes_paper_attempts(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        api_test_conn: sqlite3.Connection,
        seed_paper_data: dict[str, int],
    ) -> None:
        """Deletion removes all paper attempts for the student."""
        paper_id = seed_paper_data["paper_id"]

        # Create a paper attempt for the student
        api_test_conn.execute(
            """
            INSERT INTO paper_attempts (id, attempt_uuid, student_id, paper_id)
            VALUES (1, 'test-uuid-123', 1, ?)
            """,
            (paper_id,),
        )
        api_test_conn.commit()

        # Verify paper attempt exists
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_attempts WHERE student_id = 1")
        assert cursor.fetchone()[0] == 1

        # Mock settings to skip Supabase API call
        with mock_supabase_deletion():
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 204

        # Verify paper attempt is deleted
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_attempts WHERE student_id = 1")
        assert cursor.fetchone()[0] == 0

    def test_delete_account_removes_practice_attempts(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        api_test_conn: sqlite3.Connection,
        seed_paper_data: dict[str, int],
    ) -> None:
        """Deletion removes all practice question attempts for the student."""
        question_id = seed_paper_data["question_ids"][0]

        # Create a question submission and practice attempt
        api_test_conn.execute(
            """
            INSERT INTO question_submissions (id, student_id, question_id, submission_uuid)
            VALUES (1, 1, ?, 'submission-uuid-123')
            """,
            (question_id,),
        )
        api_test_conn.execute(
            """
            INSERT INTO practice_question_attempts (id, attempt_uuid, student_id, submission_id)
            VALUES (1, 'practice-uuid-123', 1, 1)
            """
        )
        api_test_conn.commit()

        # Verify practice attempt exists
        cursor = api_test_conn.execute(
            "SELECT COUNT(*) FROM practice_question_attempts WHERE student_id = 1"
        )
        assert cursor.fetchone()[0] == 1

        # Mock settings to skip Supabase API call
        with mock_supabase_deletion():
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 204

        # Verify practice attempt is deleted
        cursor = api_test_conn.execute(
            "SELECT COUNT(*) FROM practice_question_attempts WHERE student_id = 1"
        )
        assert cursor.fetchone()[0] == 0

    def test_delete_account_removes_all_related_data(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        api_test_conn: sqlite3.Connection,
        seed_paper_data: dict[str, int],
    ) -> None:
        """Deletion cascades to all related data: submissions, images, marking attempts."""
        paper_id = seed_paper_data["paper_id"]
        question_id = seed_paper_data["question_ids"][0]

        # Create complete data chain:
        # paper_attempt -> question_attempt -> submission -> images + marking
        api_test_conn.execute(
            """
            INSERT INTO paper_attempts (id, attempt_uuid, student_id, paper_id, submitted_at)
            VALUES (1, 'paper-uuid-123', 1, ?, CURRENT_TIMESTAMP)
            """,
            (paper_id,),
        )

        api_test_conn.execute(
            """
            INSERT INTO question_submissions (id, student_id, question_id, submission_uuid)
            VALUES (1, 1, ?, 'submission-uuid-123')
            """,
            (question_id,),
        )

        api_test_conn.execute(
            """
            INSERT INTO question_attempts (id, paper_attempt_id, submission_id)
            VALUES (1, 1, 1)
            """
        )

        api_test_conn.execute(
            """
            INSERT INTO submission_images (id, submission_id, image_path, image_sequence)
            VALUES (1, 1, 'images/test/image1.png', 1)
            """
        )

        # Create LLM model for marking attempt
        api_test_conn.execute(
            """
            INSERT INTO llm_models (id, model_identifier, display_name, provider)
            VALUES (1, 'gpt-4', 'GPT-4', 'openai')
            """
        )

        api_test_conn.execute(
            """
            INSERT INTO marking_attempts
                (id, submission_id, llm_model_id, status,
                 system_prompt, user_prompt, response_received)
            VALUES (1, 1, 1, 'success', 'system', 'user', '{"marks": 5}')
            """
        )

        api_test_conn.commit()

        # Verify data exists
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_attempts")
        assert cursor.fetchone()[0] == 1
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM question_attempts")
        assert cursor.fetchone()[0] == 1
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM question_submissions")
        assert cursor.fetchone()[0] == 1
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM submission_images")
        assert cursor.fetchone()[0] == 1
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM marking_attempts")
        assert cursor.fetchone()[0] == 1

        # Mock settings to skip Supabase API call
        with mock_supabase_deletion():
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 204

        # Verify all related data is deleted
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_attempts")
        assert cursor.fetchone()[0] == 0
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM question_attempts")
        assert cursor.fetchone()[0] == 0
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM question_submissions")
        assert cursor.fetchone()[0] == 0
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM submission_images")
        assert cursor.fetchone()[0] == 0
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM marking_attempts")
        assert cursor.fetchone()[0] == 0

    def test_delete_account_paper_results_removed(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        api_test_conn: sqlite3.Connection,
        seed_paper_data: dict[str, int],
    ) -> None:
        """Deletion removes paper_results for the student's paper attempts."""
        paper_id = seed_paper_data["paper_id"]

        # Create paper attempt with results
        api_test_conn.execute(
            """
            INSERT INTO paper_attempts
                (id, attempt_uuid, student_id, paper_id, submitted_at, completed_at)
            VALUES (1, 'paper-uuid-123', 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (paper_id,),
        )
        api_test_conn.execute(
            """
            INSERT INTO paper_results
                (id, paper_attempt_id, total_marks_awarded, total_marks_available, percentage)
            VALUES (1, 1, 50, 80, 62.5)
            """
        )
        api_test_conn.commit()

        # Verify paper result exists
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_results")
        assert cursor.fetchone()[0] == 1

        # Mock settings to skip Supabase API call
        with mock_supabase_deletion():
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 204

        # Verify paper result is deleted
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_results")
        assert cursor.fetchone()[0] == 0

    def test_delete_account_with_both_paper_and_practice_attempts(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        api_test_conn: sqlite3.Connection,
        seed_paper_data: dict[str, int],
    ) -> None:
        """Deletion removes data from both paper flow and practice flow."""
        paper_id = seed_paper_data["paper_id"]
        question_ids = seed_paper_data["question_ids"]

        # Create paper attempt with question
        api_test_conn.execute(
            """
            INSERT INTO paper_attempts (id, attempt_uuid, student_id, paper_id)
            VALUES (1, 'paper-uuid-123', 1, ?)
            """,
            (paper_id,),
        )

        api_test_conn.execute(
            """
            INSERT INTO question_submissions (id, student_id, question_id, submission_uuid)
            VALUES (1, 1, ?, 'paper-submission-uuid')
            """,
            (question_ids[0],),
        )

        api_test_conn.execute(
            """
            INSERT INTO question_attempts (id, paper_attempt_id, submission_id)
            VALUES (1, 1, 1)
            """
        )

        # Create practice attempt with different question
        api_test_conn.execute(
            """
            INSERT INTO question_submissions (id, student_id, question_id, submission_uuid)
            VALUES (2, 1, ?, 'practice-submission-uuid')
            """,
            (question_ids[1],),
        )

        api_test_conn.execute(
            """
            INSERT INTO practice_question_attempts (id, attempt_uuid, student_id, submission_id)
            VALUES (1, 'practice-uuid-123', 1, 2)
            """
        )

        api_test_conn.commit()

        # Verify both types of data exist
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_attempts")
        assert cursor.fetchone()[0] == 1
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM practice_question_attempts")
        assert cursor.fetchone()[0] == 1
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM question_submissions")
        assert cursor.fetchone()[0] == 2

        # Mock settings to skip Supabase API call
        with mock_supabase_deletion():
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 204

        # Verify all data is deleted
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM paper_attempts")
        assert cursor.fetchone()[0] == 0
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM practice_question_attempts")
        assert cursor.fetchone()[0] == 0
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM question_submissions")
        assert cursor.fetchone()[0] == 0
        cursor = api_test_conn.execute("SELECT COUNT(*) FROM students WHERE id = 1")
        assert cursor.fetchone()[0] == 0

    def test_delete_account_returns_503_when_supabase_not_configured(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Returns 503 when Supabase credentials are not configured.

        This prevents orphaned auth users if DB deletion would succeed
        but Supabase deletion can't be attempted.
        """
        with patch("paperlab.api.main.settings.supabase_service_role_key", ""):
            response = client.delete("/api/account", headers=auth_headers)

        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]
