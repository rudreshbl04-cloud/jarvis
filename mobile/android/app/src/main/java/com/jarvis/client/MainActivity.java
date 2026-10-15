package com.jarvis.client;

import android.Manifest;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.text.InputType;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.PermissionRequest;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {

    private static final String PREFS_NAME = "JarvisClientPrefs";
    private static final String KEY_SERVER_URL = "server_url";
    private static final int PERMISSION_REQ_CODE = 101;

    private WebView webView;
    private ProgressBar progressBar;
    private SharedPreferences prefs;
    private PermissionRequest pendingPermissionRequest;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        webView = findViewById(R.id.webView);
        progressBar = findViewById(R.id.progressBar);

        setupWebView();
        checkAndRequestAppPermissions();

        String serverUrl = prefs.getString(KEY_SERVER_URL, "");
        if (serverUrl.isEmpty()) {
            promptServerUrl();
        } else {
            loadServerUrl(serverUrl);
        }
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);

        // Mobile user agent with Jarvis wrapper tag
        String customUA = settings.getUserAgentString() + " JarvisAndroidWrapper/4.0";
        settings.setUserAgentString(customUA);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                progressBar.setVisibility(View.VISIBLE);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                progressBar.setVisibility(View.GONE);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request.isForMainFrame()) {
                    progressBar.setVisibility(View.GONE);
                    Toast.makeText(MainActivity.this, "Cannot connect to Laptop Jarvis. Verify Wi-Fi and that Jarvis is running.", Toast.LENGTH_LONG).show();
                }
            }

            @Override
            public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                // For development with self-signed SSL certificate on LAN
                new AlertDialog.Builder(MainActivity.this)
                        .setTitle("SSL Certificate Notice")
                        .setMessage("A self-signed certificate was detected on your local Jarvis server. Proceed to connect?")
                        .setPositiveButton("Proceed", (dialog, which) -> handler.proceed())
                        .setNegativeButton("Cancel", (dialog, which) -> handler.cancel())
                        .show();
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                pendingPermissionRequest = request;
                runOnUiThread(() -> {
                    String[] requestedResources = request.getResources();
                    for (String r : requestedResources) {
                        if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(r) ||
                            PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r)) {
                            request.grant(requestedResources);
                            return;
                        }
                    }
                    request.deny();
                });
            }
        });
    }

    private void checkAndRequestAppPermissions() {
        String[] permissions = {
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO
        };
        boolean needRequest = false;
        for (String p : permissions) {
            if (ContextCompat.checkSelfPermission(this, p) != PackageManager.PERMISSION_GRANTED) {
                needRequest = true;
                break;
            }
        }
        if (needRequest) {
            ActivityCompat.requestPermissions(this, permissions, PERMISSION_REQ_CODE);
        }
    }

    private void promptServerUrl() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(R.string.server_prompt);
        builder.setMessage("Enter the IP or address shown on your laptop screen (e.g., http://192.168.1.15:5000):");

        final EditText input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        input.setHint("http://192.168.x.x:5000");
        builder.setView(input);

        builder.setPositiveButton(R.string.connect, (dialog, which) -> {
            String url = input.getText().toString().trim();
            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "http://" + url;
            }
            if (!url.contains(":5000") && !url.contains(":443") && !url.contains(":80")) {
                url = url + ":5000";
            }
            prefs.edit().putString(KEY_SERVER_URL, url).apply();
            loadServerUrl(url);
        });

        builder.setCancelable(false);
        builder.show();
    }

    private void loadServerUrl(String url) {
        webView.loadUrl(url);
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
}
