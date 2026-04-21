"""API endpoint tests.

Tests for:
- GET /health - Health check (no auth)
- POST /api/auth/login - Login (success and failure)
- GET /api/papers - List papers (requires auth)
- GET /api/questions - List questions (requires auth)
"""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health check returns 200 with status ok."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_no_auth_required(self, client: TestClient) -> None:
        """Health check works without authentication."""
        # No Authorization header
        response = client.get("/health")

        assert response.status_code == 200


class TestAuthWithDevToken:
    """Tests for development token authentication.

    Note: Login endpoint was removed - auth is now via Supabase.
    These tests verify the dev token bypass works correctly.
    """

    def test_dev_token_allows_access(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Dev token in development mode allows API access."""
        response = client.get("/api/papers", headers=auth_headers)

        assert response.status_code == 200


class TestPapersEndpoint:
    """Tests for GET /api/papers endpoint."""

    def test_papers_requires_auth(self, client: TestClient) -> None:
        """Unauthenticated request returns 403 (HTTPBearer missing credentials)."""
        response = client.get("/api/papers")

        # FastAPI's HTTPBearer returns 403 when Authorization header is missing
        assert response.status_code == 403

    def test_papers_empty_list(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Returns empty list when no papers exist."""
        response = client.get("/api/papers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data == {"papers": []}

    def test_papers_returns_list(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seed_paper_data: dict[str, int],
    ) -> None:
        """Returns list of papers with correct structure."""
        response = client.get("/api/papers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "papers" in data
        assert len(data["papers"]) == 1

        paper = data["papers"][0]
        assert paper["paper_id"] == seed_paper_data["paper_id"]
        assert paper["exam_board"] == "pearson-edexcel"
        assert paper["exam_level"] == "gcse"
        assert paper["subject"] == "mathematics"
        assert paper["paper_code"] == "1MA1/3H"
        assert paper["display_name"] == "GCSE Maths Paper 3H"
        assert paper["year"] == 2023
        assert paper["month"] == 11
        assert paper["total_marks"] == 80
        assert paper["question_count"] == 3

    def test_papers_filter_by_exam_board(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seed_paper_data: dict[str, int],
    ) -> None:
        """Filter papers by exam_board parameter."""
        # Matching filter
        response = client.get("/api/papers?exam_board=pearson-edexcel", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["papers"]) == 1

        # Non-matching filter
        response = client.get("/api/papers?exam_board=aqa", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["papers"]) == 0


class TestQuestionsEndpoint:
    """Tests for GET /api/questions endpoint."""

    def test_questions_requires_auth(self, client: TestClient) -> None:
        """Unauthenticated request returns 403 (HTTPBearer missing credentials)."""
        response = client.get("/api/questions")

        # FastAPI's HTTPBearer returns 403 when Authorization header is missing
        assert response.status_code == 403

    def test_questions_empty_list(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Returns empty list when no questions exist."""
        response = client.get("/api/questions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data == {"questions": []}

    def test_questions_returns_list(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seed_paper_data: dict[str, int],
    ) -> None:
        """Returns list of questions with correct structure."""
        response = client.get("/api/questions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 3

        # Check first question structure
        q = data["questions"][0]
        assert "question_id" in q
        assert q["paper_id"] == seed_paper_data["paper_id"]
        assert "paper_name" in q
        assert q["exam_date"] == "2023-11-13"
        assert "question_number" in q
        assert q["total_marks"] == 5

    def test_questions_filter_by_paper_id(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seed_paper_data: dict[str, int],
    ) -> None:
        """Filter questions by paper_id parameter."""
        paper_id = seed_paper_data["paper_id"]

        # Matching filter
        response = client.get(f"/api/questions?paper_id={paper_id}", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["questions"]) == 3

        # Non-matching filter
        response = client.get("/api/questions?paper_id=99999", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["questions"]) == 0

    def test_questions_ordered_by_date_and_number(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        seed_paper_data: dict[str, int],
    ) -> None:
        """Questions are ordered by exam_date DESC, question_number ASC."""
        response = client.get("/api/questions", headers=auth_headers)

        assert response.status_code == 200
        questions = response.json()["questions"]

        # All from same paper, should be in question_number order
        question_numbers = [q["question_number"] for q in questions]
        assert question_numbers == [1, 2, 3]


class TestInvalidToken:
    """Tests for invalid/expired token handling."""

    def test_invalid_token_format(self, client: TestClient) -> None:
        """Invalid token format returns 401."""
        response = client.get("/api/papers", headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

    def test_missing_bearer_prefix(self, client: TestClient) -> None:
        """Missing Bearer prefix returns 403 (malformed Authorization header)."""
        response = client.get("/api/papers", headers={"Authorization": "some-token"})

        # FastAPI's HTTPBearer returns 403 for malformed headers
        assert response.status_code == 403
