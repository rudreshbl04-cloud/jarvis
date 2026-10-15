# Contributing to JARVIS / RUBI CORE

Thank you for your interest in contributing to JARVIS / RUBI CORE! We welcome bug reports, documentation improvements, and pull requests that adhere to our local-first, privacy-respecting principles.

---

## Code of Conduct & Core Philosophy

JARVIS is designed as an offline-first, honest, and safe personal AI assistant. All contributions should align with these core tenets:
1. **Offline & Privacy First:** Core functionality must operate fully locally using local Ollama models and local TTS without requiring external cloud services or telemetry.
2. **Deterministic Safety:** Destructive actions (process termination, file modifications, system commands) must always traverse the unified risk gate with explicit confirmation.
3. **No Hallucinated Tool Actions:** The assistant must never invent actions or pretend to open/execute programs that do not exist.
4. **Honest Disambiguation:** Ambiguous system requests (e.g., "Open Ed") must prompt for clarification rather than executing guessed actions.

---

## Development Workflow

### 1. Environment Setup
- **Operating System:** Windows 10 or Windows 11.
- **Python Version:** Python 3.10 to 3.13 (Python 3.12 recommended).
- **Local LLM Engine:** [Ollama](https://ollama.com/) running on `http://127.0.0.1:11434`.

```powershell
# Clone the repository
git clone https://github.com/rudreshbl04-cloud/jarvis.git
cd jarvis

# Create and activate a virtual environment
py -3.12 -m venv venv
.\venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Running Locally
```powershell
# Start the server interactively
python jarvis.py
```
Visit `http://127.0.0.1:5000` in your web browser.

---

## Testing Guidelines

Before opening a pull request, ensure all unit tests pass cleanly:

```powershell
# Run the stage architecture test suite
py -3.12 -m unittest discover -s tests -p "test_stage*.py"

# Run the full regression test suite (with server running)
py -3.12 -m unittest discover -s tests -p "test_*.py"
```

---

## Submitting Pull Requests

1. Fork the repository and create your feature branch from `main`:
   ```powershell
   git checkout -b feature/my-feature
   ```
2. Commit your changes with clear, descriptive commit messages.
3. Ensure no personal credentials, private data files (`sessions.json`, `notes.txt`, `settings.json`), or build outputs are staged.
4. Push to your fork and submit a Pull Request describing your changes, test evidence, and motivation.
