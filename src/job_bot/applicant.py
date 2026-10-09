"""Fill out and submit multi-page job applications in a browser (Playwright)."""
from __future__ import annotations

import json

from .profile import Profile

# JS run in the page: tag each visible form control with data-jb-id, return descriptors.
COLLECT_JS = """() => {
  const out = []; let n = 0;
  const label = el => {
    if (el.labels && el.labels.length) return [...el.labels].map(l => l.innerText).join(' ');
    const fs = el.closest('fieldset'); const lg = fs && fs.querySelector('legend');
    return (el.getAttribute('aria-label') || (lg && lg.innerText) || el.placeholder || el.name || '').trim();
  };
  document.querySelectorAll('input, select, textarea, button').forEach(el => {
    const r = el.getBoundingClientRect();
    if (el.type === 'hidden' || (!r.width && !r.height)) return;
    const id = 'jb' + (n++); el.setAttribute('data-jb-id', id);
    const tag = el.tagName.toLowerCase();
    const d = {id, tag, type: el.type || '', label: label(el)};
    if (tag === 'button' || el.type === 'submit') d.text = (el.innerText || el.value || '').trim();
    if (tag === 'select') d.options = [...el.options].map(o => o.text.trim());
    if (el.type === 'radio' || el.type === 'checkbox') d.value = el.value;
    out.push(d);
  });
  return out;
}"""

PROMPT = """You are filling out a job application form for a candidate. Use ONLY the data below.
Candidate info: {candidate}
Configured answers (for questions like veteran status, disability, gender, sponsorship, etc.): {answers}
Job: {job}

Form controls on the current page:
{fields}

Respond with ONLY JSON: {{"actions": [{{"id": "jbN", "action": "fill|select|check|upload|click", "value": "..."}}],
"next": "jbN or null", "done": false}}
Rules: for 'select' value must be one of the options; map questions to the closest configured answer;
use 'upload' (no value) for resume file inputs; for 'check' radio/checkbox controls only include the one to choose.
Put the id of the button that advances to the next page (Next/Continue) in "next", or the final
Submit/Apply button id in "submit". Set "done": true only if the page shows the application was submitted.
If a required value is unknown, leave that field out and add "missing": ["description"]."""


def _fields_for_llm(fields: list[dict]) -> str:
    return json.dumps(fields, indent=1)


def apply_to_job(page, llm, profile: Profile, job: dict, max_pages: int = 15, dry_run: bool = False) -> bool:
    """Drive ``page`` through a (possibly multi-page) application. Returns True if submitted."""
    page.goto(job["url"])
    resume = profile.candidate.get("resume_path", "")
    for _ in range(max_pages):
        page.wait_for_load_state()
        fields = page.evaluate(COLLECT_JS)
        plan = llm.generate_json(PROMPT.format(
            candidate=json.dumps(profile.candidate), answers=json.dumps(profile.answers),
            job=json.dumps(job), fields=_fields_for_llm(fields)))
        if plan.get("done"):
            return True
        valid = {f["id"] for f in fields}
        for act in plan.get("actions", []):
            if act.get("id") not in valid:
                continue
            loc = page.locator(f'[data-jb-id="{act["id"]}"]')
            kind, value = act.get("action"), act.get("value", "")
            if kind == "fill":
                loc.fill(str(value))
            elif kind == "select":
                loc.select_option(label=str(value))
            elif kind == "check":
                loc.check()
            elif kind == "upload" and resume:
                loc.set_input_files(resume)
            elif kind == "click":
                loc.click()
        submit_id, next_id = plan.get("submit"), plan.get("next")
        target = submit_id if submit_id in valid else next_id if next_id in valid else None
        if target is None:
            return False
        if target == submit_id and dry_run:
            return False
        page.locator(f'[data-jb-id="{target}"]').click()
        if target == submit_id:
            page.wait_for_load_state()
            return True
    return False


def apply_all(llm, profile: Profile, jobs: list[dict], headless: bool = False, dry_run: bool = False) -> dict[str, bool]:
    from playwright.sync_api import sync_playwright

    results = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        for job in jobs:
            page = browser.new_page()
            try:
                results[job["url"]] = apply_to_job(page, llm, profile, job, dry_run=dry_run)
            except Exception as exc:  # keep going with remaining jobs
                print(f"Error applying to {job['url']}: {exc}")
                results[job["url"]] = False
            finally:
                page.close()
        browser.close()
    return results
