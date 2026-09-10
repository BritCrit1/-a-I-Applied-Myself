from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


def resume_upload_path(instance: "Resume", filename: str) -> str:
    return f"resumes/user_{instance.user_id}/{filename}"


class Resume(TimeStampedModel):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PARSED = "parsed", "Parsed"
        NEEDS_REVIEW = "needs_review", "Needs Review"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to=resume_upload_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    parsed_payload = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return self.original_filename


class CandidateProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=160, blank=True)
    employment_history = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    other_qualifications = models.JSONField(default=list, blank=True)
    work_authorization = models.CharField(max_length=160, blank=True)
    security_clearance = models.CharField(max_length=160, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.full_name or self.user.get_username()


class SearchPreference(TimeStampedModel):
    class SearchIntent(models.TextChoices):
        STRONG_MATCH = "strong_match", "Strong resume and skill match"
        LATERAL_SHIFT = "lateral_shift", "Lateral career shift"
        ENTRY_LEVEL_SHIFT = "entry_level_shift", "Entry-level work in another field"

    class WorkMode(models.TextChoices):
        LOCAL = "local", "Local"
        HYBRID = "hybrid", "Hybrid"
        REMOTE = "remote", "Remote"
        ANY = "any", "Any"

    class Priority(models.TextChoices):
        SKILL_MATCH = "skill_match", "Strongest skill match"
        SALARY = "salary", "Highest salary"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_preference",
    )
    search_intent = models.CharField(max_length=30, choices=SearchIntent.choices)
    zip_code = models.CharField(max_length=12)
    search_radius_miles = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(250)]
    )
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.ANY)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.SKILL_MATCH)
    minimum_salary = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.get_username()} search preferences"
