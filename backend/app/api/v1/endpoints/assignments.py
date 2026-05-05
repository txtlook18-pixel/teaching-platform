import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.database import get_db
from app.models.lesson import Lesson
from app.models.assignment import Assignment, AssignmentStatus
from app.models.session import StudentSession, StudentResponse
from app.schemas.assignment import (
    AssignmentCreate, AssignmentResponse,
    StudentJoinRequest, StudentAnswerRequest, TeacherGradeRequest,
)
from app.core.security import get_current_user_id
from app.providers.factory import get_ai_provider

router = APIRouter(prefix="/assignments", tags=["assignments"])


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
    content = lesson.source_content or ""
    topic = lesson.cluster_data.get("main_topic", lesson.title) if lesson.cluster_data else lesson.title

    atype = assignment.assignment_type.value
    if atype == "test":
        questions = await ai.generate_questions(
            topic=topic, content=content,
            difficulty_levels=["easy", "medium", "hard"],
            count=assignment.question_count, language=lesson.language,
        )
        assignment.questions_data = {"questions": questions, "type": "test"}

    elif atype == "battle":
        cases = await ai.generate_cases(topic=topic, content=content, case_type="battle", language=lesson.language)
        assignment.questions_data = {"cases": cases, "type": "battle"}

    elif atype == "analysis":
        cases = await ai.generate_cases(topic=topic, content=content, case_type="analysis", language=lesson.language)
        assignment.questions_data = {"cases": cases, "type": "analysis"}

    elif atype == "cards":
        cards = await ai.generate_flashcards(content=content, count=assignment.question_count, language=lesson.language)
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

    return {
        "session_id": session.id,
        "assignment_id": assignment.id,
        "assignment_type": assignment.assignment_type,
        "questions_data": assignment.questions_data,
        "timer_seconds": assignment.timer_seconds,
    }


@router.post("/answer")
async def submit_answer(data: StudentAnswerRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudentSession).where(StudentSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    response = StudentResponse(
        assignment_id=session.assignment_id,
        student_session_id=session.id,
        question_index=data.question_index,
        question_difficulty=data.question_difficulty,
        answer_data=data.answer_data,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return {"response_id": response.id, "status": "recorded"}


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
    return {"status": "finished"}
