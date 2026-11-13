#!/usr/bin/env bash
# ==============================================================================
# VOID Desktop Assistant — Portable Launch Script
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

# Export models directory if present
if [ -d "${ROOT_DIR}/models" ]; then
    export OLLAMA_MODELS="${ROOT_DIR}/models"
elif [ -d "${HOME}/.ollama/models" ]; then
    export OLLAMA_MODELS="${HOME}/.ollama/models"
fi

echo "[VOID] Launching VOID Personal AI Desktop Assistant via ${PYTHON_BIN}..."
exec "$PYTHON_BIN" "${BIN_DIR}/void-launcher.py" "$@"
