from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime
from app.models.assignment import AssignmentType, AssignmentStatus


class AssignmentCreate(BaseModel):
    assignment_type: AssignmentType
    question_count: int = 10
    timer_seconds: int = 60
    settings_data: Optional[Dict[str, Any]] = None


class AssignmentResponse(BaseModel):
    id: str
    lesson_id: str
    assignment_type: AssignmentType
    status: AssignmentStatus
    questions_data: Optional[Any] = None
    settings_data: Optional[Dict[str, Any]] = None
    session_token: Optional[str] = None
    session_expires_at: Optional[datetime] = None
    question_count: int
    timer_seconds: int
    show_results: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentJoinRequest(BaseModel):
    student_name: str
    session_token: str


class StudentAnswerRequest(BaseModel):
    session_id: str
    question_index: str
    answer_data: Dict[str, Any]
    question_difficulty: Optional[str] = None


class TeacherGradeRequest(BaseModel):
    response_id: str
    grade: str
    comment: Optional[str] = None
