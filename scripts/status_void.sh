#!/usr/bin/env bash
# VOID Diagnostics & Health Check
set -e
echo "================================================="
echo "   VOID AI DESKTOP ASSISTANT DIAGNOSTICS        "
echo "================================================="

echo -n "1. Widget Process: "
if pgrep -f "void-widget.py" > /dev/null; then
    echo "ONLINE (PID $(pgrep -f 'void-widget.py'))"
else
    echo "OFFLINE"
fi

echo -n "2. Ollama Daemon:  "
if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "ONLINE"
else
    echo "STANDBY / OFFLINE"
fi

echo -n "3. Loaded Brains:  "
curl -s http://127.0.0.1:11434/api/ps 2>/dev/null || echo "None"
echo ""

echo -n "4. Dodaios Health: "
curl -s http://127.0.0.1:47821/api/health 2>/dev/null || echo "Offline"
echo ""
echo "================================================="

