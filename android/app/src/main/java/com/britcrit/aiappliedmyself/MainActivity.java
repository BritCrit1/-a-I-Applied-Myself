package com.britcrit.aiappliedmyself;

import androidx.activity.ComponentActivity;
import androidx.activity.OnBackPressedCallback;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.*;
import android.widget.*;
import com.android.billingclient.api.*;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Collections;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends ComponentActivity implements PurchasesUpdatedListener {
    private WebView web;
    private BillingClient billing;
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private ValueCallback<Uri[]> fileCallback;
    private static final String PRODUCT = "premium";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setOnApplyWindowInsetsListener((v, insets) -> {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(android.view.WindowInsets.Type.systemBars() | android.view.WindowInsets.Type.ime());
                v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            } else {
                v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(), insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        Button subscription = new Button(this);
        subscription.setText("Subscription");
        subscription.setOnClickListener(v -> web.loadUrl(BuildConfig.APP_URL + "/billing/"));
        layout.addView(subscription);
        web = new WebView(this);
        layout.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(layout);
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() {
                if (web.canGoBack()) web.goBack(); else finish();
            }
        });
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!trusted(uri)) {
                    if (request.isForMainFrame() && ("https".equals(uri.getScheme()) || "mailto".equals(uri.getScheme()))) {
                        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
                        catch (android.content.ActivityNotFoundException e) { message("No app can open this link."); }
                    }
                    return true;
                }
                if (request.isForMainFrame() && "/billing/subscribe-native/".equals(uri.getPath())) { subscribe(); return true; }
                if (request.isForMainFrame() && "/billing/restore-native/".equals(uri.getPath())) { restore(); return true; }
                return false;
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) message("Cannot load the app. Check your connection and reopen the app.");
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"});
                try { startActivityForResult(intent, 100); }
                catch (android.content.ActivityNotFoundException e) { fileCallback.onReceiveValue(null); fileCallback = null; }
                return true;
            }
        });
        billing = BillingClient.newBuilder(this).setListener(this)
            .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
            .enableAutoServiceReconnection().build();
        billing.startConnection(new BillingClientStateListener() {
            @Override public void onBillingSetupFinished(BillingResult result) { if (result.getResponseCode() == 0) restore(false); }
            @Override public void onBillingServiceDisconnected() { }
        });
        if (BuildConfig.APP_URL.endsWith(".invalid")) {
            TextView setup = new TextView(this);
            setup.setText("AIAMS\n\nPreview build. The production server address has not been configured.");
            setup.setPadding(32, 32, 32, 32);
            setContentView(setup);
        } else { web.loadUrl(BuildConfig.APP_URL + "/dashboard/"); }
    }

    private boolean trusted(Uri uri) {
        Uri base = Uri.parse(BuildConfig.APP_URL);
        return "https".equals(uri.getScheme()) && base.getAuthority().equals(uri.getAuthority());
    }

    private JSONObject request(String path, JSONObject body, String csrf) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(BuildConfig.APP_URL + path).openConnection();
        try {
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(20000);
            String cookies = CookieManager.getInstance().getCookie(BuildConfig.APP_URL);
            if (cookies != null) connection.setRequestProperty("Cookie", cookies);
            if (body != null) {
                connection.setRequestMethod("POST");
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setRequestProperty("X-CSRFToken", csrf);
                connection.setRequestProperty("Referer", BuildConfig.APP_URL + "/billing/");
                try (var output = connection.getOutputStream()) { output.write(body.toString().getBytes(StandardCharsets.UTF_8)); }
            }
            for (var header : connection.getHeaderFields().entrySet()) {
                if ("Set-Cookie".equalsIgnoreCase(header.getKey())) {
                    for (String cookie : header.getValue()) CookieManager.getInstance().setCookie(BuildConfig.APP_URL, cookie);
                }
            }
            int status = connection.getResponseCode();
            if (status == 302 || status == 401) throw new Exception("Sign in to the app first, then restore purchases or subscribe.");
            if (status != 200) throw new Exception("Purchase verification failed. Check your account and retry Restore purchases.");
            try (var input = connection.getInputStream(); var output = new java.io.ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096];
                int count;
                while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
                return new JSONObject(output.toString(StandardCharsets.UTF_8.name()));
            }
        } finally { connection.disconnect(); }
    }

    private void subscribe() {
        if (!billing.isReady()) { message("Google Play is connecting. Please try again."); return; }
        network.execute(() -> {
            try {
                String account = request("/billing/config/", null, null).getString("accountId");
                billing.queryProductDetailsAsync(QueryProductDetailsParams.newBuilder().setProductList(Collections.singletonList(
                    QueryProductDetailsParams.Product.newBuilder().setProductId(PRODUCT).setProductType(BillingClient.ProductType.SUBS).build()
                )).build(), (result, details) -> runOnUiThread(() -> {
                    if (result.getResponseCode() != 0 || details.getProductDetailsList().isEmpty()) { message("Subscription unavailable. Please try again later."); return; }
                    ProductDetails product = details.getProductDetailsList().get(0);
                    var offers = product.getSubscriptionOfferDetails();
                    ProductDetails.SubscriptionOfferDetails chosen = null;
                    if (offers != null) {
                        for (var offer : offers) {
                            if (!"weekly".equals(offer.getBasePlanId())) continue;
                            if (offer.getOfferId() == null && chosen == null) chosen = offer;
                            if ("trial-7-days".equals(offer.getOfferId())) { chosen = offer; break; }
                        }
                    }
                    if (chosen == null) { message("Weekly subscription is unavailable."); return; }
                    var selected = chosen;
                    StringBuilder terms = new StringBuilder();
                    for (var phase : chosen.getPricingPhases().getPricingPhaseList()) {
                        if (phase.getPriceAmountMicros() == 0 && "P7D".equals(phase.getBillingPeriod())) terms.append("7 days free, then ");
                        else if ("P1W".equals(phase.getBillingPeriod())) terms.append(phase.getFormattedPrice()).append(" per week. ");
                        else { message("Unexpected plan terms. Please try later."); return; }
                    }
                    terms.append("Automatically renews until canceled. Cancel in Google Play before the trial ends to avoid a charge.");
                    new AlertDialog.Builder(this).setTitle("Premium subscription").setMessage(terms)
                        .setNegativeButton("Cancel", null).setPositiveButton("Continue", (dialog, which) -> {
                            BillingResult launched = billing.launchBillingFlow(this, BillingFlowParams.newBuilder()
                                .setObfuscatedAccountId(account).setProductDetailsParamsList(Collections.singletonList(
                                    BillingFlowParams.ProductDetailsParams.newBuilder().setProductDetails(product).setOfferToken(selected.getOfferToken()).build()
                                )).build());
                            if (launched.getResponseCode() != 0) message("Could not start purchase. Please retry.");
                        }).show();
                }));
            } catch (Exception e) { message(e.getMessage()); }
        });
    }

    private void restore() { restore(true); }
    private void restore(boolean reportEmpty) {
        if (!billing.isReady()) { if (reportEmpty) message("Google Play is connecting. Please retry."); return; }
        billing.queryPurchasesAsync(QueryPurchasesParams.newBuilder().setProductType(BillingClient.ProductType.SUBS).build(), (result, purchases) -> {
            if (result.getResponseCode() != 0) { if (reportEmpty) message("Unable to restore purchases. Please retry."); return; }
            if (purchases.isEmpty() && reportEmpty) message("No subscription found for this Google Play account.");
            for (Purchase purchase : purchases) process(purchase);
        });
    }
    @Override public void onPurchasesUpdated(BillingResult result, List<Purchase> purchases) {
        if (result.getResponseCode() == 0 && purchases != null) for (Purchase purchase : purchases) process(purchase);
        else if (result.getResponseCode() != BillingClient.BillingResponseCode.USER_CANCELED) message("Purchase did not complete. Please retry or restore purchases.");
    }
    private void process(Purchase purchase) {
        if (!purchase.getProducts().contains(PRODUCT)) return;
        if (purchase.getPurchaseState() != Purchase.PurchaseState.PURCHASED) { message("Payment is pending. Access starts after Google confirms it."); return; }
        network.execute(() -> {
            try {
                JSONObject config = request("/billing/config/", null, null);
                JSONObject result = request("/billing/verify/", new JSONObject().put("purchaseToken", purchase.getPurchaseToken()), config.getString("csrfToken"));
                runOnUiThread(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    if (result.optBoolean("active")) {
                        // Restoring on resume must not discard an in-progress profile form.
                        String current = web.getUrl();
                        if (current != null && Uri.parse(current).getPath().startsWith("/billing/")) {
                            web.loadUrl(BuildConfig.APP_URL + "/dashboard/");
                        }
                    } else message("This subscription is not currently active.");
                });
            } catch (Exception e) { message(e.getMessage()); }
        });
    }
    private void message(String text) {
        runOnUiThread(() -> { if (!isFinishing() && !isDestroyed()) new AlertDialog.Builder(this).setMessage(text).setPositiveButton("OK", null).show(); });
    }
    @Override protected void onResume() { super.onResume(); if (billing != null && billing.isReady()) restore(false); }
    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 100 && fileCallback != null) {
            fileCallback.onReceiveValue(resultCode == RESULT_OK && data != null && data.getData() != null ? new Uri[]{data.getData()} : null);
            fileCallback = null;
        }
    }
    @Override protected void onDestroy() {
        if (fileCallback != null) fileCallback.onReceiveValue(null);
        billing.endConnection(); network.shutdownNow(); web.destroy(); super.onDestroy();
    }
}
