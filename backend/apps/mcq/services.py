"""MCQ orchestration with a production TTL cache (§10.5, sync + Django ORM)."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from django.utils import timezone

from apps.core.deps import Identity
from apps.integrations.gemini.prompts.mcq import daily_challenge_prompt, mcq_generation_prompt
from apps.mcq.models import McqAttempt, McqQuestion, McqSet
from apps.mcq.schemas import (
    AttemptRequest,
    AttemptResponse,
    DailyChallengeSchema,
    McqGenerationSchema,
    McqItemOut,
    McqItemSchema,
    McqSetOut,
)


class McqService:
    def __init__(self, gemini: Any, ttl_hours: int) -> None:
        self.gemini = gemini
        self.ttl_hours = ttl_hours

    def generate(self, topic: str, subtopic: str, count: int, difficulty: str) -> McqSetOut:
        t, s, d = topic.strip().lower(), subtopic.strip().lower(), difficulty.strip().lower()
        cache_key = f"gen|{t}|{s}|{count}|{d}"

        def _gen() -> list[McqItemSchema]:
            result = self.gemini.generate_json(
                mcq_generation_prompt(
                    topic=topic, subtopic=subtopic, count=count, difficulty=difficulty
                ),
                McqGenerationSchema,
            )
            return result.questions

        meta = {"topic": topic, "subtopic": subtopic, "count": count, "difficulty": difficulty}
        set_row, questions = self._get_or_generate(cache_key, meta, _gen)
        return McqSetOut(
            set_id=set_row.id, topic=set_row.topic, subtopic=set_row.subtopic,
            difficulty=set_row.difficulty, count=len(questions),
            questions=[McqItemOut.model_validate(q) for q in questions],
        )

    def daily_challenge(self, topic: str) -> McqItemOut:
        key_topic = (topic or "mixed").strip().lower()
        cache_key = f"daily|{date.today().isoformat()}|{key_topic}"

        def _gen() -> list[McqItemSchema]:
            result = self.gemini.generate_json(
                daily_challenge_prompt(key_topic), DailyChallengeSchema
            )
            explanation = result.explanation
            if result.fun_fact:
                explanation = f"{explanation}\n\nFun fact: {result.fun_fact}".strip()
            return [
                McqItemSchema(
                    question=result.question, options=result.options,
                    correct_answer=result.correct_answer, explanation=explanation,
                )
            ]

        meta = {"topic": key_topic, "subtopic": "daily", "count": 1, "difficulty": "medium"}
        _set, questions = self._get_or_generate(cache_key, meta, _gen)
        return McqItemOut.model_validate(questions[0])

    def record_attempt(self, identity: Identity, req: AttemptRequest) -> AttemptResponse:
        attempt = McqAttempt.objects.create(
            user_id=identity.user_id, guest_id=identity.guest_id, set_id=req.set_id,
            subject=req.subject, difficulty=req.difficulty, correct=req.correct, total=req.total,
        )
        percent = round((req.correct / req.total) * 100) if req.total else 0
        return AttemptResponse(id=attempt.id, correct=req.correct, total=req.total, percent=percent)

    # --- cache internals ---

    def _is_fresh(self, set_row: McqSet) -> bool:
        return timezone.now() - set_row.created_at < timedelta(hours=self.ttl_hours)

    def _get_or_generate(
        self,
        cache_key: str,
        meta: dict[str, object],
        generate_items: Callable[[], list[McqItemSchema]],
    ) -> tuple[McqSet, list[McqQuestion]]:
        existing = McqSet.objects.filter(cache_key=cache_key).first()
        if existing is not None and self._is_fresh(existing):
            return existing, list(existing.questions.all())
        if existing is not None:
            existing.delete()  # evict stale (attempts keep via SET NULL)

        items = generate_items()
        set_row = McqSet.objects.create(cache_key=cache_key, **meta)
        questions = [
            McqQuestion.objects.create(
                set=set_row, question=it.question, options=it.options,
                correct_answer=it.correct_answer, explanation=it.explanation,
            )
            for it in items
        ]
        return set_row, questions
