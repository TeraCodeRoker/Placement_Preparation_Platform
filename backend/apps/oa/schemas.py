"""OA request/response contracts + Gemini output schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class OAProblemRequest(BaseModel):
    step: str
    topic: str
    languages: list[str] = Field(default_factory=lambda: ["python"])
    num_hidden: int = Field(5, ge=1, le=10)


class OARunRequest(BaseModel):
    problem_id: uuid.UUID
    language: str
    source_code: str


class OASubmitRequest(OARunRequest):
    pass


class OATestCase(BaseModel):
    stdin: str = ""
    expected_output: str = ""


class OAProblemSchema(BaseModel):
    title: str = ""
    statement: str = ""
    starter_code: dict[str, str] = Field(default_factory=dict)
    visible_tests: list[OATestCase] = Field(default_factory=list)
    hidden_tests: list[OATestCase] = Field(default_factory=list)
    time_complexity_hint: str = ""


class OAReviewSchema(BaseModel):
    correctness_rationale: str = ""
    time_complexity: str = ""
    space_complexity: str = ""
    code_quality: str = ""
    suggestions: list[str] = Field(default_factory=list)
    review_score: int = 0


class VisibleTestOut(BaseModel):
    stdin: str
    expected_output: str


class OAProblemOut(BaseModel):
    problem_id: uuid.UUID
    title: str
    statement: str
    starter_code: dict[str, str]
    visible_tests: list[VisibleTestOut]
    time_complexity_hint: str


class TestCaseResultOut(BaseModel):
    index: int
    visible: bool
    passed: bool
    timed_out: bool = False
    time_ms: float | None = None
    stdout: str | None = None
    stderr: str | None = None
    expected_output: str | None = None


class OARunResponse(BaseModel):
    results: list[TestCaseResultOut]
    passed: int
    total: int


class OASubmitResponse(BaseModel):
    submission_id: uuid.UUID
    test_results: list[TestCaseResultOut]
    pass_count: int
    total_count: int
    ai_review: OAReviewSchema | None
    final_score: int
    mode: str


class OASubmissionOut(BaseModel):
    id: uuid.UUID
    problem_id: uuid.UUID
    language: str
    pass_count: int
    total_count: int
    final_score: int
    mode: str
    ai_review: OAReviewSchema | None
    created_at: datetime
