import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.lesson import Lesson, SourceType
from app.models.assignment import Assignment, AssignmentType


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db):
    user = User(
        email="teacher@test.com",
        username="Teacher",
        hashed_password=hash_password("secret123"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    token = create_access_token({"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_lesson(db, test_user):
    lesson = Lesson(
        teacher_id=test_user.id,
        title="Test Lesson",
        source_content="Python programming fundamentals.",
        language="en",
        source_type=SourceType.TEXT,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@pytest_asyncio.fixture
async def test_assignment(db, test_lesson):
    assignment = Assignment(
        lesson_id=test_lesson.id,
        assignment_type=AssignmentType.TEST,
        question_count=5,
        timer_seconds=30,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment
