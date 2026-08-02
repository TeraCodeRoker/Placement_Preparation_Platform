"""OA orchestration — real execution + AI review + degraded mode (sync + ORM)."""
from __future__ import annotations

import time
import uuid
from typing import Any

from apps.core.deps import Identity
from apps.core.exceptions import NotFoundError
from apps.integrations.execution.base import enforce_source_size
from apps.integrations.execution.errors import ExecutionUnavailableError
from apps.integrations.gemini.errors import GeminiError
from apps.integrations.gemini.prompts.oa import oa_review_prompt, problem_generation_prompt
from apps.oa.models import OAProblem, OASubmission
from apps.oa.schemas import (
    OAProblemOut,
    OAProblemSchema,
    OAReviewSchema,
    OARunResponse,
    OASubmissionOut,
    OASubmitResponse,
    TestCaseResultOut,
    VisibleTestOut,
)

_STDOUT_CAP = 4000


def _normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.rstrip("\n").splitlines())


def _matches(actual: str, expected: str) -> bool:
    if _normalize(actual) == _normalize(expected):
        return True
    try:
        return abs(float(actual.strip()) - float(expected.strip())) <= 1e-6
    except ValueError:
        return False


class OAService:
    def __init__(
        self,
        gemini: Any,
        executor: Any,
        max_source_bytes: int,
        per_case_timeout_s: float,
        wall_clock_s: float,
    ) -> None:
        self.gemini = gemini
        self.executor = executor
        self.max_source_bytes = max_source_bytes
        self.per_case_timeout_s = per_case_timeout_s
        self.wall_clock_s = wall_clock_s

    def create_problem(
        self, step: str, topic: str, languages: list[str], num_hidden: int
    ) -> OAProblemOut:
        result = self.gemini.generate_json(
            problem_generation_prompt(
                step=step, topic=topic, languages=languages, num_hidden=num_hidden
            ),
            OAProblemSchema,
        )
        problem = OAProblem.objects.create(
            step=step, topic=topic, statement=result.statement, starter_code=result.starter_code,
            visible_tests=[t.model_dump() for t in result.visible_tests],
            hidden_tests=[t.model_dump() for t in result.hidden_tests],
        )
        return OAProblemOut(
            problem_id=problem.id, title=result.title, statement=result.statement,
            starter_code=result.starter_code,
            visible_tests=[VisibleTestOut(**t.model_dump()) for t in result.visible_tests],
            time_complexity_hint=result.time_complexity_hint,
        )

    def run(self, problem_id: uuid.UUID, language: str, source_code: str) -> OARunResponse:
        enforce_source_size(source_code, self.max_source_bytes)
        problem = self._get_problem(problem_id)
        cases = [(c, True) for c in problem.visible_tests]
        results = self._execute_cases(language, source_code, cases)
        return OARunResponse(
            results=results, passed=sum(1 for r in results if r.passed), total=len(results)
        )

    def submit(
        self, identity: Identity, problem_id: uuid.UUID, language: str, source_code: str
    ) -> OASubmitResponse:
        enforce_source_size(source_code, self.max_source_bytes)
        problem = self._get_problem(problem_id)
        cases = [(c, True) for c in problem.visible_tests] + [
            (c, False) for c in problem.hidden_tests
        ]
        total = len(cases)

        degraded = False
        results: list[TestCaseResultOut] = []
        try:
            results = self._execute_cases(language, source_code, cases)
        except ExecutionUnavailableError:
            degraded = True

        pass_count = sum(1 for r in results if r.passed)
        final_score = round((pass_count / total) * 100) if (total and not degraded) else 0
        review = self._safe_review(
            problem, language, source_code, pass_count, 0 if degraded else total
        )
        mode = "ai_review_only" if degraded else "graded"

        submission = OASubmission.objects.create(
            problem=problem, user_id=identity.user_id, guest_id=identity.guest_id,
            language=language, source_code=source_code,
            test_results=[r.model_dump() for r in results],
            pass_count=pass_count, total_count=total,
            ai_review=review.model_dump() if review else None,
            final_score=final_score, mode=mode,
        )
        return OASubmitResponse(
            submission_id=submission.id, test_results=results, pass_count=pass_count,
            total_count=total, ai_review=review, final_score=final_score, mode=mode,
        )

    def get_submission_out(self, submission_id: uuid.UUID, identity: Identity) -> OASubmissionOut:
        submission = OASubmission.objects.filter(id=submission_id).first()
        if submission is None or (
            submission.user_id is not None and submission.user_id != identity.user_id
        ):
            raise NotFoundError("Submission not found.")
        return OASubmissionOut(
            id=submission.id, problem_id=submission.problem_id, language=submission.language,
            pass_count=submission.pass_count, total_count=submission.total_count,
            final_score=submission.final_score, mode=submission.mode,
            ai_review=OAReviewSchema.model_validate(submission.ai_review)
            if submission.ai_review else None,
            created_at=submission.created_at,
        )

    # --- helpers ---

    def _execute_cases(
        self, language: str, source_code: str, cases: list[tuple[dict[str, Any], bool]]
    ) -> list[TestCaseResultOut]:
        results: list[TestCaseResultOut] = []
        started = time.monotonic()
        for index, (case, visible) in enumerate(cases):
            if time.monotonic() - started > self.wall_clock_s:
                results.append(
                    TestCaseResultOut(index=index, visible=visible, passed=False, timed_out=True)
                )
                continue
            outcome = self.executor.execute(
                language, source_code, case.get("stdin", ""), self.per_case_timeout_s
            )
            passed = (not outcome.timed_out) and _matches(
                outcome.stdout, case.get("expected_output", "")
            )
            results.append(
                TestCaseResultOut(
                    index=index, visible=visible, passed=passed, timed_out=outcome.timed_out,
                    time_ms=outcome.time_ms,
                    stdout=outcome.stdout[:_STDOUT_CAP] if visible else None,
                    stderr=outcome.stderr[:_STDOUT_CAP] if visible else None,
                    expected_output=case.get("expected_output") if visible else None,
                )
            )
        return results

    def _safe_review(
        self, problem: OAProblem, language: str, code: str, passed: int, total: int
    ) -> OAReviewSchema | None:
        try:
            return self.gemini.generate_json(
                oa_review_prompt(
                    problem=problem.statement, language=language, code=code,
                    passed=passed, total=total,
                ),
                OAReviewSchema,
            )
        except GeminiError:
            return None

    def _get_problem(self, problem_id: uuid.UUID) -> OAProblem:
        problem = OAProblem.objects.filter(id=problem_id).first()
        if problem is None:
            raise NotFoundError("Problem not found.")
        return problem
