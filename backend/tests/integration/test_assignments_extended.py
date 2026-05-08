"""Extended assignment tests covering generation types, error paths, retelling chat."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest


# --- generate: all assignment types ---

async def _create_and_get_assignment(client, auth_headers, test_lesson, assignment_type: str):
    payload = {"assignment_type": assignment_type, "question_count": 3}
    r = await client.post(
        f"/api/v1/assignments/lessons/{test_lesson.id}/assignments",
        json=payload,
        headers=auth_headers,
    )
    assert r.status_code == 200
    return r.json()["id"]


async def test_generate_battle_type(client, test_lesson, auth_headers):
    aid = await _create_and_get_assignment(client, auth_headers, test_lesson, "battle")
    mock_cases = [{"title": "Case A", "side_a": "pro", "side_b": "con", "synthesis": "result"}]

    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.generate_cases = AsyncMock(return_value=mock_cases)
        mock_factory.return_value = mock_ai
        r = await client.post(f"/api/v1/assignments/{aid}/generate", headers=auth_headers)

    assert r.status_code == 200
    assert r.json()["status"] == "generated"


async def test_generate_analysis_type(client, test_lesson, auth_headers):
    aid = await _create_and_get_assignment(client, auth_headers, test_lesson, "analysis")
    mock_cases = [{"title": "Analysis Case", "description": "Describe...", "expected_answer": "..."}]

    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.generate_cases = AsyncMock(return_value=mock_cases)
        mock_factory.return_value = mock_ai
        r = await client.post(f"/api/v1/assignments/{aid}/generate", headers=auth_headers)

    assert r.status_code == 200


async def test_generate_cards_type(client, test_lesson, auth_headers):
    aid = await _create_and_get_assignment(client, auth_headers, test_lesson, "cards")
    mock_cards = [{"term": "Photosynthesis", "definition": "Process of..."}]

    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.generate_flashcards = AsyncMock(return_value=mock_cards)
        mock_factory.return_value = mock_ai
        r = await client.post(f"/api/v1/assignments/{aid}/generate", headers=auth_headers)

    assert r.status_code == 200


async def test_generate_retelling_type(client, test_lesson, auth_headers):
    aid = await _create_and_get_assignment(client, auth_headers, test_lesson, "retelling")

    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.generate_reference_retelling = AsyncMock(return_value="Reference text about the topic.")
        mock_factory.return_value = mock_ai
        r = await client.post(f"/api/v1/assignments/{aid}/generate", headers=auth_headers)

    assert r.status_code == 200


async def test_generate_not_found(client, auth_headers):
    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_factory.return_value = mock_ai
        r = await client.post("/api/v1/assignments/no-such-id/generate", headers=auth_headers)
    assert r.status_code == 404


# --- activate 404 ---

async def test_activate_not_found(client, auth_headers):
    r = await client.post("/api/v1/assignments/no-such/activate", headers=auth_headers)
    assert r.status_code == 404


# --- join: inactive and expired session ---

async def test_join_inactive_session(client, test_assignment, auth_headers, db):
    """Assignment that was never activated → status = draft → 400."""
    from app.models.assignment import Assignment
    assignment = await db.get(Assignment, test_assignment.id)
    # Put a fake session token but keep status = draft
    assignment.session_token = "fake-draft-token"
    await db.commit()

    r = await client.post("/api/v1/assignments/join", json={
        "session_token": "fake-draft-token",
        "student_name": "Alice",
    })
    assert r.status_code == 400
    assert "not active" in r.json()["detail"].lower()


async def test_join_expired_session(client, test_assignment, auth_headers, db):
    from app.models.assignment import Assignment, AssignmentStatus

    assignment = await db.get(Assignment, test_assignment.id)
    assignment.status = AssignmentStatus.ACTIVE
    assignment.session_token = "expired-token-xyz"
    assignment.session_expires_at = datetime.utcnow() - timedelta(minutes=1)
    await db.commit()

    r = await client.post("/api/v1/assignments/join", json={
        "session_token": "expired-token-xyz",
        "student_name": "Bob",
    })
    assert r.status_code == 400
    assert "expired" in r.json()["detail"].lower()


# --- results 404 ---

async def test_get_results_not_found(client, auth_headers):
    r = await client.get("/api/v1/assignments/no-such/results", headers=auth_headers)
    assert r.status_code == 404


# --- finish 404 ---

async def test_finish_not_found(client, auth_headers):
    with patch("app.api.v1.endpoints.assignments.ws_manager") as mock_mgr:
        mock_mgr.notify_all_students = AsyncMock()
        r = await client.post("/api/v1/assignments/no-such/finish", headers=auth_headers)
    assert r.status_code == 404


# --- retelling chat ---

async def _setup_retelling(client, auth_headers, test_lesson, db):
    """Create and return ID of a retelling assignment."""
    r = await client.post(
        f"/api/v1/assignments/lessons/{test_lesson.id}/assignments",
        json={"assignment_type": "retelling"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    return r.json()["id"]


async def test_retelling_chat_success(client, auth_headers, test_lesson, db):
    aid = await _setup_retelling(client, auth_headers, test_lesson, db)

    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.chat_response = AsyncMock(return_value="AI reply about the topic.")
        mock_factory.return_value = mock_ai
        r = await client.post(
            f"/api/v1/assignments/{aid}/chat",
            json={"message": "Tell me more", "history": []},
            headers=auth_headers,
        )

    assert r.status_code == 200
    assert "reply" in r.json()


async def test_retelling_chat_wrong_type(client, auth_headers, test_assignment):
    """test assignment (not retelling) should return 400."""
    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_factory.return_value = mock_ai
        r = await client.post(
            f"/api/v1/assignments/{test_assignment.id}/chat",
            json={"message": "Hi", "history": []},
            headers=auth_headers,
        )
    assert r.status_code == 400


async def test_retelling_chat_not_found(client, auth_headers):
    r = await client.post(
        "/api/v1/assignments/no-such/chat",
        json={"message": "Hi", "history": []},
        headers=auth_headers,
    )
    assert r.status_code == 404


# --- grade response: response not found ---

async def test_grade_response_not_found(client, auth_headers, test_assignment):
    r = await client.post(
        f"/api/v1/assignments/{test_assignment.id}/responses/no-such-response/grade",
        json={"grade": "good", "is_correct": True},
        headers=auth_headers,
    )
    assert r.status_code == 404
