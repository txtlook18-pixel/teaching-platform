from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.user import User
from app.models.lesson import Lesson
from app.models.assignment import Assignment
from app.models.session import StudentSession, StudentResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        telegram_username=user_data.telegram_username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

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
        raise HTTPException(status_code=404, detail="User not found")
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
