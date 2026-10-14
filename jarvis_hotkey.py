"""
J.A.R.V.I.S Global Hotkey Helper (Ctrl + Shift + J)
Opens or focuses Jarvis (http://127.0.0.1:5000) from anywhere in Windows.
Pure Win32 API implementation via ctypes (no pip packages needed).
"""
import ctypes
import ctypes.wintypes
import webbrowser
import sys
import os

user32 = ctypes.windll.user32
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_J = 0x4A
HOTKEY_ID = 101
TARGET_URL = "http://127.0.0.1:5000"

def run_hotkey_listener():
    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_J):
        print(f"Error: Could not register hotkey Ctrl+Shift+J. Error code: {ctypes.GetLastError()}")
        sys.exit(1)

    print("Jarvis Global Hotkey active: Press Ctrl + Shift + J to open Jarvis in browser.")
    sys.stdout.flush()

    msg = ctypes.wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312:  # WM_HOTKEY
                if msg.wParam == HOTKEY_ID:
                    webbrowser.open(TARGET_URL)
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        user32.UnregisterHotKey(None, HOTKEY_ID)

if __name__ == "__main__":
    run_hotkey_listener()
