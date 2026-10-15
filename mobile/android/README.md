# JARVIS 4.0 / RUBI CORE — Android & Mobile Client

This directory contains the lightweight Android client wrapper for **JARVIS 4.0 / RUBI CORE**.

---

## 1. Architecture

The Android wrapper is a thin client (WebView with hardware WebChromeClient bridge). It connects to your laptop's Jarvis server over local Wi-Fi or hotspot.

- **Main Server:** Runs on your Windows laptop at `http://<laptop-ip>:5000`.
- **Phone Role:** User interface for chat, voice input (mic), camera vision, and quick actions.
- **Data & Models:** All intelligence, Ollama models, sessions, notes, and memories reside entirely on your laptop.

---

## 2. Android Installation

### Option A: Progressive Web App (PWA) — Fastest & Easiest
1. Connect your Android phone to the same Wi-Fi or laptop mobile hotspot.
2. Open **Google Chrome** on your phone.
3. Browse to the address shown in your laptop Jarvis header (e.g. `http://192.168.1.5:5000`).
4. Tap the three-dot menu `⋮` and select **"Install app"** or **"Add to Home screen"**.
5. An icon titled **Jarvis** appears on your home screen and operates full-screen like a native app.

### Option B: Build & Install Android APK
1. Open this directory (`mobile/android`) in **Android Studio**.
2. Select **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
3. Locate the output APK in `mobile/android/app/build/outputs/apk/debug/app-debug.apk`.
4. Transfer to your phone and install.
   - *Security notice:* When installing a debug APK outside the Play Store, Android will display a "Play Protect / Unknown app" prompt. This is expected for self-built applications.
   - *Signing rules:* Debug builds use the default Android debug key. Never commit private production signing keystores or passwords to Git.

---

## 3. iPhone (iOS) Users

> [!IMPORTANT]
> iOS devices **cannot** run `.apk` files. Do not attempt to install an APK on an iPhone or iPad.

To use Jarvis on an iPhone:
1. Open **Safari** on your iPhone.
2. Navigate to `http://<laptop-ip>:5000`.
3. Tap the **Share** button (box with upward arrow).
4. Scroll down and tap **"Add to Home Screen"**.
5. Jarvis will launch as a standalone web application.

---

## 4. Hardware & Connection Requirements

1. **Laptop Awake:** The laptop running Jarvis must be powered on and awake. If the laptop is shut down or sleeping, the phone will display **Laptop Unavailable**.
2. **Same Network:** Both laptop and phone must be on the same local network (Wi-Fi or laptop hotspot).
3. **No Public Port Forwarding:** Do not forward port 5000 to the public internet without an authenticated VPN (such as Tailscale or WireGuard).
4. **Microphone & Camera Permissions:** Browsers restrict audio/video recording to secure origins. For LAN access, enable HTTPS using `scripts/setup_ssl.py` or allow local device permissions in browser site settings.
