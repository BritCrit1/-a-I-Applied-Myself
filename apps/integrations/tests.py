from django.test import TestCase

from apps.integrations.factory import get_browser_agent, get_gmail_provider, get_llm_provider


class StubProviderTests(TestCase):
    def test_stub_llm_provider_returns_structured_resume(self):
        provider = get_llm_provider()
        parsed = provider.parse_resume("Python, SQL, and Django")
        self.assertEqual(parsed.other_qualifications, ["Python, SQL, and Django"])

    def test_stub_browser_agent_requires_human_action(self):
        task = get_browser_agent().discover_jobs({"zip_code": "78701"})
        self.assertTrue(task.requires_human)
        self.assertEqual(task.status, "action_required")

    def test_stub_gmail_provider_does_not_send(self):
        with self.assertRaises(RuntimeError):
            get_gmail_provider().send_follow_up({"body": "Hello"})
