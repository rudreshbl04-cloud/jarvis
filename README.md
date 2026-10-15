# JARVIS 4.0 / RUBI CORE

> Local-first personal AI assistant and Windows automation companion powered by offline Ollama models, bounded agentic workflows, and a deterministic safety gate.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-brightgreen.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-lightgrey.svg)](https://www.microsoft.com/windows)
[![Local LLM: Ollama](https://img.shields.io/badge/LLM-Ollama%20(Offline)-orange.svg)](https://ollama.com/)

JARVIS 4.0 (RUBI CORE) is an open-source, offline-first personal assistant designed to run locally on standard Windows hardware without dedicated GPU requirements. It combines deterministic fast-lane system commands (< 200ms), bounded multi-step desktop actions (capped at 12 steps), local neural voice synthesis via Piper, and honest disambiguation to prevent hallucinated actions.

---

## Verified Features & Architecture

| Capability | Implementation | Verification Status |
| :--- | :--- | :--- |
| **Local LLM Inference** | [Ollama](https://ollama.com/) (port 11434) | **Verified** with `llama3.2:3b` and `qwen2.5:3b`. |
| **Bounded Action Queue** | `core/task_engine.py` (Worker Pool) | **Verified** via `test_stage2_core_reliability.py`. |
| **Unified Safety Gate** | Deterministic Risk Evaluator | **Verified** via `test_stage6_safety_engine.py` & smoke suite. |
| **Fast-Lane Dispatcher** | Deterministic Regex & Rule Router | **Verified** (< 200ms response on time & math). |
| **Honest Disambiguation** | Disambiguation prompt logic | **Verified** (clarifies "Open Ed" without false launching). |
| **Emergency Abort** | `Ctrl+Shift+X` & `/stop` endpoint | **Verified** (cleanly stops running tasks & TTS). |
| **Offline Speech Output** | [Piper](https://github.com/rhasspy/piper) ONNX models | **Verified** via `test_stage8_speech_output.py`. |
| **Atomic File Storage** | Safe swap & rename (`core/storage.py`)| **Verified** via `test_stage11_notes_memory_reminders.py`. |
| **Real-Time Telemetry** | `/diagnostics` REST endpoint | **Verified** (reports RAM, CPU, disk, task throughput). |
| **Wake Word Detection** | Offline wake engine | *Note: Architecture verified in mock tests; not yet verified on real hardware microphone.* |
| **Android Phone Top Bar** | Android WebView app (`mobile/android`) | *Note: Gradle project builds cleanly; not yet verified on a real physical Android device.* |
| **YouTube Play Automation**| Browser launch & URL dispatcher | *Note: URL opening verified; in-page media control not yet verified on real device.* |

---

## System Requirements

- **Operating System:** Windows 10 or Windows 11 (uses Windows-specific Win32 APIs, VBS launcher, and PowerShell automation).
- **Python:** Python 3.10 to 3.13 (Python 3.12 recommended).
- **Local Model Engine:** [Ollama](https://ollama.com/) installed and running locally on `http://127.0.0.1:11434`.
- **Supported Local Models:**
  - `llama3.2:3b` (primary reasoning)
  - `qwen2.5:3b` (fast lane & tool classification)
- **Hardware:** Standard CPU laptop (8 GB RAM minimum, 16 GB recommended). No dedicated GPU required.

---

## Installation & Setup

### 1. Clone the repository
```powershell
git clone https://github.com/rudreshbl04-cloud/jarvis.git
cd jarvis
```

### 2. Set up Python virtual environment
```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initialize configuration
Copy the template configuration file:
```powershell
Copy-Item settings.example.json settings.json
```
*(On first boot without a settings file, JARVIS generates a secure cryptographically random PIN automatically.)*

### 4. Pull local models via Ollama
Ensure Ollama is running, then download the required lightweight models:
```powershell
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
```

---

## Running JARVIS

### Interactive Terminal Mode
```powershell
python jarvis.py
```
Open `http://127.0.0.1:5000` in your web browser.

### Silent Background Launcher
Double-click `start_jarvis.vbs` or run in PowerShell:
```powershell
wscript start_jarvis.vbs
```

### Stopping the Assistant
```powershell
.\stop_jarvis.bat
```

---

## Testing & Quality Assurance

JARVIS includes a full suite of automated unit tests and a live end-to-end smoke test harness:

```powershell
# 1. Run stage architecture unit tests:
py -3.12 -m unittest discover -s tests -p "test_stage*.py"

# 2. Run live smoke verification against running server (port 5000):
py -3.12 scratch/live_smoke_test.py
```

### Verified Test Evidence (v4.0.0 Release)
- **Stage Unit Tests:** 52/52 tests passed (0 failures).
- **Live Smoke Test:** 19/19 test assertions passed across 6 core flows:
  - Manifest & Security Headers: `PASS`
  - PIN Authentication Gate: `PASS`
  - System Telemetry & Models: `PASS`
  - Fast-Lane Dispatcher & Calculations: `PASS`
  - Honest Disambiguation ("Open Ed"): `PASS`
  - Two-Step Safety Gate ("Close calculator"): `PASS`
  - Bounded Folder Search: `PASS`
  - Emergency Abort (`/stop`): `PASS`
  - Atomic Persistence (Notes / Reminders / Memories): `PASS`

---

## Project Structure

```text
myagent/
├── core/                       # Core system architecture
│   ├── __init__.py
│   ├── storage.py              # Atomic JSON/text file persistence with backup recovery
│   └── task_engine.py          # Bounded ActionQueue worker pool (capped at 12 steps)
├── mobile/                     # Android client wrapper & PWA assets
│   └── android/                # Native Android WebView client (Java / Gradle)
├── scripts/                    # Automation, health check, and setup scripts
│   ├── setup_ssl.py            # Local self-signed certificate generator
│   ├── start_jarvis.ps1        # Dynamic PowerShell server launcher
│   └── run_three_rounds.py     # Three-round verification script
├── tests/                      # Architecture stage tests & integration suites
│   ├── test_stage2_core_reliability.py
│   ├── test_stage6_safety_engine.py
│   ├── test_stage8_speech_output.py
│   └── ...
├── jarvis.py                   # Main Flask application entry point (port 5000)
├── jarvis_hotkey.py            # Windows Win32 global hotkey daemon (Ctrl+Shift+J)
├── start_jarvis.vbs            # Silent Windows background launcher
├── stop_jarvis.bat             # Process termination script
├── settings.example.json       # Template configuration file
├── requirements.txt            # Python dependencies
├── CHANGELOG.md                # Version release history
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
└── README.md                   # Project documentation
```

---

## Known Limitations & Boundaries

1. **Windows Dependency:** System controls, process inspection, application launching, and the global emergency shortcut rely on Windows APIs (`win32gui`, `ctypes`, PowerShell).
2. **CPU Inference Latency:** Running on CPU produces typical generation speeds of 8–15 tokens/sec for `llama3.2:3b`. Fast-lane commands bypass the LLM and respond in under 200ms.
3. **Single Microphone Holder:** Audio input requires exclusive microphone access; running alongside aggressive third-party voice apps may inhibit wake word detection.
4. **Ollama Requirement:** Full offline conversational reasoning requires the Ollama background daemon on port 11434.

---

## Author & Acknowledgments

- **Author:** Rudresh B L ([@rudreshbl04-cloud](https://github.com/rudreshbl04-cloud))
- **Architecture:** JARVIS 4.0 / RUBI CORE
- **Underlying Open-Source Projects:** [Ollama](https://ollama.com/), [Piper](https://github.com/rhasspy/piper), [Flask](https://flask.palletsprojects.com/)

---

## License

This project is open-source software licensed under the [MIT License](LICENSE).
