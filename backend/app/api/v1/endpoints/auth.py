import secrets
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import redis.asyncio as aioredis
from app.db.database import get_db
from app.models.user import User
from app.models.lesson import Lesson
from app.models.assignment import Assignment
from app.models.session import StudentSession, StudentResponse
from app.schemas.user import UserLogin, UserResponse, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.core.security import hash_password, verify_password, create_access_token, get_current_user_id
from app.core.email import send_password_reset_email
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

RESET_TOKEN_TTL = 3600  # 1 hour


def _redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=True)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@router.get("/stats")
async def get_stats(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    lesson_ids_sq = select(Lesson.id).where(Lesson.teacher_id == user_id).scalar_subquery()
    assignment_ids_sq = select(Assignment.id).where(Assignment.lesson_id.in_(lesson_ids_sq)).scalar_subquery()

    lesson_count = await db.scalar(select(func.count()).where(Lesson.teacher_id == user_id))
    assignment_count = await db.scalar(select(func.count()).where(Assignment.lesson_id.in_(lesson_ids_sq)))
    session_count = await db.scalar(select(func.count()).where(StudentSession.assignment_id.in_(assignment_ids_sq)))
    response_count = await db.scalar(select(func.count()).where(StudentResponse.assignment_id.in_(assignment_ids_sq)))

    return {
        "total_lessons": lesson_count or 0,
        "total_assignments": assignment_count or 0,
        "total_student_sessions": session_count or 0,
        "total_responses": response_count or 0,
    }


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user:
        reset_token = secrets.token_urlsafe(32)
        redis = _redis_client()
        try:
            await redis.set(f"pwd_reset:{reset_token}", user.id, ex=RESET_TOKEN_TTL)
        finally:
            await redis.aclose()

        try:
            await send_password_reset_email(user.email, reset_token)
        except Exception:
            logger.exception("Failed to send password reset email to %s", user.email)

    # Always return success to avoid leaking whether email exists
    return {"message": "Если email зарегистрирован, на него отправлена ссылка для сброса пароля"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    redis = _redis_client()
    try:
        user_id = await redis.get(f"pwd_reset:{data.token}")
    finally:
        await redis.aclose()

    if not user_id:
        raise HTTPException(status_code=400, detail="Ссылка недействительна или истёк срок действия")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()

    # Invalidate the token
    redis = _redis_client()
    try:
        await redis.delete(f"pwd_reset:{data.token}")
    finally:
        await redis.aclose()

    return {"message": "Пароль успешно изменён"}
