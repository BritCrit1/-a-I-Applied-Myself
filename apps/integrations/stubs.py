from apps.integrations.providers import BrowserTask, JobMatch, ParsedResume


class StubLLMProvider:
    def parse_resume(self, raw_text: str) -> ParsedResume:
        return ParsedResume(other_qualifications=[raw_text[:500]] if raw_text else [])

    def score_job(self, profile: dict, job: dict) -> JobMatch:
        return JobMatch(score=0, reasoning="Scoring provider is not configured.", career_alignment="unknown")

    def generate_application_answer(self, profile: dict, question: str) -> str | None:
        return None

    def classify_correspondence(self, message: dict) -> str:
        return "unknown"

    def draft_follow_up(self, application: dict) -> str:
        return ""


class StubBrowserAgent:
    def discover_jobs(self, criteria: dict) -> BrowserTask:
        return BrowserTask(task_id="stub-discover", status="action_required", requires_human=True)

    def inspect_job(self, job_ref: dict) -> BrowserTask:
        return BrowserTask(task_id="stub-inspect", status="action_required", requires_human=True)

    def apply_to_job(self, application_payload: dict) -> BrowserTask:
        return BrowserTask(task_id="stub-apply", status="action_required", requires_human=True)

    def get_task_status(self, task_id: str) -> BrowserTask:
        return BrowserTask(task_id=task_id, status="action_required", requires_human=True)


class StubGmailProvider:
    def list_application_messages(self, user_id: int) -> list[dict]:
        return []

    def send_follow_up(self, message: dict) -> str:
        raise RuntimeError("Gmail provider is not configured.")
