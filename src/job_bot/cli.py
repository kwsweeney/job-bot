from __future__ import annotations

import argparse
import sys

from .applicant import apply_all
from .llm import Gemini
from .profile import load_profile
from .resume import review_resume
from .search import find_jobs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="job-bot")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="Review a PDF resume and write the Markdown profile")
    g.add_argument("resume")
    g.add_argument("-o", "--output", default="job_profile.md")
    r = sub.add_parser("run", help="Search for jobs and apply")
    r.add_argument("-p", "--profile", default="job_profile.md")
    r.add_argument("--headless", action="store_true")
    r.add_argument("--dry-run", action="store_true", help="Fill forms but do not submit")
    r.add_argument("--search-only", action="store_true", help="Only print job URLs")
    args = ap.parse_args(argv)

    llm = Gemini()
    if args.cmd == "generate":
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(review_resume(llm, args.resume))
        print(f"Wrote {args.output}. Edit it, then run: job-bot run")
        return 0

    profile = load_profile(args.profile)
    jobs = find_jobs(llm, profile)
    for j in jobs:
        print(f"{j['title']} @ {j['company']}: {j['url']}")
    if args.search_only:
        return 0
    results = apply_all(llm, profile, jobs, headless=args.headless, dry_run=args.dry_run)
    for url, ok in results.items():
        print(("SUBMITTED " if ok else "NOT SUBMITTED ") + url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
