"""Interview prompt templates (pure functions of typed inputs -> prompt str)."""
from __future__ import annotations

from apps.integrations.gemini.prompts._common import INJECTION_GUARD, wrap_untrusted


def subjective_question_prompt(subject: str, unit: str, topic: str, difficulty: str) -> str:
    return (
        "You are a technical interviewer at a top tech company conducting a "
        "placement interview.\n\n"
        "TASK: Ask exactly ONE subjective, conceptual interview question.\n"
        f"Subject: {subject}\nSyllabus unit: {unit}\nTopic: {topic}\n"
        f"Difficulty: {difficulty}\n\n"
        "RULES:\n"
        "- Answerable by explaining in words (no code required).\n"
        "- Stay strictly on the given topic.\n"
        "- Phrase it as real interviewers do (explain / compare / why / scenario).\n"
        "- Output ONLY the question text — no preamble, numbering, or answer."
    )


def dsa_question_prompt(unit: str, topic: str, difficulty: str) -> str:
    return (
        "You are a technical interviewer running a DSA round using Striver's A2Z "
        "sheet.\n\n"
        "TASK: Present ONE coding problem to the candidate.\n"
        f"Sheet section: {unit}\nProblem: {topic}\nDifficulty: {difficulty}\n\n"
        "RULES:\n"
        "- Give a clear, self-contained statement in 2-5 sentences.\n"
        "- Include ONE small example with input and expected output.\n"
        "- End by asking for the approach and its time/space complexity.\n"
        "- Output ONLY the statement + example + final ask. No solution or hints."
    )


def evaluate_answer_prompt(
    *, subject: str, topic: str, question: str, answer: str, is_dsa: bool
) -> str:
    focus = (
        "Judge the candidate's APPROACH: correctness of the idea, data "
        "structure/algorithm choice, and stated time & space complexity. For the "
        "correct answer, give the optimal approach in 2-4 sentences with its "
        "complexity."
        if is_dsa
        else "Judge conceptual correctness, completeness, and clarity. For the "
        "correct answer, give the ideal answer briefly."
    )
    return (
        "You are a strict but helpful technical interviewer evaluating one answer.\n"
        f"Subject: {subject}\nTopic: {topic}\nQuestion asked: {question}\n\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('candidate_answer', answer)}\n\n"
        f"{focus}\n"
        "Return JSON with: score (integer 0-10), feedback (2-3 sentences on what "
        "was good and what was wrong/missing), correct_answer (the ideal answer, "
        "brief)."
    )


def code_review_prompt(*, question: str, language: str, code: str) -> str:
    return (
        "You are a senior software engineer performing a code review for a human "
        "reader.\n"
        f"Problem: {question}\nLanguage: {language}\n\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('candidate_code', code)}\n\n"
        "Write a concise prose review covering: correctness (yes/no/partial), time "
        "and space complexity, specific issues, concrete suggestions, and an "
        "overall score out of 10."
    )
