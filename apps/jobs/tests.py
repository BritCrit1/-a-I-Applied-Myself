from django.contrib.auth.models import User
from django.test import TestCase

from apps.jobs.models import Application, Job, JobSource
from apps.jobs.services import build_job_fingerprint, canonicalize_url, salary_label
from apps.jobs.state_machine import InvalidStateTransition, transition_application


class JobNormalizationTests(TestCase):
    def test_canonicalize_url_removes_query_and_fragment(self):
        self.assertEqual(
            canonicalize_url("HTTPS://Example.com/jobs/123/?utm_source=x#apply"),
            "https://example.com/jobs/123",
        )

    def test_fingerprint_prefers_provider_id(self):
        first = build_job_fingerprint(
            provider_job_id="abc",
            canonical_url="https://example.com/jobs/1",
            company="One",
            title="Engineer",
            location="Remote",
        )
        second = build_job_fingerprint(
            provider_job_id="abc",
            canonical_url="https://other.test/jobs/2",
            company="Two",
            title="Designer",
            location="Austin",
        )
        self.assertEqual(first, second)

    def test_salary_label_never_estimates_unlisted_salary(self):
        self.assertEqual(
            salary_label(100000, 120000, employer_listed=False),
            "Employer-listed salary unavailable",
        )
        self.assertEqual(salary_label(100000, 120000, employer_listed=True), "$100,000 - $120,000")


class ApplicationStateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="candidate", password="test-pass")
        self.source = JobSource.objects.create(name="Example Board", provider_key="example")
        self.job = Job.objects.create(
            source=self.source,
            title="Software Engineer",
            company="Acme",
            normalized_fingerprint="abc",
        )
        self.application = Application.objects.create(user=self.user, job=self.job)

    def test_valid_transition_updates_state(self):
        transition_application(self.application, Application.State.SCORED)
        self.application.refresh_from_db()
        self.assertEqual(self.application.state, Application.State.SCORED)

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(InvalidStateTransition):
            transition_application(self.application, Application.State.APPLIED)

    def test_action_required_records_reason(self):
        transition_application(self.application, Application.State.SCORED)
        transition_application(self.application, Application.State.ACTION_REQUIRED, reason="Unknown legal attestation")
        self.application.refresh_from_db()
        self.assertEqual(self.application.action_required_reason, "Unknown legal attestation")
