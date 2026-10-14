# JARVIS / Rubi Core

JARVIS (Rubi Core) is a lightweight, local-first personal AI assistant built for Windows. It is designed to act like a warm, supportive "big brother"—providing patient, straightforward explanations, step-by-step problem solving, and responsive local system actions while preserving privacy by running local LLMs via Ollama.

---

## Architecture & Confirmed Features

The features below have been confirmed through source code inspection and automated test suites:

- **Local-First LLM Inference:** Connects to a local [Ollama](https://ollama.com/) instance (`http://localhost:11434`). Supported and verified models include `llama3.2:3b` (primary) and `qwen2.5:3b` (fast/fallback), with context window management (`num_ctx: 2048`) and multi-threaded CPU execution.
- **Fast-Lane Deterministic Launcher:** Sub-second execution for system control commands (volume adjustment, mute/unmute, screen lock) bypassing LLM latency via `instant_commands.json`.
- **Intelligent Agentic Command Parser:** Parses conversational requests into structured actions (app launching, window manipulation, system diagnostics).
- **Two-Step Safety Confirmations:** High-impact system actions (such as shutdown and reboot) require explicit confirmation before execution.
- **Offline Neural TTS (Piper):** Integrated offline speech synthesis using [Piper](https://github.com/rhasspy/piper) with ONNX voice models (`en_US-lessac-medium`, `en_US-amy-medium`). Automatically falls back to the browser's Web Speech API when Piper binaries are not installed.
- **Optional Cloud AI Fallback (Google Gemini):** Supports `gemini-3.5-flash` with an automatic 3-strike circuit breaker that gracefully falls back to local models if cloud requests fail or time out.
- **Resilient Local Persistence:** Stores notes, reminders, sessions, memories, and activity logs locally with atomic write operations and automatic `.arc3.bak` backups.
- **Security & Origin Guard:** Enforces strict localhost/same-origin checks, CSRF validation, PBKDF2-HMAC-SHA256 PIN hashing with rate-limited lockout (5 failed attempts = 60s cooldown) for remote LAN access.

---

## System Requirements

- **Operating System:** Windows 10 or Windows 11 (uses Windows-specific Win32 APIs, VBS launcher, and PowerShell helpers).
- **Python:** Python 3.10 to 3.13.
- **Local LLM Engine:** [Ollama](https://ollama.com/) installed and running.
- **Supported Local Models:**
  - `llama3.2:3b` (default recommendation)
  - `qwen2.5:3b` (fast/fallback)
- **RAM / Hardware:** 8 GB RAM minimum recommended for running 3B parameter models on CPU.

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/jarvis-rubi-core.git
   cd jarvis-rubi-core
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize configuration:**
   Copy the example configuration to `settings.json`:
   ```powershell
   Copy-Item settings.example.json settings.json
   ```

5. **Pull a supported model in Ollama:**
   ```bash
   ollama pull llama3.2:3b
   ```

---

## Starting the Application

### Option A: Standard Console Launch (Interactive)
```powershell
python jarvis.py
```
If `gemini_api_key` is not configured in `settings.json` or your environment, you will be prompted to optionally enter it in the console (press Enter to skip and run fully offline).

### Option B: Silent Background Launcher (Windows)
Double-click `start_jarvis.vbs` or run:
```powershell
wscript start_jarvis.vbs
```
This launcher checks that Ollama is responding, starts the Flask backend silently via `pythonw.exe`, and opens the interface in an application window.

### Stopping the Server
Run the included stop script:
```powershell
.\stop_jarvis.bat
```
Or kill the process manually in PowerShell:
```powershell
Get-Process python*, pythonw* | Where-Object { $_.CommandLine -like "*jarvis.py*" } | Stop-Process
```

---

## Accessing the Interface

Once started, open your web browser to:
```
http://127.0.0.1:5000
```
- **Web UI:** PWA-ready dashboard featuring session chat, memory browser, notes editor, reminder manager, and voice controls.
- **Global Hotkey:** Run `pythonw jarvis_hotkey.py` to register `Ctrl + Shift + J` as a global hotkey to instantly focus the assistant. See [docs/README_HOTKEY.txt](docs/README_HOTKEY.txt).
- **LAN / Phone Access:** If Phone Mode is enabled in settings, access `http://<YOUR_LAN_IP>:5000` from a mobile browser on your local network. Enter your configured PIN (default in test environments: `1234` — Change this PIN after first run).

---

## Optional: Gemini Cloud Setup

Jarvis is fully functional offline with Ollama. If you wish to enable Google Gemini cloud fallback:

1. **Via Environment Variable (Recommended):**
   ```powershell
   $env:GEMINI_API_KEY = "your-gemini-api-key"
   python jarvis.py
   ```

2. **Via Startup Prompt:**
   Run `python jarvis.py` without an environment variable and enter the key when prompted. The key is kept in process memory and is **never written to disk**.

---

## Setting Up Piper Neural TTS (Optional)

Piper provides fast, high-quality offline voice synthesis. The binaries and neural voice models (>150 MB) are excluded from the repository.

To set up Piper locally:
1. Download the Windows Piper release archive `piper_windows_amd64.zip` from [Rhasspy Piper Releases](https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip).
2. Extract the archive into a `piper/` folder in the project root so that `piper/piper/piper.exe` exists.
3. Download the ONNX voice models and their `.json` metadata from [HuggingFace rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices):
   - `en_US-lessac-medium.onnx` and `en_US-lessac-medium.onnx.json`
   - `en_US-amy-medium.onnx` and `en_US-amy-medium.onnx.json`
4. Place the voice files into `piper/voices/`.
5. Restart Jarvis; `/speak/status` will automatically detect Piper. If Piper is not installed, speech synthesis will use the browser's built-in Web Speech API.

---

## Verified vs. Untested / Experimental Features

| Feature | Status | Evidence / Notes |
| :--- | :--- | :--- |
| **Ollama Local Chat & Streaming** | **Verified** | Verified with `llama3.2:3b` and `qwen2.5:3b`. |
| **Instant System Control (Volume/Mute)** | **Verified** | Tested via fast-lane handler with response times under 200ms. |
| **Session & Notes Persistence** | **Verified** | Tested with atomic file writes and backup rotation. |
| **PIN Authentication & Lockout** | **Verified** | Tested with 5 failed attempts triggering a 60-second lockout. |
| **Piper Neural Voice Synthesis** | **Verified** | Tested locally with `en_US-lessac-medium.onnx`. |
| **Webcam Vision Analysis** | *Untested* | Code exists in `jarvis.py` for `/vision` endpoints, but hardware camera capture requires manual verification with a physical webcam. |
| **Continuous Acoustic Wake Word** | *Untested* | Background listening while the browser is minimized requires active microphone permissions and is subject to browser power-saving restrictions. |
| **Playwright Web Browser Automation** | *Experimental* | Optional automation hooks exist in scratch scripts; not included in core `requirements.txt`. |

---

## Documentation & Historical Reports

Detailed architectural audits and historical QA reports are preserved in [`docs/reports/`](docs/reports/):
- [`docs/reports/TEST_REPORT.md`](docs/reports/TEST_REPORT.md) — Comprehensive functional test report across all API endpoints.
- [`docs/reports/AGENTIC_MODE_REPAIR_REPORT.md`](docs/reports/AGENTIC_MODE_REPAIR_REPORT.md) — Agentic mode command execution verification.
- [`docs/reports/STORAGE_CLEANUP_AUDIT.md`](docs/reports/STORAGE_CLEANUP_AUDIT.md) — Storage breakdown and file inventory audit.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
