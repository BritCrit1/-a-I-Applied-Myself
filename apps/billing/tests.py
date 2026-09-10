from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings, Client
from django.utils import timezone

from .models import Subscription
from .services import account_id, has_access, verify_purchase, VerificationUnavailable


class BillingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="subscriber", password="test-password")
        self.data = {
            "externalAccountIdentifiers": {"obfuscatedExternalAccountId": account_id(self.user)},
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "acknowledgementState": "ACKNOWLEDGEMENT_STATE_PENDING",
            "lineItems": [{"productId": "premium", "offerDetails": {"basePlanId": "weekly"},
                           "expiryTime": (timezone.now() + timedelta(days=7)).isoformat()}],
        }

    @patch("apps.billing.services.play_request")
    def test_verified_purchase_is_acknowledged_and_grants_access(self, play):
        play.return_value = self.data
        verify_purchase(self.user, "token")
        self.assertTrue(has_access(self.user))
        play.assert_any_call("token", acknowledge=True)

    @patch("apps.billing.services.play_request")
    def test_failed_acknowledgement_does_not_grant_access(self, play):
        play.side_effect = [self.data, VerificationUnavailable()]
        with self.assertRaises(VerificationUnavailable):
            verify_purchase(self.user, "token")
        self.assertFalse(has_access(self.user))

    @patch("apps.billing.services.play_request")
    def test_purchase_cannot_be_claimed_by_other_user(self, play):
        play.return_value = self.data
        other = get_user_model().objects.create_user(username="other")
        with self.assertRaises(PermissionDenied):
            verify_purchase(other, "token")
        self.assertFalse(Subscription.objects.exists())

    @patch("apps.billing.services.play_request")
    def test_wrong_plan_rejected(self, play):
        self.data["lineItems"][0]["offerDetails"]["basePlanId"] = "unrelated"
        play.return_value = self.data
        with self.assertRaises(PermissionDenied):
            verify_purchase(self.user, "token")

    @patch("apps.billing.services.play_request")
    def test_expired_and_on_hold_deny_access(self, play):
        play.return_value = self.data
        for state in ("SUBSCRIPTION_STATE_ON_HOLD", "SUBSCRIPTION_STATE_EXPIRED", "SUBSCRIPTION_STATE_PENDING"):
            self.data["subscriptionState"] = state
            verify_purchase(self.user, "token")
            self.assertFalse(has_access(self.user))

    @patch("apps.billing.services.play_request")
    def test_cancelled_subscription_keeps_access_until_expiry(self, play):
        self.data["subscriptionState"] = "SUBSCRIPTION_STATE_CANCELED"
        play.return_value = self.data
        verify_purchase(self.user, "token")
        self.assertTrue(has_access(self.user))
        Subscription.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertFalse(has_access(self.user))

    @patch("apps.billing.services.play_request")
    def test_stale_access_rechecks_revocation(self, play):
        play.return_value = self.data
        verify_purchase(self.user, "token")
        Subscription.objects.update(checked_at=timezone.now() - timedelta(minutes=6))
        self.data["subscriptionState"] = "SUBSCRIPTION_STATE_EXPIRED"
        self.assertFalse(has_access(self.user))

    @override_settings(BILLING_REQUIRED=True)
    def test_unpaid_user_cannot_bypass_paywall(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get("/dashboard/"), "/billing/", fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/profiles/"), "/billing/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/billing/").status_code, 200)

    def test_verification_requires_csrf_and_authentication(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post("/billing/verify/", {}, content_type="application/json").status_code, 403)
        self.assertEqual(self.client.get("/billing/config/").status_code, 302)
