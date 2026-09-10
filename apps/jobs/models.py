from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel
from apps.profiles.models import SearchPreference


class JobSource(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    provider_key = models.CharField(max_length=80, unique=True)
    base_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Job(TimeStampedModel):
    class WorkMode(models.TextChoices):
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"
        ONSITE = "onsite", "Onsite"
        UNKNOWN = "unknown", "Unknown"

    class CareerAlignment(models.TextChoices):
        STRONG_MATCH = "strong_match", "Strong Match"
        LATERAL = "lateral", "Lateral"
        ENTRY_LEVEL_SHIFT = "entry_level_shift", "Entry-Level Shift"
        UNKNOWN = "unknown", "Unknown"

    source = models.ForeignKey(JobSource, on_delete=models.PROTECT, related_name="jobs")
    provider_job_id = models.CharField(max_length=160, blank=True)
    canonical_url = models.URLField(max_length=1000, blank=True)
    title = models.CharField(max_length=240)
    company = models.CharField(max_length=240)
    location = models.CharField(max_length=240, blank=True)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.UNKNOWN)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    salary_is_employer_listed = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    requirements = models.JSONField(default=list, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    match_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    match_reasoning = models.TextField(blank=True)
    career_alignment = models.CharField(
        max_length=30,
        choices=CareerAlignment.choices,
        default=CareerAlignment.UNKNOWN,
    )
    normalized_fingerprint = models.CharField(max_length=128, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "provider_job_id"],
                name="unique_provider_job_id_per_source",
                condition=~models.Q(provider_job_id=""),
            ),
            models.UniqueConstraint(
                fields=["canonical_url"],
                name="unique_job_canonical_url",
                condition=~models.Q(canonical_url=""),
            ),
        ]
        indexes = [
            models.Index(fields=["company", "title", "location"]),
            models.Index(fields=["match_score"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} at {self.company}"


class Application(TimeStampedModel):
    class State(models.TextChoices):
        DISCOVERED = "discovered", "Discovered"
        SCORED = "scored", "Scored"
        QUEUED = "queued", "Queued"
        APPLYING = "applying", "Applying"
        APPLIED = "applied", "Applied"
        AWAITING_RESPONSE = "awaiting_response", "Awaiting Response"
        ACTION_REQUIRED = "action_required", "Action Required"
        INTERVIEW = "interview", "Interview"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"
        CLOSED = "closed", "Closed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    search_preference = models.ForeignKey(
        SearchPreference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    state = models.CharField(max_length=30, choices=State.choices, default=State.DISCOVERED)
    auto_submit_authorized = models.BooleanField(default=False)
    action_required_reason = models.TextField(blank=True)
    last_state_change_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "job")]
        indexes = [
            models.Index(fields=["user", "state"]),
            models.Index(fields=["last_state_change_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.job}"


class ApplicationAttempt(TimeStampedModel):
    class Outcome(models.TextChoices):
        STARTED = "started", "Started"
        SUBMITTED = "submitted", "Submitted"
        ACTION_REQUIRED = "action_required", "Action Required"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="attempts")
    outcome = models.CharField(max_length=30, choices=Outcome.choices)
    provider_task_id = models.CharField(max_length=160, blank=True)
    details = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)


class AgentTask(TimeStampedModel):
    class TaskType(models.TextChoices):
        DISCOVER_JOBS = "discover_jobs", "Discover Jobs"
        INSPECT_JOB = "inspect_job", "Inspect Job"
        APPLY_TO_JOB = "apply_to_job", "Apply To Job"
        CLASSIFY_CORRESPONDENCE = "classify_correspondence", "Classify Correspondence"
        DRAFT_FOLLOWUP = "draft_followup", "Draft Follow-Up"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        TIMED_OUT = "timed_out", "Timed Out"
        ACTION_REQUIRED = "action_required", "Action Required"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_tasks")
    task_type = models.CharField(max_length=40, choices=TaskType.choices)
    provider = models.CharField(max_length=80)
    provider_task_id = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    input_payload = models.JSONField(default=dict, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    failure_reason = models.TextField(blank=True)


class Communication(TimeStampedModel):
    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    class Classification(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        RECRUITER_RESPONSE = "recruiter_response", "Recruiter Response"
        INTERVIEW_INVITE = "interview_invite", "Interview Invite"
        REJECTION = "rejection", "Rejection"
        ADDITIONAL_INFO = "additional_info", "Additional Information"

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="communications",
        null=True,
        blank=True,
    )
    external_message_id = models.CharField(max_length=255, blank=True, db_index=True)
    direction = models.CharField(max_length=20, choices=Direction.choices)
    sender = models.EmailField(blank=True)
    recipient = models.EmailField(blank=True)
    subject = models.CharField(max_length=255, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    classification = models.CharField(
        max_length=40,
        choices=Classification.choices,
        default=Classification.UNKNOWN,
    )
    raw_metadata = models.JSONField(default=dict, blank=True)


class FollowUp(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DRAFTED = "drafted", "Drafted"
        SENT = "sent", "Sent"
        CANCELLED = "cancelled", "Cancelled"
        ACTION_REQUIRED = "action_required", "Action Required"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="followups")
    due_at = models.DateTimeField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    draft_body = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)


class RunSetting(TimeStampedModel):
    class RunMode(models.TextChoices):
        AUTO = "auto", "Automatic"
        MANUAL = "manual", "Manual"
        SCHEDULED = "scheduled", "Scheduled"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="run_setting")
    run_mode = models.CharField(max_length=20, choices=RunMode.choices, default=RunMode.MANUAL)
    max_applications_per_run = models.PositiveSmallIntegerField(default=5)
    min_match_score = models.PositiveSmallIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    schedule_start = models.TimeField(null=True, blank=True)
    schedule_end = models.TimeField(null=True, blank=True)
    cadence = models.CharField(max_length=40, blank=True)
    auto_submit = models.BooleanField(default=False)
    linkedin_connected = models.BooleanField(default=False)
