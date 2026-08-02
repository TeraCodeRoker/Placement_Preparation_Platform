"""Resume request/response contracts + Gemini output schemas (permissive)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    resume_text: str
    target_role: str
    target_companies: list[str] = Field(default_factory=list)


class AtsRequest(BaseModel):
    resume_text: str
    job_description: str


class BulletRequest(BaseModel):
    bullet: str
    context: str = ""


class PlacementRequest(BaseModel):
    resume_text: str
    dream_company: str = "product-based company"


class ResumeHistoryItem(BaseModel):
    id: uuid.UUID
    target_role: str
    kind: str
    verdict: str
    created_at: datetime


class ResumeAnalysisSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    overall_score: int = 0
    section_scores: dict[str, int] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    critical_issues: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    quick_wins: list[str] = Field(default_factory=list)
    verdict: str = ""
    shortlist_probability: str = ""
    experience_level_detected: str = ""


class AtsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    ats_score: int = 0
    keyword_match: dict[str, Any] = Field(default_factory=dict)
    section_feedback: dict[str, str] = Field(default_factory=dict)
    ats_friendly_issues: list[str] = Field(default_factory=list)
    recommended_additions: list[str] = Field(default_factory=list)
    rewritten_summary: str = ""
    will_pass_ats: bool = False


class BulletSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    improved: str = ""
    alternatives: list[str] = Field(default_factory=list)
    why_better: str = ""


class PlacementSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    placement_ready_score: int = 0
    checklist: dict[str, bool] = Field(default_factory=dict)
    top_3_improvements: list[str] = Field(default_factory=list)
    stands_out_because: str = ""
    red_flags: list[str] = Field(default_factory=list)
    estimated_interview_calls: str = ""


class PdfJsonSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    links: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class PdfToJsonResponse(BaseModel):
    filename: str
    resume_text: str
    structured: PdfJsonSchema


class AnalyzePdfResponse(BaseModel):
    resume_text: str
    target_role: str
    analysis: ResumeAnalysisSchema
