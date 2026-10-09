from __future__ import annotations

import click

from .applicant import apply_all
from .llm import Gemini
from .profile import load_profile
from .resume import review_resume
from .search import find_jobs


@click.group()
def main() -> None:
    """Review a resume, find matching jobs, and apply."""


@main.command()
@click.argument("resume", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output", default="job_profile.md", show_default=True, help="Profile file to write.")
def generate(resume: str, output: str) -> None:
    """Review a PDF resume and write the Markdown profile."""
    llm = Gemini()
    with open(output, "w", encoding="utf-8") as fh:
        fh.write(review_resume(llm, resume))
    click.echo(f"Wrote {output}. Edit it, then run: job-bot run")


@main.command()
@click.option("-p", "--profile", "profile_path", default="job_profile.md", show_default=True)
@click.option("--headless", is_flag=True, help="Run the browser headless.")
@click.option("--dry-run", is_flag=True, help="Fill forms but do not submit.")
@click.option("--search-only", is_flag=True, help="Only print job URLs.")
def run(profile_path: str, headless: bool, dry_run: bool, search_only: bool) -> None:
    """Search for jobs and apply."""
    llm = Gemini()
    profile = load_profile(profile_path)
    jobs = find_jobs(llm, profile)
    for j in jobs:
        click.echo(f"{j['title']} @ {j['company']}: {j['url']}")
    if search_only:
        return
    results = apply_all(llm, profile, jobs, headless=headless, dry_run=dry_run)
    for url, ok in results.items():
        click.echo(("SUBMITTED " if ok else "NOT SUBMITTED ") + url)


if __name__ == "__main__":
    main()
