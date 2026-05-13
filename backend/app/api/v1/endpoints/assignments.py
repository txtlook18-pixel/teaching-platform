import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.db.database import get_db
from app.models.lesson import Lesson, LessonSource
from app.models.assignment import Assignment, AssignmentStatus
from app.models.session import StudentSession, StudentResponse
from app.schemas.assignment import (
    AssignmentCreate, AssignmentResponse,
    StudentJoinRequest, StudentAnswerRequest, TeacherGradeRequest,
    ChatRequest, GenerateRequest,
)
from app.models.assignment import AssignmentType
from app.core.security import get_current_user_id
from app.providers.factory import get_ai_provider
from app.ws.manager import manager as ws_manager
from app.api.v1.endpoints.lessons import _fetch_url_text

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("/lessons/{lesson_id}/assignments")
async def list_assignments(
    lesson_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lesson not found")

    res = await db.execute(
        select(Assignment).where(Assignment.lesson_id == lesson_id)
    )
    assignments = res.scalars().all()
    return [AssignmentResponse.model_validate(a) for a in assignments]


@router.get("/history")
async def list_assignment_history(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """All assignments across all teacher's lessons, newest first."""
    result = await db.execute(
        select(Assignment, Lesson)
        .join(Lesson)
        .where(Lesson.teacher_id == user_id)
        .order_by(Assignment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()

    if not rows:
        return []

    assignment_ids = [a.id for a, _ in rows]

    sess_counts_result = await db.execute(
        select(StudentSession.assignment_id, func.count().label("cnt"))
        .where(StudentSession.assignment_id.in_(assignment_ids))
        .group_by(StudentSession.assignment_id)
    )
    sess_map = {r.assignment_id: r.cnt for r in sess_counts_result}

    resp_counts_result = await db.execute(
        select(StudentResponse.assignment_id, func.count().label("cnt"))
        .where(StudentResponse.assignment_id.in_(assignment_ids))
        .group_by(StudentResponse.assignment_id)
    )
    resp_map = {r.assignment_id: r.cnt for r in resp_counts_result}

    return [
        {
            "id": a.id,
            "lesson_id": lesson.id,
            "lesson_title": lesson.title,
            "assignment_type": a.assignment_type.value,
            "status": a.status.value,
            "question_count": a.question_count,
            "student_count": sess_map.get(a.id, 0),
            "response_count": resp_map.get(a.id, 0),
            "created_at": a.created_at,
        }
        for a, lesson in rows
    ]


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment, Lesson).join(Lesson).where(
            Assignment.id == assignment_id, Lesson.teacher_id == user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment, _ = row
    return AssignmentResponse.model_validate(assignment)


@router.post("/lessons/{lesson_id}/assignments", response_model=AssignmentResponse)
async def create_assignment(
    lesson_id: str,
    data: AssignmentCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.teacher_id == user_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    assignment = Assignment(
        lesson_id=lesson_id,
        assignment_type=data.assignment_type,
        question_count=data.question_count,
        timer_seconds=data.timer_seconds,
        settings_data=data.settings_data,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return AssignmentResponse.model_validate(assignment)


@router.post("/{assignment_id}/generate")
async def generate_content(
    assignment_id: str,
    body: GenerateRequest = GenerateRequest(),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment, Lesson).join(Lesson).where(
            Assignment.id == assignment_id, Lesson.teacher_id == user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment, lesson = row

    ai = get_ai_provider()

    # Build content from enabled sources only; fall back to full source_content
    sources_result = await db.execute(
        select(LessonSource).where(LessonSource.lesson_id == lesson.id)
    )
    enabled_map = {r.source_name: r.enabled for r in sources_result.scalars().all()}

    metadata = lesson.sources_metadata or []
    if metadata:
        enabled_sources = [
            s for s in metadata
            if not s.get("fetch_error")
            and enabled_map.get(s.get("name"), False)
        ]
        parts: list[str] = []
        for s in enabled_sources:
            text: str = s.get("content") or ""
            if not text and s.get("type") == "url" and s.get("name"):
                try:
                    text = await _fetch_url_text(s["name"])
                except Exception:
                    text = ""
            if text:
                parts.append(text)
        content = "\n\n---\n\n".join(parts) if parts else (lesson.source_content or "")
    else:
        content = lesson.source_content or ""

    topic = lesson.cluster_data.get("main_topic", lesson.title) if lesson.cluster_data else lesson.title

    atype = assignment.assignment_type.value
    if atype == "test":
        prev_res = await db.execute(
            select(Assignment).where(
                Assignment.lesson_id == assignment.lesson_id,
                Assignment.assignment_type == AssignmentType.TEST,
                Assignment.questions_data.isnot(None),
            )
        )
        used_questions = [
            q["question"]
            for a in prev_res.scalars().all()
            if a.questions_data and "questions" in a.questions_data
            for q in a.questions_data["questions"]
            if "question" in q
        ]
        questions = await ai.generate_questions(
            topic=topic, content=content,
            difficulty_levels=["easy", "medium", "hard"],
            count=assignment.question_count, language=lesson.language,
            exclude_questions=used_questions,
        )
        assignment.questions_data = {"questions": questions, "type": "test"}

    elif atype == "battle":
        prev_battles = await db.execute(
            select(Assignment).where(
                Assignment.lesson_id == assignment.lesson_id,
                Assignment.assignment_type == AssignmentType.BATTLE,
                Assignment.questions_data.isnot(None),
                Assignment.id != assignment_id,
            )
        )
        exclude_cases = [
            c["title"]
            for a in prev_battles.scalars().all()
            if a.questions_data and "cases" in a.questions_data
            for c in a.questions_data["cases"]
            if "title" in c
        ]
        cases = await ai.generate_cases(
            topic=topic, content=content, case_type="battle",
            language=lesson.language, exclude_cases=exclude_cases,
        )
        assignment.questions_data = {"cases": cases, "type": "battle"}

    elif atype == "analysis":
        analysis_topic = (assignment.settings_data or {}).get("topic") or topic
        cases = await ai.generate_cases(topic=analysis_topic, content=content, case_type="analysis", language=lesson.language)
        assignment.questions_data = {"cases": cases, "type": "analysis", "topic": analysis_topic}

    elif atype == "cards":
        cards = await ai.generate_flashcards(
            content=content,
            count=assignment.question_count,
            language=lesson.language,
            exclude_terms=body.exclude_terms,
        )
        assignment.questions_data = {"cards": cards, "type": "cards"}

    elif atype == "retelling":
        retelling = await ai.generate_reference_retelling(content=content, topic=topic, language=lesson.language)
        assignment.questions_data = {"reference": retelling, "topic": topic, "type": "retelling"}

    await db.commit()
    await db.refresh(assignment)
    return {"status": "generated", "assignment_id": assignment_id}


@router.post("/{assignment_id}/activate")
async def activate_assignment(
    assignment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment, Lesson).join(Lesson).where(
            Assignment.id == assignment_id, Lesson.teacher_id == user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment, _ = row
    assignment.status = AssignmentStatus.ACTIVE
    assignment.session_token = secrets.token_urlsafe(32)
    assignment.session_expires_at = datetime.utcnow() + timedelta(minutes=15)

    await db.commit()
    await db.refresh(assignment)
    return {
        "session_token": assignment.session_token,
        "expires_at": assignment.session_expires_at,
        "assignment_id": assignment_id,
    }


@router.post("/join")
async def student_join(data: StudentJoinRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Assignment).where(Assignment.session_token == data.session_token)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=404, detail="Invalid session token")
    if assignment.status != AssignmentStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")
    if assignment.session_expires_at and assignment.session_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Session expired")

    result2 = await db.execute(
        select(StudentSession).where(
            StudentSession.assignment_id == assignment.id,
            StudentSession.student_name == data.student_name,
        )
    )
    if result2.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Name already taken in this session")

    session = StudentSession(
        assignment_id=assignment.id,
        student_name=data.student_name,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Notify teacher live
    await ws_manager.notify_teachers(str(assignment.id), {
        "event": "student_joined",
        "session_id": session.id,
        "student_name": data.student_name,
    })

    return {
        "session_id": session.id,
        "assignment_id": assignment.id,
        "assignment_type": assignment.assignment_type,
        "questions_data": assignment.questions_data,
        "timer_seconds": assignment.timer_seconds,
        "settings_data": assignment.settings_data,
        "student_name": data.student_name,
    }


@router.post("/answer")
async def submit_answer(data: StudentAnswerRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudentSession).where(StudentSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Auto-grade TEST answers (frontend sends is_correct in answer_data)
    is_correct = None
    if isinstance(data.answer_data, dict) and "is_correct" in data.answer_data:
        is_correct = bool(data.answer_data["is_correct"])

    response = StudentResponse(
        assignment_id=session.assignment_id,
        student_session_id=session.id,
        question_index=data.question_index,
        question_difficulty=data.question_difficulty,
        answer_data=data.answer_data,
        is_correct=is_correct,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)

    # Notify teacher of new answer
    await ws_manager.notify_teachers(str(session.assignment_id), {
        "event": "student_answered",
        "session_id": session.id,
        "question_index": data.question_index,
        "is_correct": is_correct,
    })

    return {"response_id": response.id, "status": "recorded", "is_correct": is_correct}


@router.get("/{assignment_id}/results")
async def get_results(
    assignment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment, Lesson).join(Lesson).where(
            Assignment.id == assignment_id, Lesson.teacher_id == user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")

    sessions_result = await db.execute(
        select(StudentSession).where(StudentSession.assignment_id == assignment_id)
    )
    sessions = sessions_result.scalars().all()

    responses_result = await db.execute(
        select(StudentResponse).where(StudentResponse.assignment_id == assignment_id)
    )
    responses = responses_result.scalars().all()

    return {
        "assignment_id": assignment_id,
        "student_count": len(sessions),
        "sessions": [
            {"id": s.id, "student_name": s.student_name, "joined_at": s.joined_at}
            for s in sessions
        ],
        "responses": [
            {
                "id": r.id,
                "student_session_id": r.student_session_id,
                "question_index": r.question_index,
                "question_difficulty": r.question_difficulty,
                "answer_data": r.answer_data,
                "is_correct": r.is_correct,
                "teacher_grade": r.teacher_grade,
                "answered_at": r.answered_at,
            }
            for r in responses
        ],
    }


@router.post("/{assignment_id}/finish")
async def finish_assignment(
    assignment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment, Lesson).join(Lesson).where(
            Assignment.id == assignment_id, Lesson.teacher_id == user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment, _ = row
    assignment.status = AssignmentStatus.FINISHED
    assignment.show_results = True
    await db.commit()

    # Notify all connected students
    await ws_manager.notify_all_students(assignment_id, {"event": "assignment_finished"})

    return {"status": "finished"}


@router.post("/{assignment_id}/chat")
async def retelling_chat(
    assignment_id: str,
    data: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment, Lesson).join(Lesson).where(
            Assignment.id == assignment_id, Lesson.teacher_id == user_id
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment, lesson = row
    if assignment.assignment_type.value != "retelling":
        raise HTTPException(status_code=400, detail="Chat only available for retelling assignments")

    ai = get_ai_provider()
    content = lesson.source_content or ""
    topic = lesson.cluster_data.get("main_topic", lesson.title) if lesson.cluster_data else lesson.title

    history = [{"role": m.role, "content": m.content} for m in data.history]
    reply = await ai.chat_response(
        content=content,
        topic=topic,
        history=history,
        message=data.message,
        language=lesson.language,
    )
    return {"reply": reply}


@router.post("/{assignment_id}/responses/{response_id}/grade")
async def grade_response(
    assignment_id: str,
    response_id: str,
    data: TeacherGradeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assignment, Lesson).join(Lesson).where(
            Assignment.id == assignment_id, Lesson.teacher_id == user_id
        )
    )
    if not result.first():
        raise HTTPException(status_code=404, detail="Assignment not found")

    res = await db.execute(
        select(StudentResponse).where(
            StudentResponse.id == response_id,
            StudentResponse.assignment_id == assignment_id,
        )
    )
    response = res.scalar_one_or_none()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    response.teacher_grade = data.grade
    response.is_correct = data.is_correct
    await db.commit()
    return {"status": "graded", "response_id": response_id}
