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
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse
from app.core.security import get_current_user_id
from app.providers.factory import get_ai_provider


class ExtraTopicsRequest(BaseModel):
    exclude: List[str] = []
    count: int = 5

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


@router.post("/extract-text")
async def extract_text_from_files(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """Extract text from uploaded files. Supports TXT, MD, PDF, DOCX. Max 20 MB each."""
    if not files:
        raise HTTPException(status_code=400, detail="error.no_files")

    parts: list[str] = []
    for f in files:
        raw = await f.read()

        if len(raw) > _MAX_FILE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f'error.file_too_large:{f.filename}',
            )

        ext = os.path.splitext(f.filename or "")[1].lower()
        if ext not in _SUPPORTED_EXT:
            raise HTTPException(
                status_code=400,
                detail=f'error.unsupported_format:{f.filename}',
            )

        if ext in (".txt", ".md"):
            text = raw.decode("utf-8", errors="replace")
        elif ext == ".pdf":
            try:
                import fitz  # pymupdf
                doc = fitz.open(stream=raw, filetype="pdf")
                text = "\n".join(page.get_text() for page in doc)
                doc.close()
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f'error.pdf_read_error:{f.filename}:{exc}')
        else:  # .docx
            try:
                from docx import Document
                doc = Document(io.BytesIO(raw))
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f'error.docx_read_error:{f.filename}:{exc}')

        parts.append(text.strip())

    combined = "\n\n---\n\n".join(parts)
    return {"text": combined[:50000], "file_count": len(parts)}


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


async def _fetch_url_text(url: str) -> str:
    """Download a URL and return its plain-text content (strips HTML tags)."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "TeachingPlatformBot/1.0"})
        resp.raise_for_status()
    text = resp.text
    # Strip HTML tags
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
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not fetch URL: {exc}")

    lesson.source_content = text
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
