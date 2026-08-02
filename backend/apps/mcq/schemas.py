"""MCQ request/response contracts + Gemini output schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class McqGenerateRequest(BaseModel):
    topic: str
    subtopic: str = ""
    count: int = Field(5, ge=1, le=20)
    difficulty: str = "medium"


class DailyChallengeRequest(BaseModel):
    topic: str = "mixed"


class AttemptRequest(BaseModel):
    set_id: uuid.UUID | None = None
    subject: str = ""
    difficulty: str = ""
    correct: int = Field(..., ge=0)
    total: int = Field(..., ge=1)


class McqItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    options: dict[str, str]
    correct_answer: str
    explanation: str


class McqSetOut(BaseModel):
    set_id: uuid.UUID
    topic: str
    subtopic: str
    difficulty: str
    count: int
    questions: list[McqItemOut]


class AttemptResponse(BaseModel):
    id: uuid.UUID
    correct: int
    total: int
    percent: int


class McqHistoryItem(BaseModel):
    id: uuid.UUID
    subject: str
    difficulty: str
    correct: int
    total: int
    percent: int
    created_at: datetime


class McqItemSchema(BaseModel):
    question: str
    options: dict[str, str]
    correct_answer: str
    explanation: str = ""


class McqGenerationSchema(BaseModel):
    questions: list[McqItemSchema]


class DailyChallengeSchema(BaseModel):
    question: str
    options: dict[str, str]
    correct_answer: str
    explanation: str = ""
    topic: str = ""
    difficulty: str = "medium"
    fun_fact: str = ""
