from django.utils import timezone

from apps.jobs.models import Application


ALLOWED_TRANSITIONS = {
    Application.State.DISCOVERED: {Application.State.SCORED, Application.State.CLOSED},
    Application.State.SCORED: {Application.State.QUEUED, Application.State.ACTION_REQUIRED, Application.State.CLOSED},
    Application.State.QUEUED: {Application.State.APPLYING, Application.State.WITHDRAWN},
    Application.State.APPLYING: {
        Application.State.APPLIED,
        Application.State.ACTION_REQUIRED,
        Application.State.FAILED,
    },
    Application.State.APPLIED: {Application.State.AWAITING_RESPONSE, Application.State.INTERVIEW, Application.State.REJECTED},
    Application.State.AWAITING_RESPONSE: {
        Application.State.INTERVIEW,
        Application.State.REJECTED,
        Application.State.ACTION_REQUIRED,
        Application.State.WITHDRAWN,
    },
    Application.State.ACTION_REQUIRED: {Application.State.QUEUED, Application.State.WITHDRAWN, Application.State.FAILED},
    Application.State.INTERVIEW: {Application.State.REJECTED, Application.State.WITHDRAWN, Application.State.CLOSED},
    Application.State.REJECTED: set(),
    Application.State.WITHDRAWN: set(),
    Application.State.CLOSED: set(),
    Application.State.FAILED: {Application.State.QUEUED, Application.State.ACTION_REQUIRED},
}


class InvalidStateTransition(ValueError):
    pass


def transition_application(application: Application, new_state: str, *, reason: str = "") -> Application:
    current = Application.State(application.state)
    target = Application.State(new_state)
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransition(f"Cannot transition application from {current} to {target}.")

    application.state = target
    application.action_required_reason = reason if target == Application.State.ACTION_REQUIRED else ""
    application.last_state_change_at = timezone.now()
    application.save(update_fields=["state", "action_required_reason", "last_state_change_at", "updated_at"])
    return application
