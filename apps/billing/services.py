from datetime import timedelta
from urllib.parse import quote

import google.auth
from google.auth.transport.requests import AuthorizedSession
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.dateparse import parse_datetime

from .models import Subscription


ACTIVE_STATES = {
    "SUBSCRIPTION_STATE_ACTIVE",
    "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
    "SUBSCRIPTION_STATE_CANCELED",
}


class VerificationUnavailable(Exception):
    pass


def account_id(user):
    return salted_hmac("play-billing-account", str(user.pk), algorithm="sha256").hexdigest()


def play_request(token, acknowledge=False):
    credentials, _ = google.auth.default(scopes=[
        "https://www.googleapis.com/auth/androidpublisher"
    ])
    root = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
    root += quote(settings.PLAY_PACKAGE_NAME, safe="") + "/purchases/"
    with AuthorizedSession(credentials) as session:
        if acknowledge:
            url = root + "subscriptions/" + quote(settings.PLAY_SUBSCRIPTION_ID, safe="")
            response = session.post(url + "/tokens/" + quote(token, safe="") + ":acknowledge", json={}, timeout=15)
        else:
            response = session.get(root + "subscriptionsv2/tokens/" + quote(token, safe=""), timeout=15)
        if response.status_code in (400, 404, 410):
            raise PermissionDenied("Purchase is invalid or expired.")
        if not response.ok:
            raise VerificationUnavailable("Google Play verification is unavailable.")
        return response.json() if not acknowledge else None


def verify_purchase(user, token):
    if not isinstance(token, str) or not 1 <= len(token) <= 2048:
        raise PermissionDenied("Invalid purchase token.")
    data = play_request(token)
    if data.get("externalAccountIdentifiers", {}).get("obfuscatedExternalAccountId") != account_id(user):
        raise PermissionDenied("This purchase belongs to a different app account.")
    lines = [line for line in data.get("lineItems", [])
             if line.get("productId") == settings.PLAY_SUBSCRIPTION_ID
             and line.get("offerDetails", {}).get("basePlanId") == settings.PLAY_BASE_PLAN_ID]
    expiries = [parse_datetime(line.get("expiryTime", "")) for line in lines]
    expiries = [expiry for expiry in expiries if expiry and timezone.is_aware(expiry)]
    if not expiries:
        raise PermissionDenied("Unexpected subscription product or expiration.")
    if (data.get("subscriptionState") in ACTIVE_STATES
            and max(expiries) > timezone.now()
            and data.get("acknowledgementState") == "ACKNOWLEDGEMENT_STATE_PENDING"):
        play_request(token, acknowledge=True)
    with transaction.atomic():
        subscription, _ = Subscription.objects.select_for_update().get_or_create(
            token=token, defaults={"user": user, "state": "", "expires_at": max(expiries)},
        )
        if subscription.user_id != user.pk:
            raise PermissionDenied("Purchase already belongs to another account.")
        subscription.state = data.get("subscriptionState", "")
        subscription.expires_at = max(expiries)
        subscription.save()
    return subscription


def has_access(user):
    for subscription in Subscription.objects.filter(user=user, expires_at__gt=timezone.now()):
        if subscription.checked_at < timezone.now() - timedelta(minutes=5):
            try:
                subscription = verify_purchase(user, subscription.token)
            except PermissionDenied:
                subscription.state = "INVALID"
                subscription.save()
                continue
        if subscription.state in ACTIVE_STATES and subscription.expires_at > timezone.now():
            return True
    return False
