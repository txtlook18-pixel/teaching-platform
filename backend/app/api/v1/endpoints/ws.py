from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.assignment import Assignment
from app.models.session import StudentSession
from app.core.security import decode_token
from app.ws.manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/assignment/{assignment_id}")
async def teacher_ws(
    websocket: WebSocket,
    assignment_id: str,
    token: str = Query(...),
):
    user_id = decode_token(token)
    if not user_id:
        await websocket.close(code=4001)
        return

    await manager.connect_teacher(assignment_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "finish":
                await manager.notify_all_students(
                    assignment_id, {"event": "assignment_finished"}
                )
            elif action == "start":
                await manager.notify_all_students(
                    assignment_id, {"event": "test_started"}
                )
            elif action == "next_question":
                await manager.notify_all_students(
                    assignment_id,
                    {"event": "next_question", "question_index": data.get("question_index", 0)},
                )
            elif action == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        manager.disconnect_teacher(assignment_id, websocket)


@router.websocket("/ws/student/{session_id}")
async def student_ws(
    websocket: WebSocket,
    session_id: str,
):
    # We need DB access — use a one-shot session
    async for db in get_db():
        result = await db.execute(
            select(StudentSession).where(StudentSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        break

    if not session:
        await websocket.close(code=4004)
        return

    assignment_id = str(session.assignment_id)
    await manager.connect_student(session_id, assignment_id, websocket)

    # Notify teacher: new student connected
    await manager.notify_teachers(assignment_id, {
        "event": "student_joined",
        "session_id": session_id,
        "student_name": session.student_name,
        "online_count": manager.student_count(assignment_id),
    })

    try:
        while True:
            # Students can send keepalive pings
            data = await websocket.receive_json()
            if data.get("action") == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        manager.disconnect_student(session_id)
        await manager.notify_teachers(assignment_id, {
            "event": "student_left",
            "session_id": session_id,
            "student_name": session.student_name,
            "online_count": manager.student_count(assignment_id),
        })
