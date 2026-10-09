"""Parse and render the user-editable Markdown profile (``job_profile.md``).

Format: ``## Section`` headings containing ``- key: value`` lines (settings /
answers) or plain ``- item`` lines (lists).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

SETTINGS = "Search Settings"
ROLES = "Target Roles"
TITLES = "Example Job Titles"
COMPANIES = "Company Types"
CANDIDATE = "Candidate Info"
ANSWERS = "Application Answers"


@dataclass
class Profile:
    roles: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    salary_min: int | None = None
    salary_max: int | None = None
    num_roles: int = 5
    candidate: dict[str, str] = field(default_factory=dict)
    answers: dict[str, str] = field(default_factory=dict)


def _sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            current = m.group(1)
            out[current] = []
        elif current is not None and line.strip().startswith("-"):
            out[current].append(line.strip().lstrip("-").strip())
    return out


def _kv(items: list[str]) -> dict[str, str]:
    result = {}
    for item in items:
        if ":" in item:
            k, v = item.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def _int(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


def parse_profile(text: str) -> Profile:
    sec = _sections(text)
    settings = _kv(sec.get(SETTINGS, []))
    return Profile(
        roles=sec.get(ROLES, []),
        titles=sec.get(TITLES, []),
        companies=sec.get(COMPANIES, []),
        salary_min=_int(settings.get("salary_min")),
        salary_max=_int(settings.get("salary_max")),
        num_roles=_int(settings.get("num_roles")) or 5,
        candidate=_kv(sec.get(CANDIDATE, [])),
        answers=_kv(sec.get(ANSWERS, [])),
    )


def load_profile(path: str) -> Profile:
    with open(path, encoding="utf-8") as fh:
        return parse_profile(fh.read())


DEFAULT_ANSWERS = {
    "work_authorization": "Yes, authorized to work",
    "requires_sponsorship": "No",
    "veteran_status": "I am not a protected veteran",
    "disability_status": "I do not wish to answer",
    "gender": "I do not wish to answer",
    "race_ethnicity": "I do not wish to answer",
    "willing_to_relocate": "No",
    "desired_salary": "",
    "start_date": "2 weeks notice",
    "how_did_you_hear": "Online job board",
}

DEFAULT_CANDIDATE = {
    "full_name": "", "email": "", "phone": "", "location": "",
    "linkedin": "", "website": "", "resume_path": "",
}


def render_profile(p: Profile) -> str:
    """Render a Profile to Markdown."""
    lines = ["# Job Bot Profile", "",
             "Edit this file, then run `job-bot run`.", ""]

    def block(title, items):
        lines.append(f"## {title}")
        lines.extend(f"- {i}" for i in items)
        lines.append("")

    block(SETTINGS, [
        f"num_roles: {p.num_roles}",
        f"salary_min: {p.salary_min or ''}",
        f"salary_max: {p.salary_max or ''}",
    ])
    block(ROLES, p.roles)
    block(TITLES, p.titles)
    block(COMPANIES, p.companies)
    block(CANDIDATE, [f"{k}: {v}" for k, v in {**DEFAULT_CANDIDATE, **p.candidate}.items()])
    block(ANSWERS, [f"{k}: {v}" for k, v in {**DEFAULT_ANSWERS, **p.answers}.items()])
    return "\n".join(lines)
