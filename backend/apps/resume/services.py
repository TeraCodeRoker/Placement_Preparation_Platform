"""Resume orchestration on the shared Gemini layer (sync + Django ORM)."""
from __future__ import annotations

import uuid
from typing import Any

from apps.core.deps import Identity
from apps.integrations.gemini.prompts.resume import (
    analyze_prompt,
    ats_prompt,
    improve_bullet_prompt,
    pdf_to_json_prompt,
    placement_check_prompt,
)
from apps.resume.models import ResumeAnalysis
from apps.resume.schemas import (
    AtsSchema,
    BulletSchema,
    PdfJsonSchema,
    PlacementSchema,
    ResumeAnalysisSchema,
)
from apps.resume.uploads import extract_pdf_text, truncate_resume_text


class ResumeService:
    def __init__(self, gemini: Any) -> None:
        self.gemini = gemini

    def analyze(
        self, identity: Identity, resume_text: str, target_role: str, companies: list[str]
    ) -> ResumeAnalysisSchema:
        result = self.gemini.generate_json(
            analyze_prompt(
                resume_text=truncate_resume_text(resume_text),
                target_role=target_role, target_companies=companies,
            ),
            ResumeAnalysisSchema,
        )
        self._persist(identity, target_role, "analyze", result.model_dump(), result.verdict)
        return result

    def ats_score(self, identity: Identity, resume_text: str, job_description: str) -> AtsSchema:
        result = self.gemini.generate_json(
            ats_prompt(
                resume_text=truncate_resume_text(resume_text),
                job_description=truncate_resume_text(job_description),
            ),
            AtsSchema,
        )
        verdict = f"ATS score {result.ats_score}; passes={result.will_pass_ats}"
        self._persist(identity, "", "ats", result.model_dump(), verdict)
        return result

    def improve_bullet(self, bullet: str, context: str) -> BulletSchema:
        return self.gemini.generate_json(
            improve_bullet_prompt(bullet=bullet, context=context), BulletSchema
        )

    def placement_check(
        self, identity: Identity, resume_text: str, dream_company: str
    ) -> PlacementSchema:
        result = self.gemini.generate_json(
            placement_check_prompt(
                resume_text=truncate_resume_text(resume_text), dream_company=dream_company
            ),
            PlacementSchema,
        )
        self._persist(identity, "", "placement", result.model_dump(), result.stands_out_because)
        return result

    def pdf_to_json(self, filename: str, data: bytes) -> tuple[str, PdfJsonSchema]:
        resume_text = extract_pdf_text(filename, data)
        structured = self.gemini.generate_json(pdf_to_json_prompt(resume_text), PdfJsonSchema)
        return resume_text, structured

    def analyze_pdf(
        self, identity: Identity, filename: str, data: bytes, target_role: str, companies: list[str]
    ) -> tuple[str, ResumeAnalysisSchema]:
        resume_text = extract_pdf_text(filename, data)
        return resume_text, self.analyze(identity, resume_text, target_role, companies)

    def history(self, user_id: uuid.UUID, limit: int, offset: int) -> list[ResumeAnalysis]:
        return list(
            ResumeAnalysis.objects.filter(user_id=user_id).order_by("-created_at")[
                offset : offset + limit
            ]
        )

    def _persist(
        self, identity: Identity, target_role: str, kind: str, scores: dict, verdict: str
    ) -> None:
        ResumeAnalysis.objects.create(
            user_id=identity.user_id, guest_id=identity.guest_id, target_role=target_role,
            kind=kind, scores=scores, verdict=verdict,
        )
