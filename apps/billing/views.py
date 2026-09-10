import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.http import require_POST
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException

from .services import VerificationUnavailable, account_id, verify_purchase, ACTIVE_STATES
from django.utils import timezone


@login_required
def paywall(request):
    return render(request, "billing/paywall.html")


@login_required
def configuration(request):
    response = JsonResponse({"accountId": account_id(request.user), "csrfToken": get_token(request)})
    response["Cache-Control"] = "no-store"
    return response


@login_required
@require_POST
def verify(request):
    try:
        body = json.loads(request.body)
        if not isinstance(body, dict):
            raise ValueError()
        subscription = verify_purchase(request.user, body.get("purchaseToken"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid request."}, status=400)
    except PermissionDenied as exc:
        return JsonResponse({"error": str(exc)}, status=403)
    except (VerificationUnavailable, GoogleAuthError, RequestException):
        return JsonResponse({"error": "Unable to verify purchase. Please retry."}, status=503)
    return JsonResponse({"active": subscription.state in ACTIVE_STATES
                         and subscription.expires_at > timezone.now()})
