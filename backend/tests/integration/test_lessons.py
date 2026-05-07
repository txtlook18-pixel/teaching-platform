from unittest.mock import AsyncMock, patch


# --- create ---

async def test_create_lesson_success(client, auth_headers):
    r = await client.post("/api/v1/lessons/", json={
        "title": "Photosynthesis",
        "language": "en",
        "source_type": "text",
        "source_content": "Photosynthesis is the process...",
    }, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Photosynthesis"
    assert data["language"] == "en"
    assert data["status"] if "status" in data else True  # optional field


async def test_create_lesson_requires_auth(client):
    r = await client.post("/api/v1/lessons/", json={"title": "X", "source_content": "Y"})
    assert r.status_code in (401, 403)


async def test_create_lesson_defaults(client, auth_headers):
    r = await client.post("/api/v1/lessons/", json={
        "title": "Minimal Lesson",
        "source_content": "Some content.",
    }, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["language"] == "ru"
    assert data["source_type"] == "text"


# --- list ---

async def test_list_lessons_empty(client, auth_headers):
    r = await client.get("/api/v1/lessons/", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


async def test_list_lessons_returns_own_only(client, auth_headers, test_lesson):
    r = await client.get("/api/v1/lessons/", headers=auth_headers)
    assert r.status_code == 200
    ids = [l["id"] for l in r.json()]
    assert test_lesson.id in ids


async def test_list_lessons_other_user_not_visible(client, test_lesson):
    # Register a second user and verify they cannot see test_lesson
    reg = await client.post("/api/v1/auth/register", json={
        "email": "other@test.com", "username": "Other", "password": "pass1234",
    })
    other_token = reg.json()["access_token"]
    r = await client.get("/api/v1/lessons/", headers={"Authorization": f"Bearer {other_token}"})
    assert r.status_code == 200
    assert all(l["id"] != test_lesson.id for l in r.json())


# --- get single ---

async def test_get_lesson_success(client, auth_headers, test_lesson):
    r = await client.get(f"/api/v1/lessons/{test_lesson.id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == test_lesson.id
    assert r.json()["title"] == test_lesson.title


async def test_get_lesson_not_found(client, auth_headers):
    r = await client.get("/api/v1/lessons/no-such-id", headers=auth_headers)
    assert r.status_code == 404


async def test_get_lesson_other_user_forbidden(client, test_lesson):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "spy@test.com", "username": "Spy", "password": "pass1234",
    })
    spy_token = reg.json()["access_token"]
    r = await client.get(
        f"/api/v1/lessons/{test_lesson.id}",
        headers={"Authorization": f"Bearer {spy_token}"},
    )
    assert r.status_code == 404


# --- update ---

async def test_update_lesson_success(client, auth_headers, test_lesson):
    r = await client.put(f"/api/v1/lessons/{test_lesson.id}", json={
        "title": "Updated Title",
        "language": "en",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "Updated Title"
    assert r.json()["language"] == "en"


async def test_update_lesson_partial(client, auth_headers, test_lesson):
    original_content = test_lesson.source_content
    r = await client.put(f"/api/v1/lessons/{test_lesson.id}", json={
        "title": "Only Title Changed",
    }, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "Only Title Changed"
    assert r.json()["source_content"] == original_content


async def test_update_lesson_not_found(client, auth_headers):
    r = await client.put("/api/v1/lessons/no-such", json={"title": "X"}, headers=auth_headers)
    assert r.status_code == 404


# --- delete ---

async def test_delete_lesson_success(client, auth_headers, db):
    from app.models.lesson import Lesson
    from app.models.lesson import SourceType
    lesson = Lesson(
        teacher_id=(await _get_user_id(client, auth_headers)),
        title="To Delete",
        source_content="bye",
        source_type=SourceType.TEXT,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)

    r = await client.delete(f"/api/v1/lessons/{lesson.id}", headers=auth_headers)
    assert r.status_code == 200

    r2 = await client.get(f"/api/v1/lessons/{lesson.id}", headers=auth_headers)
    assert r2.status_code == 404


async def test_delete_lesson_not_found(client, auth_headers):
    r = await client.delete("/api/v1/lessons/no-such", headers=auth_headers)
    assert r.status_code == 404


# --- analyze ---

async def test_analyze_lesson_success(client, auth_headers, test_lesson):
    mock_cluster = {"main_topic": "Python", "subtopics": ["syntax", "loops"]}
    with patch("app.api.v1.endpoints.lessons.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.analyze_content = AsyncMock(return_value=mock_cluster)
        mock_factory.return_value = mock_ai
        r = await client.post(
            f"/api/v1/lessons/{test_lesson.id}/analyze",
            headers=auth_headers,
        )
    assert r.status_code == 200
    assert r.json()["cluster_data"] == mock_cluster


async def test_analyze_lesson_no_content(client, auth_headers, db):
    from app.models.lesson import Lesson, SourceType
    lesson = Lesson(
        teacher_id=(await _get_user_id(client, auth_headers)),
        title="Empty",
        source_content=None,
        source_type=SourceType.TEXT,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)

    r = await client.post(f"/api/v1/lessons/{lesson.id}/analyze", headers=auth_headers)
    assert r.status_code == 400


async def test_analyze_lesson_not_found(client, auth_headers):
    r = await client.post("/api/v1/lessons/no-such/analyze", headers=auth_headers)
    assert r.status_code == 404


# --- list ordering ---

async def test_list_lessons_ordered_by_newest(client, auth_headers):
    for title in ["First", "Second", "Third"]:
        await client.post("/api/v1/lessons/", json={
            "title": title, "source_content": "x",
        }, headers=auth_headers)

    r = await client.get("/api/v1/lessons/", headers=auth_headers)
    titles = [l["title"] for l in r.json()]
    assert titles.index("Third") < titles.index("Second") < titles.index("First")


# --- helper ---

async def _get_user_id(client, auth_headers) -> str:
    r = await client.get("/api/v1/auth/me", headers=auth_headers)
    return r.json()["id"]
