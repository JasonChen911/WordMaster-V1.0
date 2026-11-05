#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(python3 - "$ROOT/version_info.txt" <<'PY'
import pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
match = re.search(r"StringStruct\(u'ProductVersion',\s*u'([^']+)'\)", text)
if not match:
    raise SystemExit('ProductVersion missing')
print(match.group(1))
PY
)"
STAGE="${RUNNER_TEMP:-/tmp}/wordmaster-deb-stage"
OUT="${1:-$ROOT/release}"
PKG="$STAGE/wordmaster"

rm -rf -- "$STAGE"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/wordmaster/python" "$PKG/usr/bin" \
  "$PKG/opt/wordmaster/web" "$PKG/usr/share/applications" \
  "$PKG/usr/share/icons/hicolor/256x256/apps" "$OUT"

python3 -m pip install --disable-pip-version-check --no-warn-script-location \
  --target "$PKG/opt/wordmaster/python" -r "$ROOT/requirements-linux.txt"
PYTHONPATH="$PKG/opt/wordmaster/python:$ROOT/server" python3 "$ROOT/scripts/build_seed_db.py"
cp "$ROOT/main.py" "$PKG/opt/wordmaster/"
cp -a "$ROOT/server" "$PKG/opt/wordmaster/"
cp -a "$ROOT/web/dist" "$PKG/opt/wordmaster/web/"
cp -a "$ROOT/内置词库请勿删除" "$PKG/opt/wordmaster/"
cp "$ROOT/version_info.txt" "$PKG/opt/wordmaster/"

# The image comes from the existing WordMaster icon, not a placeholder.
python3 - "$ROOT/resources/icon.ico" "$PKG/usr/share/icons/hicolor/256x256/apps/wordmaster.png" <<'PY'
from PIL import Image
import sys
icon = Image.open(sys.argv[1]); icon.seek(0)
icon.convert('RGBA').resize((256, 256)).save(sys.argv[2])
PY

cat > "$PKG/usr/bin/wordmaster" <<'SH'
#!/bin/sh
set -eu
export WORDMASTER_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/WordMaster"
export PYTHONPATH="/opt/wordmaster/python:/opt/wordmaster/server${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 /opt/wordmaster/main.py "$@"
SH
chmod 755 "$PKG/usr/bin/wordmaster"

cat > "$PKG/usr/share/applications/wordmaster.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=WordMaster
Comment=英语词汇学习与智能复习
Exec=wordmaster
Icon=wordmaster
Terminal=false
Categories=Education;Languages;
StartupNotify=true
DESKTOP

cat > "$PKG/DEBIAN/control" <<CONTROL
Package: wordmaster
Version: $VERSION
Section: education
Priority: optional
Architecture: amd64
Maintainer: JasonChen <cby080812b@outlook.com>
Depends: python3 (>= 3.12), python3 (<< 3.13), python3-gi, python3-gi-cairo, python3-tk, gir1.2-gtk-3.0, gir1.2-webkit2-4.1, gnome-keyring
Description: WordMaster English vocabulary desktop application
 AI-assisted vocabulary study with local learning records and FSRS reviews.
 GitHub source and this Linux package do not contain an API key.
CONTROL

find "$PKG/opt/wordmaster" -type d -name __pycache__ -prune -exec rm -rf '{}' +
find "$PKG/opt/wordmaster" -type f \( -name '*.pyc' -o -name '*.log' -o -name '*.db-wal' -o -name '*.db-shm' \) -delete
chmod -R go+rX "$PKG/opt/wordmaster" "$PKG/usr/share"
dpkg-deb --build --root-owner-group "$PKG" "$OUT/WordMaster_${VERSION}_ubuntu24.04_amd64.deb"
sha256sum "$OUT/WordMaster_${VERSION}_ubuntu24.04_amd64.deb"
