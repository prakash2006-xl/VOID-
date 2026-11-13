#!/usr/bin/env bash
# Synchronizes local system files to this VOID backup directory on TR_39
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/.."

echo "[VOID Backup] Synchronizing active files to ${TARGET_DIR}..."

cp -p "${HOME}/.local/bin/void-widget.py" "${TARGET_DIR}/bin/" 2>/dev/null || true
cp -p "${HOME}/.local/bin/void-launcher.py" "${TARGET_DIR}/bin/" 2>/dev/null || true
cp -p "${HOME}/.config/autostart/void.desktop" "${TARGET_DIR}/config/" 2>/dev/null || true
cp -p "${HOME}/.config/void/tasks.json" "${TARGET_DIR}/config/" 2>/dev/null || true
cp -p "${HOME}/.config/void/widget_pos.json" "${TARGET_DIR}/config/" 2>/dev/null || true

echo "[VOID Backup] Backup completed successfully."

