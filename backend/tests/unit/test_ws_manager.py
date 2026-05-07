import pytest
from unittest.mock import AsyncMock, MagicMock

from app.ws.manager import ConnectionManager


def _make_ws():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.fixture
def manager():
    return ConnectionManager()


async def test_connect_teacher_accepts_and_registers(manager):
    ws = _make_ws()
    await manager.connect_teacher("assign-1", ws)
    ws.accept.assert_awaited_once()
    assert ws in manager._teachers["assign-1"]


async def test_disconnect_teacher_removes_ws(manager):
    ws = _make_ws()
    await manager.connect_teacher("assign-1", ws)
    manager.disconnect_teacher("assign-1", ws)
    assert ws not in manager._teachers.get("assign-1", [])


async def test_disconnect_teacher_unknown_is_noop(manager):
    ws = _make_ws()
    manager.disconnect_teacher("no-such-assign", ws)  # should not raise


async def test_connect_student_accepts_and_registers(manager):
    ws = _make_ws()
    await manager.connect_student("sess-1", "assign-1", ws)
    ws.accept.assert_awaited_once()
    assert manager._students["sess-1"] is ws
    assert manager._session_map["sess-1"] == "assign-1"


async def test_disconnect_student_removes_maps(manager):
    ws = _make_ws()
    await manager.connect_student("sess-1", "assign-1", ws)
    manager.disconnect_student("sess-1")
    assert "sess-1" not in manager._students
    assert "sess-1" not in manager._session_map


async def test_disconnect_student_unknown_is_noop(manager):
    manager.disconnect_student("ghost")  # should not raise


async def test_notify_teachers_sends_to_all(manager):
    ws1, ws2 = _make_ws(), _make_ws()
    await manager.connect_teacher("a", ws1)
    await manager.connect_teacher("a", ws2)
    payload = {"event": "test"}
    await manager.notify_teachers("a", payload)
    ws1.send_json.assert_awaited_once_with(payload)
    ws2.send_json.assert_awaited_once_with(payload)


async def test_notify_teachers_skips_dead_connections(manager):
    ws = _make_ws()
    ws.send_json = AsyncMock(side_effect=RuntimeError("broken"))
    await manager.connect_teacher("a", ws)
    await manager.notify_teachers("a", {"event": "x"})  # should not raise
    assert ws not in manager._teachers.get("a", [])


async def test_notify_teachers_empty_assignment_is_noop(manager):
    await manager.notify_teachers("unknown", {"event": "x"})  # no raise


async def test_notify_student_sends_message(manager):
    ws = _make_ws()
    await manager.connect_student("s1", "a1", ws)
    payload = {"event": "next"}
    await manager.notify_student("s1", payload)
    ws.send_json.assert_awaited_once_with(payload)


async def test_notify_student_unknown_is_noop(manager):
    await manager.notify_student("ghost", {"event": "x"})  # no raise


async def test_notify_all_students_sends_to_matching_assignment(manager):
    ws1, ws2, ws3 = _make_ws(), _make_ws(), _make_ws()
    await manager.connect_student("s1", "a1", ws1)
    await manager.connect_student("s2", "a1", ws2)
    await manager.connect_student("s3", "a2", ws3)

    payload = {"event": "finished"}
    await manager.notify_all_students("a1", payload)

    ws1.send_json.assert_awaited_once_with(payload)
    ws2.send_json.assert_awaited_once_with(payload)
    ws3.send_json.assert_not_called()


async def test_student_count(manager):
    ws1, ws2, ws3 = _make_ws(), _make_ws(), _make_ws()
    await manager.connect_student("s1", "a1", ws1)
    await manager.connect_student("s2", "a1", ws2)
    await manager.connect_student("s3", "a2", ws3)

    assert manager.student_count("a1") == 2
    assert manager.student_count("a2") == 1
    assert manager.student_count("no-assign") == 0


async def test_multiple_teachers_same_assignment(manager):
    ws1, ws2 = _make_ws(), _make_ws()
    await manager.connect_teacher("a1", ws1)
    await manager.connect_teacher("a1", ws2)
    assert len(manager._teachers["a1"]) == 2