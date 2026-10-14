==============================================================================
JARVIS GLOBAL HOTKEY INSTRUCTIONS (Ctrl + Shift + J)
==============================================================================

WHAT IT DOES:
Pressing Ctrl + Shift + J anywhere in Windows opens or focuses your Jarvis
assistant (http://127.0.0.1:5000) in your default web browser.

HOW TO ENABLE:
1. Automatic: The hotkey helper is started automatically by start_jarvis.vbs
   in the background when Jarvis starts.
2. Manual background run:
   Run in PowerShell / Command Prompt:
   pythonw C:\Users\Dell\myagent\jarvis_hotkey.py

HOW TO DISABLE:
1. Open Task Manager, locate "Python" or "pythonw.exe" running jarvis_hotkey.py
   and end task.
2. Or in PowerShell:
   Get-Process pythonw | Stop-Process

IMPLEMENTATION DETAILS:
- Uses the standard Windows Win32 API (RegisterHotKey / UnregisterHotKey)
  via ctypes.
- Zero external pip package dependencies.
- Consumes negligible system resources (~10 MB RAM, 0% CPU).
==============================================================================
