#!/usr/bin/env bash
# VOID Desktop Assistant Clean Stop
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/../bin"
PYTHON_BIN="/home/prakash/.dodaios/.venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

echo "[VOID] Stopping VOID Desktop Assistant..."
"$PYTHON_BIN" "${BIN_DIR}/void-launcher.py" --stop

