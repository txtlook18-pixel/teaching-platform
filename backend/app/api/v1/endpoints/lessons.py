import io
import os
import re
import httpx
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.database import get_db
from app.models.lesson import Lesson, LessonSource
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse
from app.core.security import get_current_user_id
from app.providers.factory import get_ai_provider


class ExtraTopicsRequest(BaseModel):
    exclude: List[str] = []
    count: int = 5

class FetchUrlTextRequest(BaseModel):
    url: str

class DetectLanguageRequest(BaseModel):
    text: str

class GenerateSummaryRequest(BaseModel):
    source_names: List[str] = []

class ToggleSourceRequest(BaseModel):
    source_name: str

_MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB
_SUPPORTED_EXT = {".txt", ".md", ".pdf", ".docx"}

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/", response_model=LessonResponse)
async def create_lesson(
    lesson_data: LessonCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    lesson = Lesson(
        teacher_id=user_id,
        title=lesson_data.title,
        language=lesson_data.language,
        source_type=lesson_data.source_type,
        source_content=lesson_data.source_content,
        sources_metadata=[s.model_dump() for s in lesson_data.sources_metadata] if lesson_data.sources_metadata else None,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


@router.get("/", response_model=List[LessonResponse])
async def list_lessons(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lesson).where(Lesson.teacher_id == user_id).order_by(Lesson.created_at.desc()))
    lessons = result.scalars().all()
    return [LessonResponse.model_validate(l) for l in lessons]


def _extract_file_text(raw: bytes, filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in _SUPPORTED_EXT:
        raise HTTPException(status_code=400, detail=f'error.unsupported_format:{filename}')
    if ext in (".txt", ".md"):
        return raw.decode("utf-8", errors="replace").strip()
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(stream=raw, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text.strip()
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f'error.pdf_read_error:{filename}:{exc}')
    try:
        from docx import Document
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f'error.docx_read_error:{filename}:{exc}')


@router.post("/fetch-url-text")
async def fetch_url_text(
    body: FetchUrlTextRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        text = await _fetch_url_text(body.url)
    except httpx.TimeoutException:
        raise HTTPException(status_code=422, detail="error.url_timeout")
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=422, detail="error.url_http_error")
    except Exception:
        raise HTTPException(status_code=422, detail="error.url_unreachable")
    return {"text": text}


@router.post("/extract-text")
async def extract_text_from_files(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """Extract text from uploaded files (combined). Supports TXT, MD, PDF, DOCX. Max 20 MB each."""
    if not files:
        raise HTTPException(status_code=400, detail="error.no_files")
    parts: list[str] = []
    for f in files:
        raw = await f.read()
        if len(raw) > _MAX_FILE_BYTES:
            raise HTTPException(status_code=400, detail=f'error.file_too_large:{f.filename}')
        parts.append(_extract_file_text(raw, f.filename or ""))
    combined = "\n\n---\n\n".join(parts)
    return {"text": combined[:50000], "file_count": len(parts)}


@router.post("/extract-text-per-file")
async def extract_text_per_file(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """Extract text per file, preserving individual file content. Max 20 MB each."""
    if not files:
        raise HTTPException(status_code=400, detail="error.no_files")
    result = []
    for f in files:
        raw = await f.read()
        if len(raw) > _MAX_FILE_BYTES:
            raise HTTPException(status_code=400, detail=f'error.file_too_large:{f.filename}')
        text = _extract_file_text(raw, f.filename or "")
        result.append({"filename": f.filename, "text": text[:20000]})
    return {"files": result}


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LessonResponse.model_validate(lesson)


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: str,
    lesson_data: LessonUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    for field, value in lesson_data.model_dump(exclude_none=True).items():
        setattr(lesson, field, value)

    await db.commit()
    await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    await db.delete(lesson)
    await db.commit()
    return {"detail": "Lesson deleted"}


_YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})", re.I
)
_VIMEO_RE = re.compile(r"vimeo\.com/(\d+)", re.I)


async def _fetch_oembed_text(url: str) -> str:
    """Return title+description from YouTube/Vimeo oEmbed (no scraping needed)."""
    yt_match = _YOUTUBE_RE.search(url)
    if yt_match:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={yt_match.group(1)}&format=json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(oembed_url)
            resp.raise_for_status()
        data = resp.json()
        return f"Video title: {data.get('title', '')}\nChannel: {data.get('author_name', '')}\nURL: {url}"

    vm_match = _VIMEO_RE.search(url)
    if vm_match:
        oembed_url = f"https://vimeo.com/api/oembed.json?url={url}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(oembed_url)
            resp.raise_for_status()
        data = resp.json()
        parts = [f"Video title: {data.get('title', '')}"]
        if data.get("description"):
            parts.append(data["description"][:2000])
        parts.append(f"URL: {url}")
        return "\n".join(parts)

    return ""


_VIDEO_HOSTS = re.compile(r"youtube\.com|youtu\.be|vimeo\.com|rutube\.ru|tiktok\.com|twitch\.tv", re.I)


async def _fetch_url_text(url: str) -> str:
    """Download a URL and return its plain-text content (strips HTML tags).
    For video hosting sites uses oEmbed instead of direct scraping."""
    if _VIDEO_HOSTS.search(url):
        return await _fetch_oembed_text(url)

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TeachingPlatformBot/1.0)"})
        resp.raise_for_status()
    text = resp.text
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s{3,}", "\n\n", text)
    return text.strip()[:20000]


