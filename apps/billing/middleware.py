from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException
from .services import has_access, VerificationUnavailable


class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (settings.BILLING_REQUIRED and request.user.is_authenticated
                and request.path.startswith(("/dashboard/", "/profiles/"))):
            try:
                if not has_access(request.user):
                    return redirect("subscription")
            except (VerificationUnavailable, GoogleAuthError, RequestException):
                return HttpResponse("Subscription verification is temporarily unavailable. Please retry.", status=503)
        return self.get_response(request)
