#!/usr/bin/env sh
set -eu

APP_DIR="${HOME}/.local/share/applications"
KDE_MENU_DIR="${HOME}/.local/share/kio/servicemenus"
THUNAR_UCA_FILE="${HOME}/.config/Thunar/uca.xml"
LAUNCHER_FILE="${HOME}/.local/bin/gifmaker-open"
DESKTOP_FILE="${APP_DIR}/gifmaker.desktop"
KDE_SERVICE_FILE="${KDE_MENU_DIR}/gifmaker.desktop"

rm -f "$DESKTOP_FILE"
rm -f "$KDE_SERVICE_FILE"
rm -f "$LAUNCHER_FILE"

python3 - "$THUNAR_UCA_FILE" <<'PY'
import os
import sys
import xml.etree.ElementTree as ET

uca_file = sys.argv[1]
marker = "OPEN_IN_GIFMAKER"

if not os.path.exists(uca_file):
  raise SystemExit(0)

try:
  tree = ET.parse(uca_file)
  root = tree.getroot()
except Exception:
  raise SystemExit(0)

if root.tag != "actions":
  raise SystemExit(0)

for action in list(root.findall("action")):
  desc = (action.findtext("description") or "").strip()
  name = (action.findtext("name") or "").strip()
  if desc == marker or name == "Open in GIF Maker":
    root.remove(action)

if len(root.findall("action")) == 0:
  os.remove(uca_file)
else:
  tree.write(uca_file, encoding="utf-8", xml_declaration=True)
PY

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

echo "Removed desktop integration files (if present)."
