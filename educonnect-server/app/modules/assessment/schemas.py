from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class QuestionStudentView(BaseModel):
    id: str
    question_type: str
    question_text: str
    options_json: Any | None = None
    marks: float
    sequence_number: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentStudentView(BaseModel):
    id: str
    title: str
    time_limit_seconds: int | None = None
    total_marks: float
    questions: list[QuestionStudentView]

    model_config = ConfigDict(from_attributes=True)


class AnswerSubmission(BaseModel):
    question_id: str
    answer_json: Any


class AttemptSubmitRequest(BaseModel):
    attempt_id: str
    device_id: str
    started_at: datetime
    submitted_at: datetime
    answers: list[AnswerSubmission]


class AttemptSubmitResponse(BaseModel):
    attempt_id: str
    status: str
    score: float
    maximum_score: float
    grading_status: str
