"""
WebSocket integration tests using starlette's synchronous TestClient.
A separate file-based SQLite DB is used to avoid event-loop conflicts.
"""
import asyncio
import os
import secrets
import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.lesson import Lesson, SourceType
from app.models.assignment import Assignment, AssignmentStatus, AssignmentType
from app.models.session import StudentSession

_WS_DB_FILE = os.path.join(os.path.dirname(__file__), "_ws_test.db")
_WS_DB_URL = f"sqlite+aiosqlite:///{_WS_DB_FILE}"


async def _build_fixtures():
    engine = create_async_engine(_WS_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        user = User(
            email="ws_teacher@test.com",
            username="WSTeacher",
            hashed_password=hash_password("pwd"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        lesson = Lesson(
            teacher_id=user.id,
            title="WS Lesson",
            source_content="content",
            source_type=SourceType.TEXT,
        )
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)

        tok = secrets.token_urlsafe(16)
        assignment = Assignment(
            lesson_id=lesson.id,
            assignment_type=AssignmentType.TEST,
            status=AssignmentStatus.ACTIVE,
            session_token=tok,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        student_session = StudentSession(
            assignment_id=assignment.id,
            student_name="WSStudent",
        )
        db.add(student_session)
        await db.commit()
        await db.refresh(student_session)

        data = {
            "user_id": user.id,
            "jwt_token": create_access_token({"sub": user.id}),
            "assignment_id": assignment.id,
            "session_token": tok,
            "student_session_id": student_session.id,
        }

    await engine.dispose()
    return data


def _make_db_override():
    async def _override():
        engine = create_async_engine(_WS_DB_URL, poolclass=NullPool)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            yield session
        await engine.dispose()

    return _override


@pytest.fixture(scope="module")
def ws_client():
    data = asyncio.run(_build_fixtures())
    override = _make_db_override()

    # Override via FastAPI dependency injection (for Depends(get_db) paths)
    app.dependency_overrides[get_db] = override

    # Also patch the direct get_db() call inside the student WS endpoint
    with patch("app.api.v1.endpoints.ws.get_db", override):
        with TestClient(app) as client:
            yield client, data

    app.dependency_overrides.clear()
    if os.path.exists(_WS_DB_FILE):
        os.remove(_WS_DB_FILE)


# --- teacher WebSocket ---

def test_teacher_ws_ping_pong(ws_client):
    client, data = ws_client
    url = f"/ws/assignment/{data['assignment_id']}?token={data['jwt_token']}"
    with client.websocket_connect(url) as ws:
        ws.send_json({"action": "ping"})
        response = ws.receive_json()
        assert response["event"] == "pong"


def test_teacher_ws_invalid_token_closes(ws_client):
    client, data = ws_client
    url = f"/ws/assignment/{data['assignment_id']}?token=bad-token"
    # Server closes with code 4001; starlette raises WebSocketDisconnect on __enter__
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(url):
            pass


def test_teacher_ws_next_question_action(ws_client):
    client, data = ws_client
    url = f"/ws/assignment/{data['assignment_id']}?token={data['jwt_token']}"
    with client.websocket_connect(url) as ws:
        ws.send_json({"action": "next_question", "question_index": 1})
        ws.send_json({"action": "ping"})
        response = ws.receive_json()
        assert response["event"] == "pong"


# --- student WebSocket ---

def test_student_ws_ping_pong(ws_client):
    client, data = ws_client
    url = f"/ws/student/{data['student_session_id']}"
    with client.websocket_connect(url) as ws:
        ws.send_json({"action": "ping"})
        response = ws.receive_json()
        assert response["event"] == "pong"


def test_student_ws_invalid_session_closes(ws_client):
    client, _ = ws_client
    url = "/ws/student/nonexistent-session-id"
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(url):
            pass


# --- two-connection flow tests ---

def test_student_connect_notifies_teacher(ws_client):
    """Teacher receives student_joined when student WS connects."""
    client, data = ws_client
    teacher_url = f"/ws/assignment/{data['assignment_id']}?token={data['jwt_token']}"
    student_url = f"/ws/student/{data['student_session_id']}"

    with client.websocket_connect(teacher_url) as teacher_ws:
        with client.websocket_connect(student_url):
            # Student connecting triggers notify_teachers
            msg = teacher_ws.receive_json()
            assert msg["event"] == "student_joined"
            assert msg["student_name"] == "WSStudent"


def test_teacher_finish_notifies_student(ws_client):
    """Student receives assignment_finished when teacher sends finish action."""
    client, data = ws_client
    teacher_url = f"/ws/assignment/{data['assignment_id']}?token={data['jwt_token']}"
    student_url = f"/ws/student/{data['student_session_id']}"

    with client.websocket_connect(teacher_url) as teacher_ws:
        with client.websocket_connect(student_url) as student_ws:
            # Drain student_joined notification
            teacher_ws.receive_json()

            # Teacher finishes the assignment
            teacher_ws.send_json({"action": "finish"})

            # Student must receive assignment_finished
            msg = student_ws.receive_json()
            assert msg["event"] == "assignment_finished"
