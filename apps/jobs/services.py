import hashlib
import re
from urllib.parse import urlsplit, urlunsplit


WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.strip().lower())


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(url.strip())
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))


def build_job_fingerprint(
    *,
    provider_job_id: str = "",
    canonical_url: str = "",
    company: str,
    title: str,
    location: str = "",
) -> str:
    if provider_job_id:
        material = f"provider:{provider_job_id}"
    elif canonical_url:
        material = f"url:{canonicalize_url(canonical_url)}"
    else:
        material = "|".join(
            [
                normalize_text(company),
                normalize_text(title),
                normalize_text(location),
            ]
        )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def salary_label(salary_min: int | None, salary_max: int | None, employer_listed: bool) -> str:
    if not employer_listed or (salary_min is None and salary_max is None):
        return "Employer-listed salary unavailable"
    if salary_min is not None and salary_max is not None:
        return f"${salary_min:,} - ${salary_max:,}"
    if salary_min is not None:
        return f"From ${salary_min:,}"
    return f"Up to ${salary_max:,}"
