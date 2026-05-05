from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.database import Base


class AssignmentType(str, enum.Enum):
    TEST = "test"
    BATTLE = "battle"
    ANALYSIS = "analysis"
    CARDS = "cards"
    RETELLING = "retelling"


class AssignmentStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"
    ARCHIVED = "archived"


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String(36), ForeignKey("lessons.id"), nullable=False)
    assignment_type = Column(Enum(AssignmentType), nullable=False)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.DRAFT)
    questions_data = Column(JSON, nullable=True)
    settings_data = Column(JSON, nullable=True)
    session_token = Column(String(255), unique=True, nullable=True)
    session_expires_at = Column(DateTime, nullable=True)
    question_count = Column(Integer, default=10)
    timer_seconds = Column(Integer, default=60)
    show_results = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lesson = relationship("Lesson", back_populates="assignments")
    responses = relationship("StudentResponse", back_populates="assignment", cascade="all, delete-orphan")
    sessions = relationship("StudentSession", back_populates="assignment", cascade="all, delete-orphan")
