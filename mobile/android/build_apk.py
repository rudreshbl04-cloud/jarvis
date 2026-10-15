"""
Build & Packaging Utility for JARVIS 4.0 Android Client.
Verifies project integrity, checks local toolchain (Java, Gradle, Android SDK),
and executes or guides debug APK compilation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

ANDROID_DIR = Path(__file__).resolve().parent

def check_file_structure():
    print("[1/4] Verifying Android client project structure...")
    required_files = [
        ANDROID_DIR / "settings.gradle",
        ANDROID_DIR / "build.gradle",
        ANDROID_DIR / "app" / "build.gradle",
        ANDROID_DIR / "app" / "src" / "main" / "AndroidManifest.xml",
        ANDROID_DIR / "app" / "src" / "main" / "java" / "com" / "jarvis" / "client" / "MainActivity.java",
        ANDROID_DIR / "app" / "src" / "main" / "res" / "layout" / "activity_main.xml",
        ANDROID_DIR / "app" / "src" / "main" / "res" / "values" / "strings.xml",
        ANDROID_DIR / "app" / "src" / "main" / "res" / "values" / "colors.xml",
        ANDROID_DIR / "app" / "src" / "main" / "res" / "values" / "themes.xml",
    ]
    all_ok = True
    for f in required_files:
        if not f.exists():
            print(f"  [MISSING] {f.relative_to(ANDROID_DIR)}")
            all_ok = False
        else:
            print(f"  [OK] {f.relative_to(ANDROID_DIR)}")
    return all_ok

def check_toolchain():
    print("\n[2/4] Checking build toolchain...")
    # Check Java
    java_ok = False
    try:
        res = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if res.returncode == 0:
            print("  [OK] Java runtime detected.")
            java_ok = True
        else:
            print("  [WARN] Java returned non-zero code.")
    except Exception:
        print("  [WARN] Java (JDK 17+) not found on PATH.")

    # Check Gradle
    gradle_ok = False
    try:
        res = subprocess.run(["gradle", "-v"], capture_output=True, text=True)
        if res.returncode == 0:
            print("  [OK] Gradle build system detected.")
            gradle_ok = True
        else:
            print("  [WARN] Gradle returned non-zero code.")
    except Exception:
        print("  [INFO] System Gradle not installed on PATH.")

    # Check Android SDK
    sdk_ok = False
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home and Path(android_home).exists():
        print(f"  [OK] Android SDK found at: {android_home}")
        sdk_ok = True
    else:
        print("  [INFO] ANDROID_HOME environment variable not configured.")

    return java_ok, gradle_ok, sdk_ok

def build_or_guide(java_ok, gradle_ok, sdk_ok):
    print("\n[3/4] Build status and actions...")
    if gradle_ok and sdk_ok:
        print("  Attempting debug APK build with Gradle...")
        cmd = ["gradle", "assembleDebug"]
        try:
            res = subprocess.run(cmd, cwd=str(ANDROID_DIR), capture_output=True, text=True)
            if res.returncode == 0:
                print("  [SUCCESS] Debug APK built successfully!")
                return True
            else:
                print(f"  [FAIL] Gradle build failed:\n{res.stderr}")
        except Exception as e:
            print(f"  [ERROR] Execution failed: {e}")
    else:
        print("  System toolchain note:")
        print("  - To build a native debug APK on this Windows host, install Android Studio or the Android Command-line Tools (JDK 17+ and Android SDK platform 34).")
        print("  - Once installed, run: 'gradle assembleDebug' inside this folder.")
        print("  - Alternatively, users can open 'mobile/android' directly in Android Studio and click 'Build > Build APK(s)'.")
    return False

def show_deployment_summary():
    print("\n[4/4] Client deployment guidance:")
    print("=" * 60)
    print("  ANDROID USERS:")
    print("  1. Native Wrapper: Open 'mobile/android' in Android Studio, click 'Run' or 'Build APK'.")
    print("  2. Instant PWA: Open Chrome on Android, browse to your laptop's LAN URL (e.g. http://192.168.x.x:5000), tap Menu > 'Install app'.")
    print("\n  IPHONE (iOS) USERS:")
    print("  1. iOS devices do NOT run APK files. Never attempt to install an APK on iOS.")
    print("  2. Open Safari on iPhone, browse to http://<laptop-ip>:5000, tap Share (box with arrow), and tap 'Add to Home Screen'.")
    print("\n  IMPORTANT SAFETY & RUNTIME RULES:")
    print("  - Laptop must be ON, awake, and Jarvis running on port 5000.")
    print("  - Both phone and laptop must be on the same local Wi-Fi / Hotspot.")
    print("  - APK signing keys / keystores must NEVER be committed to Git.")
    print("=" * 60)

if __name__ == "__main__":
    struct_ok = check_file_structure()
    if not struct_ok:
        print("[FAIL] Missing required Android files.")
        sys.exit(1)
    j_ok, g_ok, s_ok = check_toolchain()
    build_or_guide(j_ok, g_ok, s_ok)
    show_deployment_summary()
    print("\n[VERIFIED] Android client project verification complete.")
