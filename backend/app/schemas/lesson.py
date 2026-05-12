from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime
from app.models.lesson import SourceType


class SourceMeta(BaseModel):
    name: str
    type: str  # "file" | "url" | "text"
    size: Optional[int] = None


class LessonCreate(BaseModel):
    title: str
    language: str = "ru"
    source_type: SourceType = SourceType.TEXT
    source_content: Optional[str] = None
    sources_metadata: Optional[List[SourceMeta]] = None


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None
    source_type: Optional[SourceType] = None
    source_content: Optional[str] = None


class LessonResponse(BaseModel):
    id: str
    teacher_id: str
    title: str
    language: str
    source_type: SourceType
    source_content: Optional[str] = None
    cluster_data: Optional[Dict[str, Any]] = None
    sources_metadata: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
