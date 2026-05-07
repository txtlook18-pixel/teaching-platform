import secrets
from datetime import datetime, timedelta
import pytest
from unittest.mock import AsyncMock, patch

from app.models.assignment import AssignmentStatus
from app.models.session import StudentSession


# --- list assignments ---

async def test_list_assignments_requires_auth(client, test_lesson):
    r = await client.get(f"/api/v1/assignments/lessons/{test_lesson.id}/assignments")
    assert r.status_code in (401, 403)


async def test_list_assignments_empty(client, test_lesson, auth_headers):
    r = await client.get(
        f"/api/v1/assignments/lessons/{test_lesson.id}/assignments",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json() == []


async def test_list_assignments_unknown_lesson(client, auth_headers):
    r = await client.get(
        "/api/v1/assignments/lessons/no-such-lesson/assignments",
        headers=auth_headers,
    )
    assert r.status_code == 404


# --- create assignment ---

async def test_create_assignment_success(client, test_lesson, auth_headers):
    payload = {"assignment_type": "test", "question_count": 10, "timer_seconds": 60}
    r = await client.post(
        f"/api/v1/assignments/lessons/{test_lesson.id}/assignments",
        json=payload,
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["assignment_type"] == "test"
    assert data["status"] == "draft"
    assert data["question_count"] == 10
    assert data["timer_seconds"] == 60


async def test_create_assignment_unknown_lesson(client, auth_headers):
    payload = {"assignment_type": "cards"}
    r = await client.post(
        "/api/v1/assignments/lessons/no-such/assignments",
        json=payload,
        headers=auth_headers,
    )
    assert r.status_code == 404


# --- get assignment ---

async def test_get_assignment_success(client, test_assignment, auth_headers):
    r = await client.get(
        f"/api/v1/assignments/{test_assignment.id}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["id"] == test_assignment.id


async def test_get_assignment_not_found(client, auth_headers):
    r = await client.get("/api/v1/assignments/no-such-id", headers=auth_headers)
    assert r.status_code == 404


# --- generate (mocked AI) ---

async def test_generate_content(client, test_assignment, auth_headers):
    mock_questions = [{"question": "Q?", "options": ["A", "B"], "correct": "A", "difficulty": "easy"}]

    with patch("app.api.v1.endpoints.assignments.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.generate_questions = AsyncMock(return_value=mock_questions)
        mock_factory.return_value = mock_ai

        r = await client.post(
            f"/api/v1/assignments/{test_assignment.id}/generate",
            headers=auth_headers,
        )

    assert r.status_code == 200
    assert r.json()["status"] == "generated"


# --- activate ---

async def test_activate_assignment(client, test_assignment, auth_headers):
    r = await client.post(
        f"/api/v1/assignments/{test_assignment.id}/activate",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "session_token" in data
    assert data["assignment_id"] == test_assignment.id


# --- student join ---

async def _activate(client, assignment_id, headers):
    r = await client.post(f"/api/v1/assignments/{assignment_id}/activate", headers=headers)
    return r.json()["session_token"]


async def test_student_join_success(client, test_assignment, auth_headers, db):
    token = await _activate(client, test_assignment.id, auth_headers)

    # Extend expiry so it's valid
    from sqlalchemy import select
    from app.models.assignment import Assignment
    assignment = await db.get(Assignment, test_assignment.id)
    assignment.session_expires_at = datetime.utcnow() + timedelta(minutes=30)
    await db.commit()

    with patch("app.api.v1.endpoints.assignments.ws_manager") as mock_mgr:
        mock_mgr.notify_teachers = AsyncMock()
        r = await client.post("/api/v1/assignments/join", json={
            "session_token": token,
            "student_name": "Alice",
        })

    assert r.status_code == 200
    data = r.json()
    assert data["student_name"] == "Alice"
    assert data["assignment_id"] == test_assignment.id


async def test_student_join_invalid_token(client):
    r = await client.post("/api/v1/assignments/join", json={
        "session_token": "bad-token",
        "student_name": "Bob",
    })
    assert r.status_code == 404


async def test_student_join_duplicate_name(client, test_assignment, auth_headers, db):
    token = await _activate(client, test_assignment.id, auth_headers)

    from app.models.assignment import Assignment
    assignment = await db.get(Assignment, test_assignment.id)
    assignment.session_expires_at = datetime.utcnow() + timedelta(minutes=30)
    await db.commit()

    with patch("app.api.v1.endpoints.assignments.ws_manager") as mock_mgr:
        mock_mgr.notify_teachers = AsyncMock()
        await client.post("/api/v1/assignments/join", json={
            "session_token": token, "student_name": "Alice",
        })
        r2 = await client.post("/api/v1/assignments/join", json={
            "session_token": token, "student_name": "Alice",
        })

    assert r2.status_code == 400


# --- submit answer ---

async def test_submit_answer(client, test_assignment, auth_headers, db):
    token = await _activate(client, test_assignment.id, auth_headers)

    from app.models.assignment import Assignment
    assignment = await db.get(Assignment, test_assignment.id)
    assignment.session_expires_at = datetime.utcnow() + timedelta(minutes=30)
    await db.commit()

    with patch("app.api.v1.endpoints.assignments.ws_manager") as mock_mgr:
        mock_mgr.notify_teachers = AsyncMock()
        join = await client.post("/api/v1/assignments/join", json={
            "session_token": token, "student_name": "Carol",
        })
        session_id = join.json()["session_id"]

        mock_mgr.notify_teachers = AsyncMock()
        r = await client.post("/api/v1/assignments/answer", json={
            "session_id": session_id,
            "question_index": "0",
            "answer_data": {"answer": "A", "is_correct": True},
            "question_difficulty": "easy",
        })

    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "recorded"
    assert data["is_correct"] is True


async def test_submit_answer_unknown_session(client):
    r = await client.post("/api/v1/assignments/answer", json={
        "session_id": "no-such",
        "question_index": "0",
        "answer_data": {"answer": "A"},
    })
    assert r.status_code == 404


# --- results ---

async def test_get_results(client, test_assignment, auth_headers):
    r = await client.get(
        f"/api/v1/assignments/{test_assignment.id}/results",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["assignment_id"] == test_assignment.id
    assert "sessions" in data
    assert "responses" in data


# --- finish ---

async def test_finish_assignment(client, test_assignment, auth_headers):
    with patch("app.api.v1.endpoints.assignments.ws_manager") as mock_mgr:
        mock_mgr.notify_all_students = AsyncMock()
        r = await client.post(
            f"/api/v1/assignments/{test_assignment.id}/finish",
            headers=auth_headers,
        )

    assert r.status_code == 200
    assert r.json()["status"] == "finished"


# --- grade response ---

# --- history ---

async def test_history_requires_auth(client):
    r = await client.get("/api/v1/assignments/history")
    assert r.status_code in (401, 403)


async def test_history_empty(client, auth_headers):
    r = await client.get("/api/v1/assignments/history", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


async def test_history_returns_assignment_with_lesson_title(client, test_assignment, auth_headers):
    r = await client.get("/api/v1/assignments/history", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    item = data[0]
    assert item["id"] == test_assignment.id
    assert item["lesson_title"] == "Test Lesson"
    assert item["assignment_type"] == "test"
    assert item["student_count"] == 0
    assert item["response_count"] == 0


async def test_history_isolates_teachers(client, db, test_assignment, auth_headers):
    from app.models.user import User
    from app.models.lesson import Lesson, SourceType
    from app.models.assignment import Assignment, AssignmentType
    from app.core.security import hash_password, create_access_token

    other = User(email="other@test.com", username="Other", hashed_password=hash_password("x"))
    db.add(other)
    await db.commit()
    await db.refresh(other)

    other_lesson = Lesson(
        teacher_id=other.id, title="Other Lesson",
        source_content="x", language="en", source_type=SourceType.TEXT,
    )
    db.add(other_lesson)
    await db.commit()
    await db.refresh(other_lesson)

    db.add(Assignment(lesson_id=other_lesson.id, assignment_type=AssignmentType.CARDS))
    await db.commit()

    r = await client.get("/api/v1/assignments/history", headers=auth_headers)
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()]
    assert test_assignment.id in ids
    assert all(item["lesson_title"] == "Test Lesson" for item in r.json())


async def test_history_newest_first(client, db, test_lesson, auth_headers):
    from app.models.assignment import Assignment, AssignmentType
    from datetime import datetime, timedelta

    a1 = Assignment(lesson_id=test_lesson.id, assignment_type=AssignmentType.TEST)
    a2 = Assignment(lesson_id=test_lesson.id, assignment_type=AssignmentType.CARDS)
    db.add_all([a1, a2])
    await db.commit()
    await db.refresh(a1)
    await db.refresh(a2)

    r = await client.get("/api/v1/assignments/history", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    dates = [item["created_at"] for item in items]
    assert dates == sorted(dates, reverse=True)


async def test_history_pagination(client, db, test_lesson, auth_headers):
    from app.models.assignment import Assignment, AssignmentType

    assignments = [
        Assignment(lesson_id=test_lesson.id, assignment_type=AssignmentType.TEST)
        for _ in range(5)
    ]
    db.add_all(assignments)
    await db.commit()

    r_all = await client.get("/api/v1/assignments/history", headers=auth_headers)
    assert len(r_all.json()) == 5

    r_page = await client.get(
        "/api/v1/assignments/history?limit=2&offset=0", headers=auth_headers
    )
    assert len(r_page.json()) == 2

    r_offset = await client.get(
        "/api/v1/assignments/history?limit=2&offset=2", headers=auth_headers
    )
    assert len(r_offset.json()) == 2

    first_ids = {item["id"] for item in r_page.json()}
    second_ids = {item["id"] for item in r_offset.json()}
    assert first_ids.isdisjoint(second_ids)


# --- grade response ---

async def test_grade_response(client, test_assignment, auth_headers, db):
    token = await _activate(client, test_assignment.id, auth_headers)

    from app.models.assignment import Assignment
    assignment = await db.get(Assignment, test_assignment.id)
    assignment.session_expires_at = datetime.utcnow() + timedelta(minutes=30)
    await db.commit()

    with patch("app.api.v1.endpoints.assignments.ws_manager") as mock_mgr:
        mock_mgr.notify_teachers = AsyncMock()
        join = await client.post("/api/v1/assignments/join", json={
            "session_token": token, "student_name": "Dave",
        })
        session_id = join.json()["session_id"]

        mock_mgr.notify_teachers = AsyncMock()
        ans = await client.post("/api/v1/assignments/answer", json={
            "session_id": session_id,
            "question_index": "0",
            "answer_data": {"answer": "retelling text"},
        })
        response_id = ans.json()["response_id"]

    r = await client.post(
        f"/api/v1/assignments/{test_assignment.id}/responses/{response_id}/grade",
        json={"grade": "excellent", "is_correct": True},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "graded"
