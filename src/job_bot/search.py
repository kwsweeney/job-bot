"""Web search for jobs matching the profile."""
from __future__ import annotations

from .llm import extract_json
from .profile import Profile


def build_prompt(p: Profile, count: int, exclude: list[str]) -> str:
    sal = f"{p.salary_min or '?'} - {p.salary_max or '?'} USD"
    return (
        f"Use web search to find {count} currently open job postings.\n"
        f"Target roles: {', '.join(p.roles)}\nExample titles: {', '.join(p.titles)}\n"
        f"Company types: {', '.join(p.companies)}\nSalary range: {sal}\n"
        f"Location: {p.candidate.get('location', 'any')}\n"
        f"Do not include these URLs: {exclude}\n"
        "Each result must be the DIRECT URL of the job posting / application page. "
        'Respond with ONLY a JSON list of objects: {"title","company","url"}.'
    )


def find_jobs(llm, p: Profile, max_rounds: int = 3) -> list[dict]:
    """Search until ``p.num_roles`` jobs with unique URLs are found."""
    jobs: list[dict] = []
    seen: set[str] = set()
    for _ in range(max_rounds):
        need = p.num_roles - len(jobs)
        if need <= 0:
            break
        try:
            results = extract_json(llm.search(build_prompt(p, need, sorted(seen))))
        except ValueError:
            continue
        for r in results if isinstance(results, list) else []:
            url = str(r.get("url", "")).strip() if isinstance(r, dict) else ""
            if url.startswith("http") and url not in seen:
                seen.add(url)
                jobs.append({"title": r.get("title", ""), "company": r.get("company", ""), "url": url})
                if len(jobs) >= p.num_roles:
                    break
    return jobs
