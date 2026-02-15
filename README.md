# GIF Maker

Desktop app for trimming, cropping, previewing, and exporting short loops from video files.

## Features
- Open video from app or CLI argument (`python app.py /path/video.mp4`).
- Timeline with thumbnails and draggable **start/end** markers.
- Interactive crop rectangle with corner drag + full-rectangle drag.
- First/last frame overlap comparison (blue/red blend) for loop alignment.
- Export formats: `gif`, `webm`, `mp4`, `mpeg`.
- Footer controls for width, fps, quality, format, and estimated output size.

## Requirements
- Python 3.10+
- Linux desktop (tested with XFCE/Thunar and KDE integration scripts)

## Install
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python app.py
# or
python app.py /path/to/video.mp4
```

## Build and Deploy Binary
```bash
make build
make deploy
```
This installs the binary at `/usr/local/bin/gifmaker`.

## Context Menu Integration
```bash
make install-context-menu
# optional custom path:
make install-context-menu EXECUTABLE=/path/to/gifmaker
```

Remove integration:
```bash
make uninstall-context-menu
```

Notes:
- On XFCE/Thunar, restart Thunar after install: `thunar -q`.
- If context launch fails, check: `~/.cache/gifmaker/context-menu.log`.

## Cleanup
```bash
make clean
```
