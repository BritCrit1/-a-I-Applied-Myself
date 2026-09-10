# AIAMS Android Release

Status: Android shell and subscription verification implemented. This is not yet
a production-ready paid service: the existing LLM, browser agent and Gmail
providers remain stubs. Complete those workflows before accepting payments.

## Identity and build

- App label and delivery filename: AIAMS / AIAMS.apk.
- Default Play application ID: `com.britcrit.aiams`. Finalize before the first
  upload; changing it creates a different Play app.
- Requires JDK 17 and Android SDK 36. Open `android/` in Android Studio.
- Configure the Android SDK through Android Studio or `ANDROID_HOME`.
- Debug: `./gradlew assembleDebug -PappUrl=https://YOUR-CLOUD-RUN-HOST`
- Without appUrl, the debug APK displays an explicit unconfigured preview screen.
- Release: set `ANDROID_KEYSTORE`, `ANDROID_KEYSTORE_PASSWORD`,
  `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` in the build environment, then run
  `./gradlew bundleRelease assembleRelease -PappUrl=https://YOUR-CLOUD-RUN-HOST`.
- Output: `app/build/outputs/bundle/release/app-release.aab` for Play;
  `app/build/outputs/apk/release/app-release.apk` for direct installation.
- Release builds reject a missing server address or missing signing configuration.
- Keep the upload keystore backed up privately. Never commit it or credentials.

## Play Console subscription

Create the application as free to download, with Google Play App Signing enabled.
Create subscription `premium`, auto-renewing base plan `weekly`, weekly billing,
USD 4.99 in the US. Review regional pricing before enabling other countries.
Add offer `trial-7-days`: new customer acquisition, **never had any subscription
in this app**, a seven-day free phase, then the weekly base plan. Activate the
base plan and offer. Google evaluates trial eligibility against the Play account;
this is not proof that a person has never used a different Google account.

The app selects the eligible trial returned by Play, falling back to the weekly
plan. Its confirmation uses Play's localized price, not a hardcoded dollar label.
The purchase sheet discloses automatic renewal and cancellation. Returning
subscribers do not receive trial language when Play returns only the base plan.

Enable Android Publisher API in the Cloud project. In Play Console, grant the
Cloud Run runtime service account access to this app with permissions to view
financial/order data and manage orders and subscriptions. Cloud IAM alone does
not grant Play Console permissions. No service-account keys belong in Android.

Set `BILLING_REQUIRED=true` on the server when testing the subscription gate.
Current protected routes: dashboard and profile workflows. Every future premium
API and background automation must also check `has_access(user)` before work.
Login, signup, subscription management and logout stay accessible.

## Verification and lifecycle

Purchases are verified with subscriptionsv2.get, bound to a server-generated
obfuscated app account ID, and acknowledged by the backend before access is stored.
The server checks product, base plan, state and expiry; it rejects cross-account
claims. Pending payments, holds and expired purchases do not grant access.
Cancellation retains access until paid expiry. Restore requires the original app
account and Google Play account. Keep the Django secret stable across deploys
because it derives the obfuscated account ID.

Stored entitlements refresh from Google on access after five minutes. That is
the maximum cached revocation delay. No push notification handler is configured
yet. Add authenticated Play RTDN processing before unattended premium agents run;
request-time checks alone do not stop an already running background task.

Test via Play internal testing with license testers: eligible trial, ineligible
returning account, purchase cancellation, pending payment, renewal, grace period,
hold, expiry, refund/revocation, reinstall/restore, wrong app account, and offline
verification. Unit tests mock Google; they do not replace these store tests.

Before public release, also complete real feature implementation, app icon,
privacy policy, in-app and web account deletion, Data Safety, store listing,
content rating and any account-specific Play testing requirements. The current
debug APK is not a publishable release or evidence of Play approval.

References:
- https://developer.android.com/google/play/billing/integrate
- https://support.google.com/googleplay/android-developer/answer/140504
- https://support.google.com/googleplay/android-developer/answer/12154973
