#!/usr/bin/env bash
# ==============================================================================
# VOID Desktop Assistant — Clean Stop Script
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BIN_DIR="${ROOT_DIR}/bin"

# Dynamically locate Python virtual environment
if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "${VIRTUAL_ENV}/bin/python" ]; then
    PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif [ -x "${ROOT_DIR}/.venv/bin/python" ]; then
    PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
elif [ -x "${HOME}/.dodaios/.venv/bin/python" ]; then
    PYTHON_BIN="${HOME}/.dodaios/.venv/bin/python"
elif [ -x "${HOME}/.void/.venv/bin/python" ]; then
    PYTHON_BIN="${HOME}/.void/.venv/bin/python"
else
    PYTHON_BIN="$(command -v python3 || echo "python3")"
fi

echo "[VOID] Stopping VOID Desktop Assistant, deactivating models & reclaiming RAM..."
if [ -f "${BIN_DIR}/void-launcher.py" ]; then
    "$PYTHON_BIN" "${BIN_DIR}/void-launcher.py" --stop "$@" || true
fi

# Failsafe cleanup in case of abnormal state
pkill -f "void-widget.py" 2>/dev/null || true
pkill -f "dodaios serve" 2>/dev/null || true
pkill -f "llama-server" 2>/dev/null || true
pkill -f "llama-finetune" 2>/dev/null || true
sync

if command -v notify-send >/dev/null 2>&1; then
    notify-send "VOID AI Shutdown" "VOID stopped. Models deactivated, tasks finalized, and RAM cleared." -i process-stop -t 3500 2>/dev/null || true
fi

echo "[VOID] Complete stop executed."
