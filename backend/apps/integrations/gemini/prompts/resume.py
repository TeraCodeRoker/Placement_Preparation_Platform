"""Resume prompt templates. Resume/JD/bullet text is untrusted -> fenced."""
from __future__ import annotations

from apps.integrations.gemini.prompts._common import INJECTION_GUARD, wrap_untrusted


def analyze_prompt(*, resume_text: str, target_role: str, target_companies: list[str]) -> str:
    companies = f"Target companies: {', '.join(target_companies)}\n" if target_companies else ""
    return (
        "You are an expert technical recruiter who has reviewed 10,000+ resumes.\n"
        f"Analyze the resume for a {target_role} position.\n{companies}\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('resume', resume_text)}\n\n"
        "Return JSON with: overall_score (0-100), section_scores "
        "(contact_info, skills, experience, projects, education), strengths[], "
        "critical_issues[], missing_keywords[], quick_wins[], verdict, "
        "shortlist_probability (Low/Medium/High), experience_level_detected."
    )


def ats_prompt(*, resume_text: str, job_description: str) -> str:
    return (
        "You are an ATS scanner. Score the resume against the job description.\n\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('resume', resume_text)}\n"
        f"{wrap_untrusted('job_description', job_description)}\n\n"
        "Return JSON with: ats_score (0-100), keyword_match "
        "(matched_keywords[], missing_keywords[], match_percentage), "
        "section_feedback (skills_match, experience_match, education_match), "
        "ats_friendly_issues[], recommended_additions[], rewritten_summary, "
        "will_pass_ats (boolean)."
    )


def improve_bullet_prompt(*, bullet: str, context: str) -> str:
    context_line = f"Context: {context}\n" if context else ""
    return (
        "You are a resume coach. Rewrite the bullet point to be stronger.\n"
        f"{context_line}\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('bullet', bullet)}\n\n"
        "RULES: start with a strong action verb; add metrics (estimate if absent); "
        "show impact; keep under 20 words; ATS-friendly.\n"
        "Return JSON with: improved, alternatives[] (two), why_better."
    )


def placement_check_prompt(*, resume_text: str, dream_company: str) -> str:
    return (
        f"A student is preparing for campus placements at {dream_company}. Review "
        "their resume for Indian tech campus placements.\n\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('resume', resume_text)}\n\n"
        "Return JSON with: placement_ready_score (0-100), checklist "
        "(has_github_link, has_linkedin, has_leetcode_or_cf, has_projects, "
        "has_internship, has_relevant_skills, one_page, cgpa_mentioned), "
        "top_3_improvements[], stands_out_because, red_flags[], "
        "estimated_interview_calls."
    )


def pdf_to_json_prompt(resume_text: str) -> str:
    return (
        "Convert the resume text into structured JSON. Extract only what is "
        "present; use null for missing fields and [] for empty lists. Do not "
        "invent information.\n\n"
        f"{INJECTION_GUARD}\n"
        f"{wrap_untrusted('resume', resume_text)}\n\n"
        "Return JSON with: name, email, phone, links (github, linkedin, portfolio, "
        "other[]), summary, skills[], experience[] (company, role, duration, "
        "points[]), projects[] (name, tech[], points[]), education[] (institution, "
        "degree, year, score), certifications[], achievements[]."
    )
