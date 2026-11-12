#!/usr/bin/env bash
# VOID Desktop Assistant Portable Launcher
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/../bin"
PYTHON_BIN="/home/prakash/.dodaios/.venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

export OLLAMA_MODELS="/run/media/prakash/TR_39/VOID/models"

echo "[VOID] Launching VOID Personal AI Desktop Assistant..."
"$PYTHON_BIN" "${BIN_DIR}/void-launcher.py" "$@"

