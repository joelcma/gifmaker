#!/usr/bin/env sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <binary_path> <install_path>"
  exit 1
fi

BINARY_PATH="$1"
INSTALL_PATH="$2"
INSTALL_DIR="$(dirname "$INSTALL_PATH")"

if [ ! -f "$BINARY_PATH" ]; then
  echo "Binary not found: $BINARY_PATH"
  echo "Run 'make build' first."
  exit 1
fi

if [ ! -d "$INSTALL_DIR" ]; then
  echo "Install directory does not exist: $INSTALL_DIR"
  exit 1
fi

if [ -w "$INSTALL_DIR" ]; then
  install -m 755 "$BINARY_PATH" "$INSTALL_PATH"
else
  sudo install -m 755 "$BINARY_PATH" "$INSTALL_PATH"
fi

echo "Installed $BINARY_PATH -> $INSTALL_PATH"
