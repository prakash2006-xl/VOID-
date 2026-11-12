#!/usr/bin/env bash
# Synchronizes local system files to this VOID backup directory on TR_39
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/.."

echo "[VOID Backup] Synchronizing active files to ${TARGET_DIR}..."

cp -p /home/prakash/.local/bin/void-widget.py "${TARGET_DIR}/bin/"
cp -p /home/prakash/.local/bin/void-launcher.py "${TARGET_DIR}/bin/"
cp -p /home/prakash/.config/autostart/void.desktop "${TARGET_DIR}/config/"
cp -p /home/prakash/.config/void/tasks.json "${TARGET_DIR}/config/"
cp -p /home/prakash/.config/void/widget_pos.json "${TARGET_DIR}/config/"

echo "[VOID Backup] Backup completed successfully."

