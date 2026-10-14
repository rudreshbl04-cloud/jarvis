"""
Installer for JARVIS ARC 3.0 Desktop & Start Menu Shortcuts.
Ensures the user has direct, 1-click access to the fully updated JARVIS ARC 3.0 from:
1. Desktop (OneDrive Desktop & Local Desktop)
2. Windows Start Menu (Programs)
3. Windows Startup Folder
Replaces any obsolete shortcuts pointing to older directories.
"""

import os
import sys
from pathlib import Path
import win32com.client

def install():
    shell = win32com.client.Dispatch("WScript.Shell")
    
    workspace = Path(__file__).resolve().parent.parent
    vbs_launcher = workspace / "start_jarvis.vbs"
    ico_path = workspace / "jarvis.ico"
    wscript_exe = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "wscript.exe")
    
    if not vbs_launcher.exists():
        print(f"Error: Launcher not found at {vbs_launcher}")
        return False
        
    home = Path.home()
    appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
    desktop_onedrive = home / "OneDrive" / "Desktop"
    desktop_local = home / "Desktop"
    start_menu = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    startup_folder = start_menu / "Startup"
    
    shortcuts = [
        # New primary shortcuts
        desktop_onedrive / "JARVIS ARC 3.0.lnk",
        desktop_local / "JARVIS ARC 3.0.lnk",
        start_menu / "JARVIS ARC 3.0.lnk",
        startup_folder / "Jarvis.lnk",
        
        # Override old/legacy shortcuts to prevent running stale versions
        desktop_onedrive / "JARVIS AI.lnk",
        desktop_local / "JARVIS AI.lnk"
    ]
    
    installed_count = 0
    for sc_path in shortcuts:
        parent_dir = sc_path.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                continue
                
        try:
            sc = shell.CreateShortcut(str(sc_path))
            sc.TargetPath = wscript_exe
            sc.Arguments = f'"{vbs_launcher}"'
            sc.WorkingDirectory = str(workspace)
            if ico_path.exists():
                sc.IconLocation = f"{ico_path},0"
            sc.Description = "JARVIS ARC 3.0 / RUBI CORE (Fully Updated)"
            sc.Save()
            installed_count += 1
            print(f"[OK] Installed shortcut: {sc_path}")
        except Exception as e:
            print(f"[FAIL] Could not create {sc_path}: {e}")
            
    print(f"\nSuccessfully installed {installed_count} shortcuts for JARVIS ARC 3.0.")
    return True

if __name__ == "__main__":
    install()
