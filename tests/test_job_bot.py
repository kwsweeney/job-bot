from job_bot.applicant import apply_to_job
from job_bot.llm import extract_json
from job_bot.profile import Profile, parse_profile, render_profile
from job_bot.resume import build_profile
from job_bot.search import find_jobs


def test_extract_json_fenced():
    assert extract_json('hi ```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('text [1, 2] more') == [1, 2]


def test_profile_roundtrip():
    p = build_profile({"roles": ["Backend"], "titles": ["SWE"], "companies": ["Startup"],
                       "salary_min": 100000, "salary_max": 150000,
                       "candidate": {"full_name": "A B"}}, "r.pdf")
    p.num_roles = 3
    q = parse_profile(render_profile(p))
    assert (q.roles, q.titles, q.companies) == (["Backend"], ["SWE"], ["Startup"])
    assert (q.salary_min, q.salary_max, q.num_roles) == (100000, 150000, 3)
    assert q.candidate["full_name"] == "A B" and q.candidate["resume_path"] == "r.pdf"
    assert q.answers["veteran_status"]


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)

    def search(self, prompt):
        return self.responses.pop(0)

    def generate_json(self, prompt):
        return self.responses.pop(0)


def test_find_jobs_dedupes_and_tops_up():
    llm = FakeLLM(['[{"title":"a","company":"c","url":"http://x/1"}]',
                   '[{"title":"a","company":"c","url":"http://x/1"},{"title":"b","company":"c","url":"http://x/2"}]'])
    jobs = find_jobs(llm, Profile(num_roles=2))
    assert [j["url"] for j in jobs] == ["http://x/1", "http://x/2"]


class FakeLocator:
    def __init__(self, page, sel):
        self.page, self.sel = page, sel

    def fill(self, v): self.page.log.append(("fill", self.sel, v))
    def click(self): self.page.log.append(("click", self.sel))


class FakePage:
    def __init__(self, pages):
        self.pages, self.i, self.log = pages, 0, []

    def goto(self, url): pass
    def wait_for_load_state(self): pass
    def evaluate(self, js): return self.pages[self.i]

    def locator(self, sel):
        loc = FakeLocator(self, sel)
        orig = loc.click
        def click():
            orig()
            if "jb1" in sel and self.i < len(self.pages) - 1:
                self.i += 1
        loc.click = click
        return loc


def test_multi_page_application():
    pages = [[{"id": "jb0", "tag": "input", "label": "Name"}, {"id": "jb1", "tag": "button", "text": "Next"}],
             [{"id": "jb0", "tag": "input", "label": "Veteran"}, {"id": "jb1", "tag": "button", "text": "Submit"}]]
    llm = FakeLLM([
        {"actions": [{"id": "jb0", "action": "fill", "value": "A B"}], "next": "jb1"},
        {"actions": [{"id": "jb0", "action": "fill", "value": "No"}], "submit": "jb1"},
    ])
    page = FakePage(pages)
    assert apply_to_job(page, llm, Profile(), {"url": "http://x"}) is True
    assert ("fill", '[data-jb-id="jb0"]', "No") in page.log
    assert page.i == 1


def test_dry_run_does_not_submit():
    page = FakePage([[{"id": "jb1", "tag": "button", "text": "Submit"}]])
    llm = FakeLLM([{"actions": [], "submit": "jb1"}])
    assert apply_to_job(page, llm, Profile(), {"url": "http://x"}, dry_run=True) is False
    assert not page.log
