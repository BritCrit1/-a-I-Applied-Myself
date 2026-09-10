from django.utils import timezone

from apps.integrations.factory import get_llm_provider
from apps.profiles.models import CandidateProfile, Resume


def extract_text_from_resume(resume: Resume) -> str:
    name = resume.original_filename.lower()
    if name.endswith(".txt"):
        with resume.file.open("rb") as handle:
            return handle.read().decode("utf-8", errors="replace")
    return ""


def parse_resume_into_profile(resume: Resume) -> CandidateProfile:
    provider = get_llm_provider()
    parsed = provider.parse_resume(extract_text_from_resume(resume))
    resume.parsed_payload = {
        "name": parsed.name,
        "phone": parsed.phone,
        "email": parsed.email,
        "location": parsed.location,
        "employment_history": parsed.employment_history,
        "education": parsed.education,
        "skills": parsed.skills,
        "certifications": parsed.certifications,
        "other_qualifications": parsed.other_qualifications,
    }
    resume.status = Resume.Status.NEEDS_REVIEW
    resume.failure_reason = ""
    resume.save(update_fields=["parsed_payload", "status", "failure_reason", "updated_at"])

    profile, _ = CandidateProfile.objects.update_or_create(
        user=resume.user,
        defaults={
            "resume": resume,
            "full_name": parsed.name,
            "phone": parsed.phone,
            "email": parsed.email or resume.user.email,
            "location": parsed.location,
            "employment_history": parsed.employment_history,
            "education": parsed.education,
            "skills": parsed.skills,
            "certifications": parsed.certifications,
            "other_qualifications": parsed.other_qualifications,
            "confirmed_at": None,
        },
    )
    return profile


def confirm_profile(profile: CandidateProfile) -> CandidateProfile:
    profile.confirmed_at = timezone.now()
    profile.save(update_fields=["confirmed_at", "updated_at"])
    return profile
