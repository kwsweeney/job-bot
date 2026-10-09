# job-bot
A bot that reviews your PDF resume with Gemini, searches the web for matching jobs, and fills out and submits applications (multi-page supported) in a browser.

## Setup
```
poetry install
poetry run playwright install chromium
export GEMINI_API_KEY=...        # optional: GEMINI_MODEL
```

## Usage
1. `poetry run job-bot generate resume.pdf -o job_profile.md` – Gemini reviews the resume and writes a Markdown profile.
2. Edit `job_profile.md`: target roles, example titles, company types, `salary_min`/`salary_max`, `num_roles` (how many jobs to find and apply to), your contact info, and **Application Answers** (veteran status, disability, gender, sponsorship, ...). Gemini reads each form and picks the matching answer from this file.
3. `poetry run job-bot run -p job_profile.md` – searches (Gemini + Google Search grounding) until `num_roles` job URLs are found, then drives a Playwright browser through each application page by page and submits.

Flags for `run`: `--dry-run` (fill but don't submit), `--search-only` (print URLs), `--headless`.

Tests: `poetry run pytest`.

## Things to know
- Try `--dry-run` (fills forms without submitting) or `--search-only` (prints job URLs) before a real run.
- Search runs up to three rounds to reach `num_roles` unique job URLs; it may return fewer.
- Each application is limited to 15 pages. If no Next/Submit button is found on a page, that application stops without submitting.
- A job that errors is skipped and the rest continue; the final output lists each URL as submitted or not.
- Not supported: sites that require a login, CAPTCHAs, and custom dropdowns that aren't a real `<select>` element.
- `GEMINI_MODEL` is optional and defaults to `gemini-2.5-flash`.
