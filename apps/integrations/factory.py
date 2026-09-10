from django.conf import settings

from apps.integrations.stubs import StubBrowserAgent, StubGmailProvider, StubLLMProvider


def get_llm_provider():
    if settings.LLM_PROVIDER == "stub":
        return StubLLMProvider()
    raise NotImplementedError(f"LLM provider {settings.LLM_PROVIDER!r} is not implemented.")


def get_browser_agent():
    return StubBrowserAgent()


def get_gmail_provider():
    return StubGmailProvider()
