# JARVIS 4.0 / RUBI CORE

JARVIS 4.0 (RUBI CORE) is a local-first, privacy-respecting personal AI assistant and Windows automation companion. It acts as a supportive, reliable "Big Brother"—combining patient explanations, step-by-step problem solving, fast deterministic system controls, and safe bounded desktop actions powered by local Ollama LLMs and Windows automation.

---

## What's New in JARVIS 4.0 / RUBI CORE

- **Bounded Action Queue & Worker Engine (`core/queue.py`):** Bounded background worker thread pool executing multi-step tasks (capped at 12 steps) with idempotency keys and duplicate request suppression.
- **Unified Risk-Based Safety Gate (`core/safety.py`):** Every action across text, voice, and agentic tools passes through a single unified safety engine:
  - *Safe Read / Informational:* Auto-executed immediately.
  - *Low Risk:* Process launching with verified running state.
  - *Medium Risk:* Interactive Yes/No approval modal before execution.
  - *High Risk:* Explicit typed confirmation (e.g. system shutdown, file destruction).
  - *Prohibited:* Hard blocked commands (e.g. format drive, registry wipes).
- **Emergency Stop & Takeover:** Instant `Ctrl+Shift+X` emergency kill switch and UI "Stop" control to cleanly abort any running task or streaming audio.
- **Dynamic Secure Phone Access:** Zero hardcoded default PINs. A secure cryptographically random PIN is generated on initial boot if unconfigured, with PBKDF2-HMAC-SHA256 hashing and rate-limited lockout protection.
- **Offline-First Neural Voice & Continuous Turns:** Built-in Piper neural TTS (`en_US-lessac-medium`, `en_US-amy-medium`) with zero cloud dependencies, natural barge-in interruption, and 10-second follow-up listening window.
- **Screen & Camera Vision:** Real full-resolution screen capture, camera input, and optical character recognition (OCR) with intelligent routing to vision models.
- **Missed Reminder Delivery:** Overdue reminders scheduled while the system was offline or sleeping are delivered immediately upon wake.
- **Live System Diagnostics & Task Inspector:** `/diagnostics` endpoint tracking real-time CPU, RAM, disk availability, task queue metrics, and Gemini circuit breaker health.
- **Clean Modernized ARC / RUBI UI:** Distraction-free, responsive mobile/desktop interface with Dark, Light, and Cyan theme options. Lecturer mode has been permanently removed while preserving historical notes.

---

## Confirmed Architecture & Capabilities

