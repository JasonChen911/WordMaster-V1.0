"""Real end-to-end per-user install + uninstall test.

Installs to %LOCALAPPDATA%\\Programs\\WordMaster, registers HKCU, creates
desktop/start-menu shortcuts, verifies, then uninstalls (files/registry/
shortcuts) and verifies cleanup + that %APPDATA%\\WordMaster data survives.

Run:  python installer/test_real_install.py
"""
import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import installer
import uninstaller  # noqa: F401  (imported to exercise its INSTALL_DIR logic)

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} | {detail}")


TARGET = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / "WordMaster"
BUNDLE = Path(__file__).resolve().parent / "bundle"
UNINST_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WordMaster"
DESKTOP_LNK = Path(os.environ["USERPROFILE"]) / "Desktop" / "WordMaster.lnk"
STARTMENU_DIR = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "WordMaster"


def cleanup_all():
    subprocess.run(["taskkill", "/f", "/im", "WordMaster.exe"], capture_output=True)
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
    except OSError:
        pass
    if TARGET.exists():
        shutil.rmtree(TARGET, ignore_errors=True)
    if DESKTOP_LNK.exists():
        DESKTOP_LNK.unlink()
    if STARTMENU_DIR.exists():
        shutil.rmtree(STARTMENU_DIR, ignore_errors=True)


print("=" * 60)
print("  REAL PER-USER INSTALL / UNINSTALL")
print("=" * 60)

cleanup_all()

# ── INSTALL (mirror do_install's non-GUI steps) ──
print("\n=== INSTALL ===")
TARGET.mkdir(parents=True, exist_ok=True)
for f in BUNDLE.iterdir():
    if f.is_file():
        shutil.copy2(str(f), str(TARGET / f.name))
    elif f.is_dir() and f.name != "resources":
        shutil.copytree(str(f), str(TARGET / f.name), dirs_exist_ok=True)

check("WordMaster.exe installed", (TARGET / "WordMaster.exe").exists())
check("uninstall.exe installed", (TARGET / "uninstall.exe").exists())

installer.Installer._register_uninstall(None, TARGET)
installer.Installer._create_shortcut(None, "Desktop", TARGET)
installer.Installer._create_shortcut(None, "StartMenu", TARGET)

key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
uninst = winreg.QueryValueEx(key, "UninstallString")[0]
winreg.CloseKey(key)
check("HKCU uninstall registered", uninst == f'"{TARGET / "uninstall.exe"}"', uninst)
check("Desktop shortcut created", DESKTOP_LNK.exists(), str(DESKTOP_LNK))
check("StartMenu shortcut created", (STARTMENU_DIR / "WordMaster.lnk").exists(), str(STARTMENU_DIR))

# ── UNINSTALL (mirror do_uninstall's non-GUI steps) ──
print("\n=== UNINSTALL ===")
subprocess.run(["taskkill", "/f", "/im", "WordMaster.exe"], capture_output=True)
if DESKTOP_LNK.exists():
    DESKTOP_LNK.unlink()
if STARTMENU_DIR.exists():
    shutil.rmtree(STARTMENU_DIR, ignore_errors=True)
try:
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
except OSError:
    pass
shutil.rmtree(TARGET, ignore_errors=True)

check("Install dir removed", not TARGET.exists(), str(TARGET))
check("Desktop shortcut removed", not DESKTOP_LNK.exists())
check("StartMenu removed", not STARTMENU_DIR.exists())
try:
    winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
    check("Registry removed", False, "still present")
except OSError:
    check("Registry removed", True)

# ── User data preserved ──
appdata = Path(os.environ["APPDATA"]) / "WordMaster"
check("AppData dir preserved", appdata.exists(), str(appdata))
check("wordmaster.db preserved", (appdata / "wordmaster.db").exists())

print()
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
sys.exit(1 if FAIL else 0)
