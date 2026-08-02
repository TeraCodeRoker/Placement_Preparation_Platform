"""Interview request/response contracts + the Gemini evaluation schema."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    difficulty: str = "medium"
    num_subjective: int = Field(5, ge=0, le=10)
    num_dsa: int = Field(2, ge=0, le=10)


class AnswerRequest(BaseModel):
    session_id: uuid.UUID
    answer: str
    idempotency_key: str | None = None


class QuestionOut(BaseModel):
    question_number: int
    total_questions: int
    question_type: str
    subject: str
    topic: str
    question: str


class EvaluationOut(BaseModel):
    score: int
    feedback: str
    correct_answer: str


class PerQuestion(BaseModel):
    question_number: int
    subject: str
    topic: str
    score: int


class SummaryOut(BaseModel):
    total_questions: int
    average_score: float
    per_question: list[PerQuestion]


class StartResponse(BaseModel):
    session_id: uuid.UUID
    message: str
    question: QuestionOut


class AnswerResponse(BaseModel):
    evaluation: EvaluationOut
    is_complete: bool
    next_question: QuestionOut | None = None
    summary: SummaryOut | None = None


class SessionStateResponse(BaseModel):
    is_complete: bool
    question: QuestionOut | None = None
    summary: SummaryOut | None = None


class InterviewHistoryItem(BaseModel):
    session_id: uuid.UUID
    status: str
    total_questions: int
    created_at: datetime
    completed_at: datetime | None = None


class CodeReviewRequest(BaseModel):
    question: str
    user_code: str
    language: str


class CodeReviewResponse(BaseModel):
    review: str
    language: str


class EvaluationSchema(BaseModel):
    """Gemini structured-output schema for answer evaluation (§10.2)."""

    score: int
    feedback: str = ""
    correct_answer: str = ""