| Capability | Engine / Implementation | Verification Evidence |
| :--- | :--- | :--- |
| **Local LLM Inference** | [Ollama](https://ollama.com/) (port 11434) | Tested with `llama3.2:3b` and `qwen2.5:3b`. |
| **Action Queue & Execution** | Python `core.queue.ActionQueue` | Tested via `test_stage2_core_reliability.py`. |
| **Unified Safety Gate** | Python `core.safety.SafetyEngine` | Tested via `test_stage6_safety_engine.py`. |
| **Fast-Lane Launcher** | Deterministic rule-based dispatcher | Verified < 200ms latency on system actions. |
| **Speech Output (TTS)** | [Piper](https://github.com/rhasspy/piper) ONNX models | Tested via `test_stage8_speech_output.py`. |
| **Phone / Mobile PWA** | Responsive layout + PIN Auth | Tested via `test_stage4_phone_client.py`. |
| **Vision & Screen OCR** | `PIL`, `pytesseract`, Vision models | Tested via `test_stage9_camera_screen_vision.py`. |
| **Cloud AI Fallback** | Google Gemini (`gemini-3.5-flash`) | Automatic 3-strike circuit breaker fallback. |
| **Atomic File Storage** | Temporary file swap + rename | Tested via `test_stage11_notes_memory_reminders.py`. |
| **Diagnostics & Monitoring**| `/diagnostics` REST endpoint | Tested via `test_stage13_diagnostics.py`. |

---

## System Requirements

- **Operating System:** Windows 10 or Windows 11 (uses Windows-specific Win32 APIs, VBS launcher, and PowerShell automation).
- **Python:** Python 3.10 to 3.13 (Python 3.12 recommended).
- **Local Model Engine:** [Ollama](https://ollama.com/) installed and running on `http://127.0.0.1:11434`.
- **Supported Local Models:**
  - `llama3.2:3b` (primary general intelligence)
  - `qwen2.5:3b` (high-speed fast lane & fallback)
  - `phi3:mini`, `mistral:7b` (supported)
- **RAM / Hardware:** 8 GB RAM minimum (16 GB recommended) for CPU-only inference. No dedicated GPU required.

---

## Installation & Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/rudreshbl04-cloud/jarvis.git
   cd jarvis
   ```

2. **Create and activate a Python virtual environment:**
   ```powershell
   py -3.12 -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Initialize configuration:**
   Copy the example settings template:
   ```powershell
   Copy-Item settings.example.json settings.json
   ```

5. **Ensure Ollama is running and models are installed:**
   ```powershell
   ollama pull llama3.2:3b
   ollama pull qwen2.5:3b
   ```

---

## Starting JARVIS

### Interactive Console
```powershell
py -3.12 jarvis.py
```

### Windows Background Launcher
Double-click `start_jarvis.vbs` or run in PowerShell:
```powershell
wscript start_jarvis.vbs
```

### Stopping the Assistant
```powershell
.\stop_jarvis.bat
```

---

## Accessing the Interface

- **Desktop Browser:** Open `http://127.0.0.1:5000`
- **Phone / Mobile Device:** Open `http://<YOUR_LAN_IP>:5000` on any mobile browser connected to the same Wi-Fi network. Enter your configured PIN when prompted.
- **System Diagnostics:** Visit `http://127.0.0.1:5000/diagnostics` for real-time CPU, RAM, disk, and task metrics.

---

## Running the Automated Test Suite

JARVIS 4.0 includes a comprehensive automated test suite and live end-to-end smoke verification:

```powershell
# 1. Run all stage architecture unit tests:
py -3.12 -m unittest discover -s tests -p "test_stage*.py"

# 2. Run full regression suite (with jarvis.py running on port 5000):
py -3.12 -m unittest discover -s tests -p "test_*.py"

# 3. Run live end-to-end smoke verification:
py -3.12 scratch/live_smoke_test.py
```

### Verified Test Status (v4.0.0)
- **Architecture Unit Tests:** Passed all Stage 2 through Stage 13 tests.
- **Live Smoke Test:** 19/19 checks passed cleanly (0 failures) covering PIN authentication, security headers, fast-lane dispatcher, honest disambiguation, two-step safety gate, bounded folder search, emergency abort, and atomic persistence.

---

## Known Limitations & Boundaries

1. **Windows Platform:** Process management, emergency hotkeys (`Ctrl+Shift+X`), and application launching rely on Windows APIs (`ctypes`, `win32gui`, PowerShell). Linux and macOS support is unverified.
2. **CPU-Only Model Latency:** Tested on standard Intel/AMD CPU laptops without dedicated GPU acceleration. Expected generation latency for `llama3.2:3b` is approximately 8–15 tokens/sec. Fast-lane deterministic commands respond in under 200ms.
3. **Microphone Access:** Audio capture requires single exclusive microphone ownership. Background conference apps holding exclusive audio locks may prevent wake-word detection.
4. **Local Model Dependency:** Offline operation requires the local [Ollama](https://ollama.com/) daemon running on port 11434 with models pre-downloaded.

---

## Contributing & Changelog

- See [CONTRIBUTING.md](CONTRIBUTING.md) for code of conduct and development workflows.
- See [CHANGELOG.md](CHANGELOG.md) for full version history and release notes.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

