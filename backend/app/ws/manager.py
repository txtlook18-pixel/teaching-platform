from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # assignment_id -> list of teacher websockets
        self._teachers: Dict[str, List[WebSocket]] = {}
        # session_id -> websocket
        self._students: Dict[str, WebSocket] = {}
        # session_id -> assignment_id
        self._session_map: Dict[str, str] = {}

    async def connect_teacher(self, assignment_id: str, ws: WebSocket):
        await ws.accept()
        self._teachers.setdefault(assignment_id, []).append(ws)

    async def connect_student(self, session_id: str, assignment_id: str, ws: WebSocket):
        await ws.accept()
        self._students[session_id] = ws
        self._session_map[session_id] = assignment_id

    def disconnect_teacher(self, assignment_id: str, ws: WebSocket):
        conns = self._teachers.get(assignment_id, [])
        if ws in conns:
            conns.remove(ws)

    def disconnect_student(self, session_id: str):
        self._students.pop(session_id, None)
        self._session_map.pop(session_id, None)

    async def notify_teachers(self, assignment_id: str, payload: dict):
        dead = []
        for ws in list(self._teachers.get(assignment_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_teacher(assignment_id, ws)

    async def notify_student(self, session_id: str, payload: dict):
        ws = self._students.get(session_id)
        if ws:
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect_student(session_id)

    async def notify_all_students(self, assignment_id: str, payload: dict):
        dead = []
        for sid, aid in list(self._session_map.items()):
            if aid == assignment_id:
                ws = self._students.get(sid)
                if ws:
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        dead.append(sid)
        for sid in dead:
            self.disconnect_student(sid)

    def student_count(self, assignment_id: str) -> int:
        return sum(1 for aid in self._session_map.values() if aid == assignment_id)


manager = ConnectionManager()
