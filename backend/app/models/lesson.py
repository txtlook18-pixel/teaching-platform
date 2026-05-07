from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.database import Base


class SourceType(str, enum.Enum):
    URL = "url"
    FILE = "file"
    TEXT = "text"


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    language = Column(String(10), default="ru")
    source_type = Column(
        Enum(SourceType, values_callable=lambda x: [e.value for e in x]),
        default=SourceType.TEXT,
    )
    source_content = Column(Text, nullable=True)
    cluster_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = relationship("User", back_populates="lessons")
    assignments = relationship("Assignment", back_populates="lesson", cascade="all, delete-orphan")
