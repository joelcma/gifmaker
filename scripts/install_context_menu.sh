#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <gifmaker_executable_path>"
  exit 1
fi

EXECUTABLE="$1"
SUPPORTED_EXTENSIONS="mp4 mov mkv avi webm m4v"
MIME_TYPES="video/mp4;video/quicktime;video/x-matroska;video/x-msvideo;video/webm;video/x-m4v;"
THUNAR_PATTERNS="*.mp4;*.MP4;*.mov;*.MOV;*.mkv;*.MKV;*.avi;*.AVI;*.webm;*.WEBM;*.m4v;*.M4V"

if [ ! -x "$EXECUTABLE" ]; then
  echo "Executable not found or not executable: $EXECUTABLE"
  echo "Tip: run 'make deploy' first, or pass EXECUTABLE=/path/to/gifmaker"
  exit 1
fi

APP_DIR="${HOME}/.local/share/applications"
KDE_MENU_DIR="${HOME}/.local/share/kio/servicemenus"
THUNAR_CONFIG_DIR="${HOME}/.config/Thunar"
THUNAR_UCA_FILE="${THUNAR_CONFIG_DIR}/uca.xml"
LOCAL_BIN_DIR="${HOME}/.local/bin"
LAUNCHER_FILE="${LOCAL_BIN_DIR}/gifmaker-open"
LOG_DIR="${HOME}/.cache/gifmaker"
DESKTOP_FILE="${APP_DIR}/gifmaker.desktop"
KDE_SERVICE_FILE="${KDE_MENU_DIR}/gifmaker.desktop"

mkdir -p "$LOCAL_BIN_DIR"
mkdir -p "$LOG_DIR"

cat > "$LAUNCHER_FILE" <<EOF
#!/usr/bin/env sh
set -eu

TARGET_EXEC="${EXECUTABLE}"
LOG_FILE="${LOG_DIR}/context-menu.log"

if [ "\$#" -lt 1 ]; then
  echo "[\$(date '+%F %T')] No input file provided" >> "\$LOG_FILE"
  exit 1
fi

INPUT_PATH="\$1"
INPUT_LOWER="\$(printf '%s' "\$INPUT_PATH" | tr '[:upper:]' '[:lower:]')"

is_supported=0
for ext in ${SUPPORTED_EXTENSIONS}; do
  case "\$INPUT_LOWER" in
    *."\$ext")
      is_supported=1
      break
      ;;
  esac
done

if [ "\$is_supported" -ne 1 ]; then
  echo "[\$(date '+%F %T')] Unsupported file extension: \$INPUT_PATH" >> "\$LOG_FILE"
  exit 1
fi

if [ ! -x "\$TARGET_EXEC" ]; then
  echo "[\$(date '+%F %T')] Executable not found: \$TARGET_EXEC" >> "\$LOG_FILE"
  exit 1
fi

nohup "\$TARGET_EXEC" "\$INPUT_PATH" >> "\$LOG_FILE" 2>&1 &
EOF
chmod +x "$LAUNCHER_FILE"

mkdir -p "$APP_DIR"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=GIF Maker
Comment=Create GIFs and short clips from video files
Exec=${LAUNCHER_FILE} %f
Terminal=false
NoDisplay=false
Categories=AudioVideo;Video;
MimeType=${MIME_TYPES}
EOF

mkdir -p "$KDE_MENU_DIR"
cat > "$KDE_SERVICE_FILE" <<EOF
[Desktop Entry]
Type=Service
X-KDE-ServiceTypes=KonqPopupMenu/Plugin
MimeType=${MIME_TYPES}
Actions=OpenInGifMaker
X-KDE-Priority=TopLevel

[Desktop Action OpenInGifMaker]
Name=Open in GIF Maker
Exec=${LAUNCHER_FILE} %f
Icon=video-x-generic
EOF

mkdir -p "$THUNAR_CONFIG_DIR"
THUNAR_PATTERNS="$THUNAR_PATTERNS" python3 - "$THUNAR_UCA_FILE" <<'PY'
import os
import sys
import xml.etree.ElementTree as ET

uca_file = sys.argv[1]
marker = "OPEN_IN_GIFMAKER"
patterns = os.environ.get("THUNAR_PATTERNS", "*.mp4;*.mov;*.mkv;*.avi;*.webm;*.m4v")

if os.path.exists(uca_file):
  try:
    tree = ET.parse(uca_file)
    root = tree.getroot()
    if root.tag != "actions":
      root = ET.Element("actions")
      tree = ET.ElementTree(root)
  except Exception:
    root = ET.Element("actions")
    tree = ET.ElementTree(root)
else:
  root = ET.Element("actions")
  tree = ET.ElementTree(root)

for action in list(root.findall("action")):
  desc = (action.findtext("description") or "").strip()
  name = (action.findtext("name") or "").strip()
  if desc == marker or name == "Open in GIF Maker":
    root.remove(action)

action = ET.SubElement(root, "action")
ET.SubElement(action, "icon").text = "video-x-generic"
ET.SubElement(action, "name").text = "Open in GIF Maker"
ET.SubElement(action, "submenu").text = ""
ET.SubElement(action, "unique-id").text = "gifmaker-open-context"
ET.SubElement(action, "command").text = f'{os.path.expanduser("~")}/.local/bin/gifmaker-open %f'
ET.SubElement(action, "description").text = marker
ET.SubElement(action, "patterns").text = patterns
ET.SubElement(action, "directories")
ET.SubElement(action, "audio-files")
ET.SubElement(action, "image-files")
ET.SubElement(action, "other-files")
ET.SubElement(action, "text-files")
ET.SubElement(action, "video-files")

tree.write(uca_file, encoding="utf-8", xml_declaration=True)
PY

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi

echo "Installed desktop integration:" 
echo "  $DESKTOP_FILE"
echo "Installed launcher wrapper:"
echo "  $LAUNCHER_FILE"
echo "Installed KDE context-menu entry (if KDE/Dolphin is used):"
echo "  $KDE_SERVICE_FILE"
echo "Installed XFCE/Thunar context-menu entry (if Thunar is used):"
echo "  $THUNAR_UCA_FILE"
echo ""
echo "You may need to restart your file manager session (or run: thunar -q) to see new menu entries."
echo "If action still fails, check log: ${LOG_DIR}/context-menu.log"
