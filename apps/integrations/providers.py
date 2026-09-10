from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ParsedResume:
    name: str = ""
    phone: str = ""
    email: str = ""
    location: str = ""
    employment_history: list[dict] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    other_qualifications: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JobMatch:
    score: int
    reasoning: str
    career_alignment: str


@dataclass(frozen=True)
class BrowserTask:
    task_id: str
    status: str
    result: dict = field(default_factory=dict)
    failure_reason: str = ""
    requires_human: bool = False


class LLMProvider(Protocol):
    def parse_resume(self, raw_text: str) -> ParsedResume:
        ...

    def score_job(self, profile: dict, job: dict) -> JobMatch:
        ...

    def generate_application_answer(self, profile: dict, question: str) -> str | None:
        ...

    def classify_correspondence(self, message: dict) -> str:
        ...

    def draft_follow_up(self, application: dict) -> str:
        ...


class BrowserAgent(Protocol):
    def discover_jobs(self, criteria: dict) -> BrowserTask:
        ...

    def inspect_job(self, job_ref: dict) -> BrowserTask:
        ...

    def apply_to_job(self, application_payload: dict) -> BrowserTask:
        ...

    def get_task_status(self, task_id: str) -> BrowserTask:
        ...


class GmailProvider(Protocol):
    def list_application_messages(self, user_id: int) -> list[dict]:
        ...

    def send_follow_up(self, message: dict) -> str:
        ...
