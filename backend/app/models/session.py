from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.database import Base


class StudentSession(Base):
    __tablename__ = "student_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    student_name = Column(String(255), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    progress_data = Column(JSON, nullable=True)

    assignment = relationship("Assignment", back_populates="sessions")
    responses = relationship("StudentResponse", back_populates="student_session")


class StudentResponse(Base):
    __tablename__ = "student_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    student_session_id = Column(String(36), ForeignKey("student_sessions.id"), nullable=False)
    question_index = Column(String(50), nullable=True)
    question_difficulty = Column(String(10), nullable=True)
    answer_data = Column(JSON, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    teacher_grade = Column(String(20), nullable=True)
    score = Column(String(10), nullable=True)
    answered_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="responses")
    student_session = relationship("StudentSession", back_populates="responses")
