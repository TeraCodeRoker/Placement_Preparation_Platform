"""Interview orchestration (sync, Django ORM).

Ports the legacy flow: question_bank is the source of truth, Gemini phrases and
evaluates. Idempotent /answer; the caller (view) owns the transaction.
"""
from __future__ import annotations

import random
import uuid
from typing import Any

from django.utils import timezone

from apps.core.deps import Identity
from apps.core.exceptions import NotFoundError, ValidationAppError
from apps.integrations.gemini.prompts.interview import (
    code_review_prompt,
    dsa_question_prompt,
    evaluate_answer_prompt,
    subjective_question_prompt,
)
from apps.interview.models import InterviewResult, InterviewSession
from apps.interview.question_bank import (
    ALL_DSA_STEPS,
    ALL_SUBJECTS,
    STRIVER_A2Z,
    SYLLABUS_SUBJECTS,
)
from apps.interview.schemas import (
    AnswerResponse,
    EvaluationOut,
    EvaluationSchema,
    PerQuestion,
    QuestionOut,
    SessionStateResponse,
    StartResponse,
    SummaryOut,
)

PlanItem = dict[str, str]


def build_question_plan(num_subjective: int, num_dsa: int, difficulty: str) -> list[PlanItem]:
    plan: list[PlanItem] = []
    subjects = ALL_SUBJECTS[:]
    random.shuffle(subjects)
    for i in range(max(0, num_subjective)):
        subject = subjects[i % len(subjects)]
        unit = random.choice(list(SYLLABUS_SUBJECTS[subject]["units"].keys()))
        topic = random.choice(SYLLABUS_SUBJECTS[subject]["units"][unit])
        plan.append(
            {"type": "subjective", "subject": subject, "unit": unit,
             "topic": topic, "difficulty": difficulty}
        )
    steps = ALL_DSA_STEPS[:]
    random.shuffle(steps)
    for i in range(max(0, num_dsa)):
        step = steps[i % len(steps)]
        problem = random.choice(STRIVER_A2Z[step])
        plan.append(
            {"type": "dsa", "subject": "Data Structures & Algorithms", "unit": step,
             "topic": problem, "difficulty": difficulty}
        )
    if not plan:
        raise ValidationAppError("An interview must have at least one question.")
    first = next((q for q in plan if q["type"] == "subjective"), None)
    if first:
        plan.remove(first)
        random.shuffle(plan)
        plan.insert(0, first)
    else:
        random.shuffle(plan)
    return plan


class InterviewService:
    def __init__(self, gemini: Any) -> None:
        self.gemini = gemini

    def start(
        self, identity: Identity, difficulty: str, num_subjective: int, num_dsa: int
    ) -> StartResponse:
        plan = build_question_plan(num_subjective, num_dsa, difficulty)
        plan[0]["question"] = self._generate_question(plan[0])
        session = InterviewSession.objects.create(
            user_id=identity.user_id, guest_id=identity.guest_id, plan=plan,
            status="active", current_index=0,
        )
        return StartResponse(
            session_id=session.id,
            message=f"Interview started — {len(plan)} questions.",
            question=self._question_out(session),
        )

    def answer(
        self, session: InterviewSession, answer_text: str, idempotency_key: str | None
    ) -> AnswerResponse:
        if session.status == "complete":
            raise ValidationAppError("This interview is already complete.")
        if idempotency_key:
            existing = InterviewResult.objects.filter(
                session=session, answer_idempotency_key=idempotency_key
            ).first()
            if existing is not None:
                return self._replay(session, existing)

        idx = session.current_index
        item = session.plan[idx]
        evaluation = self._evaluate(item, answer_text)
        InterviewResult.objects.create(
            session=session, question_number=idx + 1, question_type=item["type"],
            subject=item["subject"], topic=item["topic"], question=item["question"],
            answer=answer_text, score=evaluation.score, feedback=evaluation.feedback,
            correct_answer=evaluation.correct_answer, answer_idempotency_key=idempotency_key,
        )

        next_idx = idx + 1
        if next_idx < len(session.plan):
            session.plan[next_idx]["question"] = self._generate_question(session.plan[next_idx])
            session.current_index = next_idx
            session.save(update_fields=["plan", "current_index"])
            return AnswerResponse(
                evaluation=evaluation, is_complete=False, next_question=self._question_out(session)
            )
        session.status = "complete"
        session.completed_at = timezone.now()
        session.save(update_fields=["status", "completed_at"])
        return AnswerResponse(
            evaluation=evaluation, is_complete=True, summary=self._summary(session)
        )

    def get_state(self, session: InterviewSession) -> SessionStateResponse:
        if session.status == "complete":
            return SessionStateResponse(is_complete=True, summary=self._summary(session))
        return SessionStateResponse(is_complete=False, question=self._question_out(session))

    def code_review(self, question: str, language: str, code: str) -> str:
        return self.gemini.generate_text(
            code_review_prompt(question=question, language=language, code=code)
        )

    # --- helpers ---

    def _generate_question(self, item: PlanItem) -> str:
        if item["type"] == "subjective":
            prompt = subjective_question_prompt(
                item["subject"], item["unit"], item["topic"], item["difficulty"]
            )
        else:
            prompt = dsa_question_prompt(item["unit"], item["topic"], item["difficulty"])
        return self.gemini.generate_text(prompt)

    def _evaluate(self, item: PlanItem, answer_text: str) -> EvaluationOut:
        result = self.gemini.generate_json(
            evaluate_answer_prompt(
                subject=item["subject"], topic=item["topic"], question=item["question"],
                answer=answer_text, is_dsa=item["type"] == "dsa",
            ),
            EvaluationSchema,
        )
        return EvaluationOut(
            score=max(0, min(10, result.score)),
            feedback=result.feedback,
            correct_answer=result.correct_answer,
        )

    def _question_out(self, session: InterviewSession) -> QuestionOut:
        item = session.plan[session.current_index]
        return QuestionOut(
            question_number=session.current_index + 1,
            total_questions=len(session.plan),
            question_type=item["type"], subject=item["subject"],
            topic=item["topic"], question=item["question"],
        )

    def _summary(self, session: InterviewSession) -> SummaryOut:
        results = list(session.results.order_by("question_number"))
        scores = [r.score for r in results]
        return SummaryOut(
            total_questions=len(results),
            average_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            per_question=[
                PerQuestion(
                    question_number=r.question_number, subject=r.subject,
                    topic=r.topic, score=r.score,
                )
                for r in results
            ],
        )

    def _replay(self, session: InterviewSession, existing: InterviewResult) -> AnswerResponse:
        evaluation = EvaluationOut(
            score=existing.score, feedback=existing.feedback,
            correct_answer=existing.correct_answer,
        )
        if session.status == "complete":
            return AnswerResponse(
                evaluation=evaluation, is_complete=True, summary=self._summary(session)
            )
        return AnswerResponse(
            evaluation=evaluation, is_complete=False, next_question=self._question_out(session)
        )

    def get_session_or_404(self, session_id: uuid.UUID) -> InterviewSession:
        session = InterviewSession.objects.filter(id=session_id).first()
        if session is None:
            raise NotFoundError("Interview session not found.")
        return session