@router.post("/{lesson_id}/fetch-url", response_model=LessonResponse)
async def fetch_lesson_url(
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Download content from the lesson's source_content URL and store it as text."""
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if lesson.source_type != "url" or not lesson.source_content:
        raise HTTPException(status_code=400, detail="Lesson source_type must be 'url'")

    try:
        text = await _fetch_url_text(lesson.source_content)
    except httpx.TimeoutException:
        raise HTTPException(status_code=422, detail="error.url_timeout")
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=422, detail="error.url_http_error")
    except Exception:
        raise HTTPException(status_code=422, detail="error.url_unreachable")

    if text:
        lesson.source_content = text
        await db.commit()
        await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


async def _check_url_accessible(url: str) -> bool:
    """HEAD-check a URL; falls back to GET if server doesn't support HEAD."""
    if _VIDEO_HOSTS.search(url):
        try:
            return bool(await _fetch_oembed_text(url))
        except Exception:
            return False
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.head(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; TeachingPlatformBot/1.0)"}
            )
            if resp.status_code == 405:
                resp = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (compatible; TeachingPlatformBot/1.0)"}
                )
            return resp.status_code < 400
    except Exception:
        return False


@router.post("/{lesson_id}/validate-url-sources", response_model=LessonResponse)
async def validate_url_sources(
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson or not lesson.sources_metadata:
        raise HTTPException(status_code=404, detail="Lesson not found")

    updated = []
    for src in lesson.sources_metadata:
        if src.get("type") == "url":
            ok = await _check_url_accessible(src.get("name", ""))
            updated.append({**src, "fetch_error": not ok})
        else:
            updated.append(src)

    lesson.sources_metadata = updated
    await db.commit()
    await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


@router.post("/{lesson_id}/upload-file", response_model=LessonResponse)
async def upload_lesson_file(
    lesson_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a plain-text file and store its content in the lesson."""
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    raw = await file.read()
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(status_code=422, detail="Cannot decode file as text")

    lesson.source_content = text[:20000]
    lesson.source_type = "file"
    await db.commit()
    await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


@router.post("/{lesson_id}/analyze", response_model=LessonResponse)
async def analyze_lesson(
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if not lesson.source_content:
        raise HTTPException(status_code=400, detail="No content to analyze")

    ai = get_ai_provider()
    cluster_data = await ai.analyze_content(lesson.source_content, lesson.language)
    lesson.cluster_data = cluster_data

    await db.commit()
    await db.refresh(lesson)
    return LessonResponse.model_validate(lesson)


@router.post("/detect-language")
async def detect_language(
    body: DetectLanguageRequest,
    user_id: str = Depends(get_current_user_id),
):
    text = body.text[:3000]
    alpha = sum(1 for c in text if c.isalpha())
    if alpha == 0:
        return {"language": "unknown", "supported": False}

    cyrillic = sum(1 for c in text if "Ѐ" <= c <= "ӿ")
    if cyrillic / alpha > 0.35:
        lang = "ru"
    else:
        lower = text.lower()
        if any(m in lower for m in ["o'zbek", "o'z", "oʻzbek", "gʻ", "oʻ"]):
            lang = "uz"
        else:
            lang = "en"

    return {"language": lang, "supported": lang in ("ru", "en", "uz")}


async def _source_content(src: dict) -> str:
    if src.get("content"):
        return src["content"]
    if src.get("type") == "url" and src.get("name") and not src.get("fetch_error"):
        try:
            return await _fetch_url_text(src["name"])
        except Exception:
            return ""
    return ""


@router.post("/{lesson_id}/generate-summary")
async def generate_summary(
    lesson_id: str,
    body: GenerateSummaryRequest = GenerateSummaryRequest(),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if not lesson.source_content and not lesson.sources_metadata:
        raise HTTPException(status_code=400, detail="error.no_content")

    content = lesson.source_content or ""
    if body.source_names and lesson.sources_metadata:
        target = set(body.source_names)
        parts = []
        for s in lesson.sources_metadata:
            if s.get("name") in target:
                text = await _source_content(s)
                if text:
                    parts.append(text)
        if parts:
            content = "\n\n---\n\n".join(parts)

    topic = (lesson.cluster_data or {}).get("main_topic", lesson.title)
    ai = get_ai_provider()
    summary = await ai.generate_reference_retelling(content, topic, lesson.language)
    return {"summary": summary}


@router.get("/{lesson_id}/sources")
async def get_lesson_sources(
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    db_rows = await db.execute(
        select(LessonSource).where(LessonSource.lesson_id == lesson_id)
    )
    enabled_map = {row.source_name: row.enabled for row in db_rows.scalars().all()}

    sources = lesson.sources_metadata or []
    return [
        {
            "name": s.get("name"),
            "enabled": enabled_map.get(s.get("name"), True),
        }
        for s in sources
        if not s.get("fetch_error")
    ]


@router.patch("/{lesson_id}/sources/toggle")
async def toggle_lesson_source(
    lesson_id: str,
    body: ToggleSourceRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lesson not found")

    source_name = body.source_name
    row_result = await db.execute(
        select(LessonSource).where(
            LessonSource.lesson_id == lesson_id,
            LessonSource.source_name == source_name,
        )
    )
    row = row_result.scalar_one_or_none()

    if row is None:
        row = LessonSource(lesson_id=lesson_id, source_name=source_name, enabled=False)
        db.add(row)
    else:
        row.enabled = not row.enabled

    await db.commit()
    return {"source_name": source_name, "enabled": row.enabled}


@router.post("/{lesson_id}/topics/more")
async def get_more_topics(
    lesson_id: str,
    body: ExtraTopicsRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if not lesson.source_content:
        raise HTTPException(status_code=400, detail="No content to analyze")

    main_topic = (lesson.cluster_data or {}).get("main_topic", lesson.title)
    ai = get_ai_provider()
    topics = await ai.generate_extra_topics(
        content=lesson.source_content,
        main_topic=main_topic,
        exclude_topics=body.exclude,
        count=body.count,
        language=lesson.language,
    )
    return {"topics": topics}
