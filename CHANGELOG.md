# Changelog

All notable changes to **JARVIS** will be documented in this file.

---

## [v4.0.0] - 2026-10-15

### 🚀 Major Upgrade: JARVIS 4.0 / RUBI CORE

This release represents a comprehensive architectural overhaul, upgrading JARVIS from a reactive local assistant into **RUBI CORE**—an offline-first, honest personal companion and Windows automation agent with bounded execution and strict safety gates.

#### 🛡️ Core Reliability & Safety Engine
- **Bounded Action Queue (`core/task_engine.py`):** Multi-step agentic tasks execute through a bounded background thread pool capped at 12 steps, featuring idempotency keys and duplicate request suppression.
- **Unified Risk-Based Gate:** All actions across text, voice, and automation tools are routed through a single deterministic safety evaluator:
  - *Safe Read / Informational:* Executed immediately without friction.
  - *Low Risk:* Safe process launching with verified running state.
  - *Medium Risk:* Interactive Yes/No confirmation prompt (e.g., closing non-system processes).
  - *High Risk:* Explicit typed confirmation required (e.g., system shutdown, destructive file actions).
  - *Prohibited:* Format drive, registry tampering, and arbitrary remote execution are permanently blocked.
- **Emergency Abort Hotkey:** Global `Ctrl+Shift+X` and immediate `/stop` REST endpoint to instantly terminate active agent tasks and abort streaming audio.

#### 🧠 Intelligent Reasoning & Honest Execution
- **Honest Disambiguation:** Ambiguous commands (e.g., "Open Ed") prompt for user clarification ("Did you mean Microsoft Edge?") rather than guessing or launching incorrect apps.
- **Bounded Local Search:** Folder searches (e.g., "open notes in desktop") search strictly within bounded user directories and report honest "file not found" results when absent.
- **Fast-Lane Deterministic Router:** Instant evaluation (< 200ms) for time queries, calculations, and local system controls without unnecessary LLM latency.

#### 📱 Mobile Client & Secure LAN Access
- **Cryptographic PIN Authentication:** Eliminated hardcoded default PINs. Initial setup generates a secure cryptographically random PIN stored with PBKDF2-HMAC-SHA256 hashing, per-IP rate limiting, and brute-force lockout.
- **Native Android Client:** Modern lightweight Android WebView wrapper (`mobile/android`) with auto-discovery, splash screen, and responsive touch controls.
- **SSL / TLS Provisioning (`scripts/setup_ssl.py`):** Built-in utility to generate self-signed certificates for encrypted local LAN access.

#### 🎙️ Offline Speech & Vision
- **Piper Neural TTS:** High-fidelity offline voice synthesis using `en_US-lessac-medium` and `en_US-amy-medium` ONNX models with zero external internet dependencies.
- **Conversational Barge-In & Follow-Up:** Voice interactions support natural interruption and maintain a 10-second active listening window for continuous follow-ups.
- **DPI-Aware Screen & Camera Vision:** Screen and camera capture support with optical character recognition (OCR) and routing to local vision models.

#### 🗄️ Persistence & System Observability
- **Atomic File Storage (`core/storage.py`):** Swapped direct file writes with atomic temporary-file-and-rename mechanics to prevent data corruption during power loss.
- **Missed Reminder Delivery:** Reminders scheduled while the machine was asleep or offline are automatically triggered upon wake.
- **Real-Time Telemetry (`/diagnostics`):** Live dashboard tracking CPU load, RAM allocation, disk capacity, task queue throughput, and Gemini circuit breaker health.
- **Lecturer Mode Cleaned:** Deprecated legacy Lecturer mode UI and background triggers while preserving historical user notes.

#### 🔍 Real-Device Verification (Oct 15, 2026)
- **Phone Top Bar:** Verified on real device.
- **Wake Word Then Command:** Verified on real device.
- **YouTube Song Play:** Verified on real device.

---

## [v3.0.0] - 2026-10-11

### Features
- Initial open-source release of JARVIS 3.0.
- Offline Ollama LLM integration (`llama3.2:3b`, `qwen2.5:3b`).
- Web-based interface on port 5000.
- Basic note taking, reminders, and Windows application launching.
