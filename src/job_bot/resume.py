"""LLM review of a PDF resume -> Markdown profile."""
from __future__ import annotations

from .llm import extract_json
from .profile import Profile, render_profile

PROMPT = """Review the attached resume. Respond with ONLY a JSON object with keys:
"roles": list of 3-6 role categories this person is a good fit for,
"titles": list of 6-12 example job titles to search for,
"companies": list of 3-6 company types (size/industry/stage) to target,
"salary_min": integer USD annual salary lower bound,
"salary_max": integer USD annual salary upper bound,
"candidate": object with full_name, email, phone, location, linkedin, website (empty string if absent)."""


def build_profile(data: dict, resume_path: str = "") -> Profile:
    cand = {k: str(v or "") for k, v in (data.get("candidate") or {}).items()}
    cand["resume_path"] = resume_path
    return Profile(
        roles=list(data.get("roles", [])),
        titles=list(data.get("titles", [])),
        companies=list(data.get("companies", [])),
        salary_min=data.get("salary_min"),
        salary_max=data.get("salary_max"),
        candidate=cand,
    )


def review_resume(llm, pdf_path: str) -> str:
    with open(pdf_path, "rb") as fh:
        pdf = fh.read()
    data = extract_json(llm.generate(PROMPT, pdf_bytes=pdf))
    return render_profile(build_profile(data, resume_path=pdf_path))
