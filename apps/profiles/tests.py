from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.profiles.models import CandidateProfile, Resume, SearchPreference


class OnboardingFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="candidate",
            email="candidate@example.com",
            password="test-pass",
        )

    def test_resume_upload_creates_resume_and_profile(self):
        self.client.login(username="candidate", password="test-pass")
        uploaded = SimpleUploadedFile(
            "resume.txt",
            b"Experienced Python developer with Django and SQL skills.",
            content_type="text/plain",
        )

        response = self.client.post(reverse("resume_upload"), {"file": uploaded})

        self.assertRedirects(response, reverse("profile_confirm"))
        resume = Resume.objects.get(user=self.user)
        profile = CandidateProfile.objects.get(user=self.user)
        self.assertEqual(resume.status, Resume.Status.NEEDS_REVIEW)
        self.assertEqual(profile.email, "candidate@example.com")
        self.assertIn("Experienced Python developer", profile.other_qualifications[0])

    def test_profile_confirmation_sets_confirmed_at(self):
        resume = Resume.objects.create(user=self.user, original_filename="resume.txt")
        CandidateProfile.objects.create(user=self.user, resume=resume, email=self.user.email)
        self.client.login(username="candidate", password="test-pass")

        response = self.client.post(
            reverse("profile_confirm"),
            {
                "full_name": "Candidate User",
                "phone": "555-0100",
                "email": "candidate@example.com",
                "location": "Austin, TX",
                "work_authorization": "",
                "security_clearance": "",
            },
        )

        self.assertRedirects(response, reverse("search_preferences"))
        profile = CandidateProfile.objects.get(user=self.user)
        self.assertIsNotNone(profile.confirmed_at)
        self.assertEqual(profile.full_name, "Candidate User")

    def test_search_preferences_are_saved(self):
        self.client.login(username="candidate", password="test-pass")

        response = self.client.post(
            reverse("search_preferences"),
            {
                "search_intent": SearchPreference.SearchIntent.STRONG_MATCH,
                "zip_code": "78701",
                "search_radius_miles": 25,
                "work_mode": SearchPreference.WorkMode.HYBRID,
                "priority": SearchPreference.Priority.SKILL_MATCH,
                "minimum_salary": 90000,
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        preference = SearchPreference.objects.get(user=self.user)
        self.assertEqual(preference.zip_code, "78701")
