import os
import sys
import shutil
import zipfile
import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 1. New Pre-cleanup Backup Targets
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

shutil.copy2(os.path.join(PROJECT_ROOT, "jarvis.py"), os.path.join(BACKUP_DIR, f"jarvis_pre_cleanup_{TIMESTAMP}.py"))
shutil.copy2(os.path.join(PROJECT_ROOT, "settings.json"), os.path.join(BACKUP_DIR, f"settings_pre_cleanup_{TIMESTAMP}.json"))
print(f"[BACKUP] Created jarvis_pre_cleanup_{TIMESTAMP}.py and settings_pre_cleanup_{TIMESTAMP}.json")

# Define Tier 1 exact candidate files to delete
# (DO NOT touch review list items or protected items)

# A. Leftover zip archive
tier1_files = [
    os.path.join(PROJECT_ROOT, "piper", "piper_windows_amd64.zip")
]

# B. Root backup files
root_backups = [
    "jarvis_backup_20261011_1626.py",
    "jarvis_backup_20261011_173325.py",
    "jarvis_backup_20261011_181054.py",
    "jarvis_backup_20261011_arc3.py",
    "activity.json.arc3.bak",
    "activity.json.arc3_bak",
    "activity.json.pre-arc.bak",
    "benchmark_results.json.arc3.bak",
    "documents.json.arc3.bak",
    "memories.json.arc3.bak",
    "notes.txt.arc3.bak",
    "reminders.json.arc3.bak",
    "reminders.json.arc3_bak",
    "reminders.json.pre-arc.bak",
    "sessions.json.arc3.bak",
    "sessions.json.arc3_bak",
    "sessions.json.pre-arc.bak",
    "settings.json.arc3.bak",
]
for rb in root_backups:
    p = os.path.join(PROJECT_ROOT, rb)
    if os.path.exists(p):
        tier1_files.append(p)

# C. Older backups in backups/
# Explicitly PROTECT the 2 newest sets + today's wake repair + pre_cleanup
protected_backups = {
    "jarvis_wake_repair_20261014.py",
    "jarvis_agentic_final_20261013_230500.py",
    "settings_agentic_final_20261013_230500.json",
    "jarvis_agentic_repair_20261013_221600.py",
    "settings_agentic_repair_20261013_221600.json",
    f"jarvis_pre_cleanup_{TIMESTAMP}.py",
    f"settings_pre_cleanup_{TIMESTAMP}.json"
}

for fname in os.listdir(BACKUP_DIR):
    if fname in protected_backups:
        continue
    fpath = os.path.join(BACKUP_DIR, fname)
    if os.path.isfile(fpath) and not fname.endswith(".zip"):
        tier1_files.append(fpath)

# D. Temporary scratch dumps & non-test files
scratch_temp_files = [
    os.path.join(PROJECT_ROOT, "scratch", "candidate_jarvis.py"),
    os.path.join(PROJECT_ROOT, "scratch", "temp_embedded.js"),
    os.path.join(PROJECT_ROOT, "scratch", "temp_js_check.js"),
    os.path.join(PROJECT_ROOT, "scratch", "extracted-rendered.js"),
    os.path.join(PROJECT_ROOT, "scratch", "master_run.log")
]
for st in scratch_temp_files:
    if os.path.exists(st):
        tier1_files.append(st)

# E. Verification logs in artifacts/verification
art_ver_dir = os.path.join(PROJECT_ROOT, "artifacts", "verification")
if os.path.exists(art_ver_dir):
    for f in os.listdir(art_ver_dir):
        if f.endswith(".log") or f == "extracted-rendered.js":
            tier1_files.append(os.path.join(art_ver_dir, f))

# Filter tier1_files to only those that currently exist
existing_tier1 = [f for f in tier1_files if os.path.exists(f)]

# 2. Archive all candidate files into a rollback zip before deletion
archive_zip_path = os.path.join(BACKUP_DIR, f"tier1_pre_cleanup_archive_{TIMESTAMP}.zip")
print(f"[ARCHIVE] Archiving {len(existing_tier1)} candidate files to {archive_zip_path}...")
with zipfile.ZipFile(archive_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in existing_tier1:
        arcname = os.path.relpath(f, PROJECT_ROOT)
        zf.write(f, arcname)
print(f"[ARCHIVE] Archive created successfully ({os.path.getsize(archive_zip_path)} bytes)")

# 3. Perform Deletion of Tier 1 candidate files
deleted_count = 0
deleted_bytes = 0
deleted_list = []

for f in existing_tier1:
    size = os.path.getsize(f)
    rel = os.path.relpath(f, PROJECT_ROOT)
    try:
        os.remove(f)
        deleted_count += 1
        deleted_bytes += size
        deleted_list.append((rel, size))
    except Exception as e:
        print(f"[ERROR] Failed to remove {rel}: {e}")

# 4. Clean Python bytecode caches (__pycache__) in root, scratch, and scripts
pycache_dirs = [
    os.path.join(PROJECT_ROOT, "__pycache__"),
    os.path.join(PROJECT_ROOT, "scratch", "__pycache__"),
    os.path.join(PROJECT_ROOT, "scripts", "__pycache__")
]

pyc_deleted = 0
pyc_bytes = 0

for pydir in pycache_dirs:
    if os.path.exists(pydir):
        for root, dirs, files in os.walk(pydir):
            for file in files:
                fpath = os.path.join(root, file)
                sz = os.path.getsize(fpath)
                try:
                    os.remove(fpath)
                    pyc_deleted += 1
                    pyc_bytes += sz
                    deleted_list.append((os.path.relpath(fpath, PROJECT_ROOT), sz))
                except Exception as e:
                    pass
        try:
            shutil.rmtree(pydir)
        except Exception as e:
            pass

total_deleted_files = deleted_count + pyc_deleted
total_deleted_bytes = deleted_bytes + pyc_bytes

print(f"\n[SUMMARY] Total deleted files: {total_deleted_files}")
print(f"[SUMMARY] Total deleted bytes: {total_deleted_bytes} ({total_deleted_bytes / (1024*1024):.2f} MB)")

# Calculate final project size
total_final_files = 0
total_final_bytes = 0
for root, dirs, files in os.walk(PROJECT_ROOT):
    for f in files:
        fpath = os.path.join(root, f)
        total_final_files += 1
        total_final_bytes += os.path.getsize(fpath)

print(f"[FINAL] Final project files: {total_final_files}")
print(f"[FINAL] Final project size: {total_final_bytes} bytes ({total_final_bytes / (1024*1024):.2f} MB)")
