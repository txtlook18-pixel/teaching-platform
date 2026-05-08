"""Extended lesson tests covering file upload, URL fetch, and upload-file endpoints."""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


# --- extract-text endpoint ---

async def test_extract_text_txt_file(client, auth_headers):
    content = b"Hello world, this is a text file."
    r = await client.post(
        "/api/v1/lessons/extract-text",
        files=[("files", ("doc.txt", io.BytesIO(content), "text/plain"))],
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "Hello world" in data["text"]
    assert data["file_count"] == 1


async def test_extract_text_md_file(client, auth_headers):
    content = b"# Title\n\nSome markdown content."
    r = await client.post(
        "/api/v1/lessons/extract-text",
        files=[("files", ("readme.md", io.BytesIO(content), "text/markdown"))],
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert "Title" in r.json()["text"]


async def test_extract_text_unsupported_format(client, auth_headers):
    r = await client.post(
        "/api/v1/lessons/extract-text",
        files=[("files", ("image.png", io.BytesIO(b"\x89PNG"), "image/png"))],
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "неподдерживаемый формат" in r.json()["detail"]


async def test_extract_text_multiple_files(client, auth_headers):
    files = [
        ("files", ("a.txt", io.BytesIO(b"Content A"), "text/plain")),
        ("files", ("b.txt", io.BytesIO(b"Content B"), "text/plain")),
    ]
    r = await client.post(
        "/api/v1/lessons/extract-text",
        files=files,
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["file_count"] == 2
    assert "Content A" in data["text"]
    assert "Content B" in data["text"]


async def test_extract_text_requires_auth(client):
    r = await client.post(
        "/api/v1/lessons/extract-text",
        files=[("files", ("doc.txt", io.BytesIO(b"text"), "text/plain"))],
    )
    assert r.status_code in (401, 403)


async def test_extract_text_pdf_file(client, auth_headers):
    """Test PDF extraction path via sys.modules mock (fitz imported inside function)."""
    import sys

    mock_page = MagicMock()
    mock_page.get_text.return_value = "PDF page text"

    mock_doc = MagicMock()
    mock_doc.__iter__ = MagicMock(side_effect=lambda: iter([mock_page]))
    mock_doc.close = MagicMock()

    mock_fitz = MagicMock()
    mock_fitz.open.return_value = mock_doc

    with patch.dict(sys.modules, {"fitz": mock_fitz}):
        r = await client.post(
            "/api/v1/lessons/extract-text",
            files=[("files", ("doc.pdf", io.BytesIO(b"%PDF fake"), "application/pdf"))],
            headers=auth_headers,
        )
    assert r.status_code == 200
    assert "PDF page text" in r.json()["text"]


# --- fetch-url endpoint ---

async def test_fetch_url_success(client, auth_headers, db, test_user):
    from app.models.lesson import Lesson, SourceType

    lesson = Lesson(
        teacher_id=test_user.id,
        title="URL Lesson",
        source_content="https://example.com",
        source_type=SourceType.URL,
        language="en",
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)

    mock_response = MagicMock()
    mock_response.text = "<html><body><p>Fetched content from web.</p></body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("app.api.v1.endpoints.lessons._fetch_url_text", new=AsyncMock(return_value="Fetched content from web.")):
        r = await client.post(
            f"/api/v1/lessons/{lesson.id}/fetch-url",
            headers=auth_headers,
        )

    assert r.status_code == 200
    assert "Fetched content" in r.json()["source_content"]


async def test_fetch_url_not_found(client, auth_headers):
    r = await client.post(
        "/api/v1/lessons/no-such-id/fetch-url",
        headers=auth_headers,
    )
    assert r.status_code == 404


async def test_fetch_url_wrong_source_type(client, auth_headers, test_lesson):
    """Lesson with source_type=text should reject fetch-url."""
    r = await client.post(
        f"/api/v1/lessons/{test_lesson.id}/fetch-url",
        headers=auth_headers,
    )
    assert r.status_code == 400


async def test_fetch_url_network_error(client, auth_headers, db, test_user):
    from app.models.lesson import Lesson, SourceType

    lesson = Lesson(
        teacher_id=test_user.id,
        title="Bad URL Lesson",
        source_content="https://nonexistent.example.invalid",
        source_type=SourceType.URL,
        language="en",
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)

    with patch(
        "app.api.v1.endpoints.lessons._fetch_url_text",
        new=AsyncMock(side_effect=Exception("Connection refused")),
    ):
        r = await client.post(
            f"/api/v1/lessons/{lesson.id}/fetch-url",
            headers=auth_headers,
        )

    assert r.status_code == 422
    assert "Could not fetch URL" in r.json()["detail"]


# --- upload-file endpoint ---

async def test_upload_file_success(client, auth_headers, test_lesson):
    content = b"This is the uploaded lesson content."
    r = await client.post(
        f"/api/v1/lessons/{test_lesson.id}/upload-file",
        files={"file": ("material.txt", io.BytesIO(content), "text/plain")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "uploaded lesson content" in data["source_content"]
    assert data["source_type"] == "file"


async def test_upload_file_not_found(client, auth_headers):
    r = await client.post(
        "/api/v1/lessons/no-such/upload-file",
        files={"file": ("x.txt", io.BytesIO(b"text"), "text/plain")},
        headers=auth_headers,
    )
    assert r.status_code == 404


async def test_upload_file_truncates_to_20000(client, auth_headers, test_lesson):
    big_content = b"A" * 30000
    r = await client.post(
        f"/api/v1/lessons/{test_lesson.id}/upload-file",
        files={"file": ("big.txt", io.BytesIO(big_content), "text/plain")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["source_content"]) <= 20000
