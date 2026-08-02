"""OA prompt templates."""
from __future__ import annotations

from apps.integrations.gemini.prompts._common import INJECTION_GUARD, wrap_untrusted


def problem_generation_prompt(
    *, step: str, topic: str, languages: list[str], num_hidden: int
) -> str:
    langs = ", ".join(languages)
    return (
        "You are setting a coding problem for an online assessment, based on "
        "Striver's A2Z DSA sheet.\n\n"
        f"Sheet section: {step}\nProblem theme: {topic}\n"
        f"Languages to provide starter code for: {langs}\n\n"
        "RULES:\n"
        "- Write a self-contained statement solvable via stdin -> stdout.\n"
        "- Programs read input from standard input and print to standard output.\n"
        "- Provide starter code per language that reads stdin and prints stdout.\n"
        "- Provide 2-3 VISIBLE example test cases and exactly "
        f"{num_hidden} HIDDEN test cases, each with exact stdin and expected "
        "stdout.\n"
        "Return JSON with: title, statement, starter_code (map language -> code), "
        "visible_tests[] (stdin, expected_output), hidden_tests[] (stdin, "
        "expected_output), time_complexity_hint."
    )


def oa_review_prompt(*, problem: str, language: str, code: str, passed: int, total: int) -> str:
    return (
        "You are a senior engineer reviewing an online-assessment submission for a "
        "human reader.\n"
        f"Problem: {problem}\nLanguage: {language}\n"
        f"Objective result: {passed}/{total} test cases passed.\n\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('submission_code', code)}\n\n"
        "Return JSON with: correctness_rationale, time_complexity, space_complexity, "
        "code_quality (short), suggestions[], review_score (integer 0-10). Base the "
        "review on the code and the objective result; do not re-run the code."
    )
