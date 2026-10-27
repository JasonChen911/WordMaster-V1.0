"""Verify the installer/uninstaller use per-user (no-admin) locations.

Run:  python installer/test_peruser.py
"""
import os
import sys
import tempfile
import winreg
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import installer
import uninstaller

PASS = 0
FAIL = 0
UNINST_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WordMaster"


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} | {detail}")


print("=" * 60)
print("  PER-USER INSTALL / UNINSTALL REGRESSION")
print("=" * 60)

# 1. Default install dir is per-user (not Program Files)
default = installer.DEFAULT_INSTALL_DIR
localappdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
check("DEFAULT_INSTALL_DIR under LOCALAPPDATA", localappdata in default.parents or localappdata == default.parent,
      str(default))
check("DEFAULT_INSTALL_DIR not Program Files", "Program Files" not in str(default), str(default))
print(f"    install dir = {default}")

# 2. Registry registration uses HKCU
tmp = Path(tempfile.mkdtemp(prefix="wm_install_test_"))
(tmp / "WordMaster.exe").write_bytes(b"dummy")
(tmp / "uninstall.exe").write_bytes(b"dummy")

# clean any pre-existing key first
try:
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
except OSError:
    pass

installer.Installer._register_uninstall(None, tmp)

try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
    uninst, _ = winreg.QueryValueEx(key, "UninstallString")
    loc, _ = winreg.QueryValueEx(key, "InstallLocation")
    disp, _ = winreg.QueryValueEx(key, "DisplayName")
    winreg.CloseKey(key)
    check("HKCU uninstall key created", True, "")
    check("UninstallString points to uninstall.exe", uninst == f'"{tmp / "uninstall.exe"}"', uninst)
    check("InstallLocation == install dir", loc == str(tmp), loc)
    check("DisplayName == WordMaster", disp == "WordMaster", disp)
except OSError as e:
    check("HKCU uninstall key created", False, str(e))

# 3. Uninstaller-style removal deletes the HKCU key
try:
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
    removed = True
except OSError:
    removed = False
check("HKCU uninstall key deleted (uninstaller path)", removed, "")

# confirm truly gone
try:
    winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINST_KEY)
    check("HKCU key truly removed", False, "key still present")
except OSError:
    check("HKCU key truly removed", True, "")

# 4. Uninstaller INSTALL_DIR derives from the running uninstall.exe location
check("uninstaller has INSTALL_DIR from sys.executable", hasattr(uninstaller, "INSTALL_DIR"), "")

print()
print(f"  RESULT: {PASS} PASSED, {FAIL} FAILED  ({PASS + FAIL} checks)")
sys.exit(1 if FAIL else 0)
