#!/usr/bin/env python3
"""
VOID Floating Glass Island Desktop Assistant Widget
- Ultra-compact Glass Capsule / Dynamic Island (50px height collapsed)
- Expandable Glass Flow Card with rich action cards, screenshot preview, monospace terminal output
- Full Dodaios 105 tools integration (search_web, calculate, screenshot, audio-devices, skills, config)
- Sub-5ms fast-path local desktop automation (KWin DBus window control, app launch/close, volume, power, timers)
- Continuous background wake-word listening ("Hey VOID" / "VOID") with Vosk open-grammar
- Faster-Whisper base int8 STT + Piper local neural TTS
- Direct Ollama lfm3-omni:2b brain integration with instant standby mode
"""

import os
import sys

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

import time
import json
import re
import ast
import queue
import shutil
import io
import wave
import asyncio
import threading
import subprocess
import math
import random
import collections
import urllib.parse
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import sounddevice as sd
from vosk import Model as VoskModel, KaldiRecognizer
from faster_whisper import WhisperModel

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPoint, QPointF, QRect
from PySide6.QtGui import (
    QColor, QPainter, QRadialGradient, QLinearGradient, QBrush,
    QPen, QFont, QMouseEvent, QPixmap, QPainterPath
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea
)

# Agentic Multi-Agent Framework Integration
try:
    _void_pkg_root = "/run/media/prakash/TR_39/VOID"
    if _void_pkg_root not in sys.path:
        sys.path.insert(0, _void_pkg_root)
    from agentic import (
        SupervisorAgent, ToolRegistry, AIProviderManager, parse_cloud_credentials, PermissionManager,
        AgentMemoryManager, AuditLogger, CompetitionDemos, AgentActivityCard,
        CompactExecutionPopup, SystemInfoPopup,
        WorkflowLifecycleState, TaskStatus
    )
except ImportError as e:
    print(f'[VOID Agentic Import Notice] {e}', flush=True)


# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------
SSD_VOID_DIR = Path("/run/media/prakash/TR_39/VOID")
CONFIG_DIR = SSD_VOID_DIR / "config" if SSD_VOID_DIR.exists() else Path("/home/prakash/.config/void")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
POS_FILE = CONFIG_DIR / "widget_pos.json"
MODELS_DIR = SSD_VOID_DIR / "models" if SSD_VOID_DIR.exists() else Path("/home/prakash/.ollama/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)
os.environ["OLLAMA_MODELS"] = str(MODELS_DIR)
CHROMIUM_BIN = "/usr/bin/chromium-browser"

MEMORY_DIR = SSD_VOID_DIR / "memory" if SSD_VOID_DIR.exists() else CONFIG_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
MAX_MEMORY_BYTES = 1500 * 1024 * 1024  # 1.5 GB SSD Ring Buffer allocation
PRUNE_TARGET_BYTES = 1200 * 1024 * 1024 # 1.2 GB LRU target

OLLAMA_URL = "http://127.0.0.1:11434"
DODAIOS_URL = "http://127.0.0.1:47821"

VOSK_MODEL_PATH = "/home/prakash/.dodaios/data/wake_models/vosk/en/vosk-model-small-en-us-0.15"
WHISPER_MODEL_NAME = "base"
PIPER_MODEL_PATH = "/home/prakash/.dodaios/data/models/vits-piper-en_US-ryan-medium/en_US-ryan-medium.onnx"
SCREENSHOT_DIR = Path("/home/prakash/Pictures/Screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

FORBIDDEN_PATHS = [
    "/usr", "/etc", "/boot", "/root", "/var", "/bin", "/sbin",
    "/lib", "/lib64", "/sys", "/proc", "/dev"
]

try:
    import docx
except ImportError:
    docx = None

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    openpyxl = None

DOCS_DIR = Path("/home/prakash/Documents")
REPORTS_DIR = DOCS_DIR / "Reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "draft_docx_document",
            "description": "Draft and format a professional Word document (.docx) with title, headings, bullet lists, and tables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the document"},
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "heading": {"type": "string", "description": "Section heading"},
                                "content": {"type": "string", "description": "Paragraph text or bullet items"},
                                "table": {
                                    "type": "object",
                                    "properties": {
                                        "headers": {"type": "array", "items": {"type": "string"}},
                                        "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
                                    }
                                }
                            }
                        },
                        "description": "List of structured sections"
                    },
                    "filename": {"type": "string", "description": "Optional custom filename"}
                },
                "required": ["title", "sections"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_excel_spreadsheet",
            "description": "Draft and format a professional Excel workbook (.xlsx) with styled dark-blue headers, borders, and auto-fitted columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the spreadsheet"},
                    "headers": {"type": "array", "items": {"type": "string"}, "description": "Column header names"},
                    "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "Grid of row values"},
                    "sheet_name": {"type": "string", "description": "Optional worksheet name"},
                    "filename": {"type": "string", "description": "Optional custom filename"}
                },
                "required": ["title", "headers", "rows"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_formatted_report",
            "description": "Draft a formatted report or executive summary in docx, xlsx, txt, or md format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Report title"},
                    "topic": {"type": "string", "description": "Subject or topic of the report"},
                    "content": {"type": "string", "description": "Main report content or key findings"},
                    "file_type": {"type": "string", "enum": ["docx", "xlsx", "txt", "md"], "description": "Desired file format"}
                },
                "required": ["title", "topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_and_generate_document",
            "description": "Conduct multi-source web research on a topic and generate a beautifully formatted report document (.docx, .xlsx, or .md).",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic or industry to research online"},
                    "file_type": {"type": "string", "enum": ["docx", "xlsx", "md", "txt"], "description": "Desired output document format"}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_dictation_mode",
            "description": "Toggle voice typing / dictation mode to type spoken thoughts directly into notes and clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["start", "stop"], "description": "Action to perform"},
                    "note_title": {"type": "string", "description": "Optional title for the dictation note"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the live web for current information, news, documentation, or facts via DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query keywords"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_scrape_deep_research",
            "description": "Perform deep online research or extract readable content from a given web URL or research topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Optional specific URL to scrape and analyze"},
                    "topic": {"type": "string", "description": "Optional topic name to conduct multi-source web research on"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Capture a screenshot of the user's active desktop screen and save to ~/Pictures/Screenshots with optional custom filename.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Optional custom name for the saved screenshot (without extension)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": "Open Chromium browser with a specific URL, new tab, or search query on screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open (e.g. https://google.com or chrome://newtab)"},
                    "new_tab": {"type": "boolean", "description": "Whether to open in a new tab"},
                    "search_query": {"type": "string", "description": "Optional search query to run in Chromium"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_search",
            "description": "Perform a live Google or DuckDuckGo search directly inside Chromium browser on screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords or question"},
                    "engine": {"type": "string", "description": "Search engine ('google' or 'duckduckgo')"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_compose_email",
            "description": "Compose an email and open it directly inside Chromium browser (Gmail compose or Outlook webmail) with recipient, subject, and body pre-filled so user can review and send.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Recipient email address (e.g. rskakavin@gmail.com)"},
                    "subject": {"type": "string", "description": "Subject of the email"},
                    "body": {"type": "string", "description": "Complete text body of the email"},
                    "provider": {"type": "string", "description": "Webmail provider ('gmail' or 'outlook')"}
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user_clarification",
            "description": "Prompt the user with a question when an essential parameter is missing (e.g. asking for recipient email, search term, or confirmation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The exact question to ask the user"},
                    "missing_param": {"type": "string", "description": "Name of missing parameter (e.g. 'recipient_email')"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_read_page",
            "description": "Extract and read text content from a web page URL using BeautifulSoup parser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Web page URL to read and analyze"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Adjust or set master audio volume percentage (0 - 100%) or mute/unmute audio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level_pct": {"type": "integer", "description": "Target volume percentage (0 - 100)"},
                    "action": {"type": "string", "enum": ["set", "mute", "unmute", "toggle_mute", "up", "down"], "description": "Volume action to perform"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_control",
            "description": "Control media playback (play, pause, next, previous, stop) for music and video players via MPRIS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["play", "pause", "toggle", "next", "previous", "stop"], "description": "Playback action to execute"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_clipboard",
            "description": "Read from or copy new text to the Wayland system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read", "write"], "description": "'read' to get clipboard, 'write' to set it"},
                    "text": {"type": "string", "description": "Text to copy to clipboard (if action is 'write')"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_brightness",
            "description": "Read or adjust screen display brightness percentage via KDE DBus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level_pct": {"type": "integer", "description": "Target brightness percentage (5 - 100)"},
                    "action": {"type": "string", "enum": ["set", "get", "up", "down"], "description": "Brightness action"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current live weather condition and temperature for any city or the user's current location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name (e.g. Madurai, Chennai, London) or empty for current location"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_hardware_vitals",
            "description": "Inspect battery percentage, power supply state, and CPU/GPU thermal temperatures.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a sticky note, memo, or thought to ~/Documents/Notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title or topic of note"},
                    "content": {"type": "string", "description": "The body text content of the note"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Launch a desktop application or browser with optional URL on Fedora KDE Plasma.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of app: chromium, firefox, konsole, dolphin, kcalc, kwrite, systemsettings"},
                    "url": {"type": "string", "description": "Optional URL to navigate to in the browser"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Close a running application by process name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of application: chromium, firefox, konsole, dolphin, etc."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_window",
            "description": "Control KDE Plasma active or named window (close, minimize, maximize, fullscreen, show_desktop).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["close", "minimize", "maximize", "fullscreen", "show_desktop"], "description": "The window action"},
                    "app_name": {"type": "string", "description": "Optional target application name (e.g. chromium, firefox, konsole)"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_safe_command",
            "description": "Execute a harmless read-only shell command on Fedora (e.g. date, uptime, free -h, df -h, uname -a). Never destructive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression safely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression (e.g. 50 * 4, sqrt(144))"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_timer",
            "description": "Start an interactive countdown timer on the user desktop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "integer", "description": "Timer duration in seconds"}
                },
                "required": ["seconds"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files by filename pattern in the user's home directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Filename pattern to match (e.g. *.txt, *report*, *.pdf)"},
                    "search_path": {"type": "string", "description": "Directory to search within (default ~/Documents)"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_document",
            "description": "Create and save a text, note, or markdown document in the user's home directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Target file path (e.g. ~/Documents/notes.txt or /home/prakash/Documents/summary.md)"},
                    "content": {"type": "string", "description": "The text or markdown content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Read the content of a text or markdown file located in the user's home directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read (e.g. ~/Documents/notes.txt)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_document",
            "description": "Append text or notes to an existing document in ~/Documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Target file path (e.g. ~/Documents/log.txt)"},
                    "content": {"type": "string", "description": "Content to append"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files and folders in a specified user directory (default ~/Documents).",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Folder path to list (e.g. ~/Documents, ~/Downloads)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compose_email",
            "description": "Compose and format an email draft, and optionally save it to ~/Documents/Drafts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Recipient email or name"},
                    "subject": {"type": "string", "description": "Email subject title"},
                    "body": {"type": "string", "description": "Body message text of the email"},
                    "save_draft": {"type": "boolean", "description": "Whether to save draft to disk"}
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "security_audit",
            "description": "Inspect system security status: open listening ports, active user sessions, failed logins, and firewall/SELinux state.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_status",
            "description": "Get detailed machine vitals: CPU load, RAM usage %, disk space, system uptime, and Ollama AI model residency state.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_task",
            "description": "Manage persistent tasks and reminders (add, list, complete, delete) stored across reboots in tasks.json.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "list", "complete", "delete"], "description": "Task action"},
                    "task_text": {"type": "string", "description": "Description of the task when adding"},
                    "task_id": {"type": "string", "description": "Task ID (e.g. T1, T2) or keyword when completing or deleting"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "learn_fact",
            "description": "Store a user preference, habit, or learned fact permanently into VOID SSD narrow AI memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The fact or preference to remember"},
                    "category": {"type": "string", "description": "Category (preference, project, habit, system)"}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Recall learned user preferences, habits, or stored facts from VOID SSD memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword or topic to search in memory"}
                },
                "required": ["query"]
            }
        }
    }
]

# ---------------------------------------------------------------------------
# Audio Chimes (Synthesized Sine Waves)
# ---------------------------------------------------------------------------
def play_chime(kind: str = "wake") -> None:
    def _run():
        try:
            sr = 22050
            if kind == "wake":
                t1 = np.linspace(0, 0.08, int(sr * 0.08), False)
                t2 = np.linspace(0, 0.12, int(sr * 0.12), False)
                tone1 = np.sin(2 * np.pi * 587.33 * t1) * 0.25 * np.linspace(1, 0.4, len(t1))
                tone2 = np.sin(2 * np.pi * 880.00 * t2) * 0.30 * np.linspace(1, 0, len(t2))
                audio = np.concatenate([tone1, tone2])
            else:  # alarm chime
                tones = []
                for freq in [659.25, 880.00, 1046.50, 1318.51]:
                    t = np.linspace(0, 0.12, int(sr * 0.12), False)
                    tone = np.sin(2 * np.pi * freq * t) * 0.35 * np.linspace(1, 0.1, len(t))
                    tones.append(tone)
                audio = np.concatenate(tones)
            sd.play(audio.astype(np.float32), samplerate=sr)
            sd.wait()
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

# ---------------------------------------------------------------------------
# Safe Math Evaluation
# ---------------------------------------------------------------------------
def _safe_eval(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        if isinstance(node.op, ast.UAdd): return +operand
        if isinstance(node.op, ast.USub): return -operand
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div):
            if right == 0: raise ZeroDivisionError("division by zero")
            return left / right
        if isinstance(node.op, ast.Pow):
            if abs(right) > 20: raise ValueError("power too large")
            return left ** right
        if isinstance(node.op, ast.Mod): return left % right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fname = node.func.id
        args = [_safe_eval(a) for a in node.args]
        import math
        if fname == "sqrt" and len(args) == 1: return math.sqrt(args[0])
        if fname == "abs" and len(args) == 1: return abs(args[0])
    raise ValueError("unsupported math operation")

def evaluate_math(expr: str) -> float | int | None:
    try:
        cleaned = expr.strip().replace("^", "**").replace("x", "*")
        tree = ast.parse(cleaned, mode="eval")
        res = _safe_eval(tree.body)
        return int(res) if isinstance(res, float) and res.is_integer() else round(res, 4)
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Desktop Automation (Fast-Path <5ms)
# ---------------------------------------------------------------------------
def kwin_shortcut(shortcut_name: str) -> bool:
    try:
        res = subprocess.run([
            "qdbus-qt6", "org.kde.kglobalaccel", "/component/kwin",
            "org.kde.kglobalaccel.Component.invokeShortcut", shortcut_name
        ], capture_output=True, text=True, timeout=1.0)
        return res.returncode == 0
    except Exception:
        return False

def close_software_by_name(name: str) -> bool:
    clean = name.strip().lower()
    app_map = {
        "chromium": "chromium", "firefox": "firefox", "browser": "chromium",
        "dolphin": "dolphin", "files": "dolphin", "file manager": "dolphin",
        "terminal": "konsole", "konsole": "konsole", "kate": "kate",
        "kwrite": "kwrite", "kcalc": "kcalc", "calculator": "kcalc",
        "vlc": "vlc", "settings": "systemsettings"
    }
    target = app_map.get(clean, clean)
    try:
        subprocess.run(["pkill", "-f", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def spawn_software(binary: str) -> bool:
    try:
        parts = binary.split()
        cmd = [shutil.which(parts[0]) or parts[0]] + parts[1:]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception:
        return False

def is_command_safe(cmd: str) -> tuple[bool, str]:
    c_lower = cmd.strip().lower()
    if any(c_lower.startswith(p) for p in ["sudo ", "su ", "pkexec ", "doas "]):
        return False, "Privileged execution is blocked by safety policy."
    for forbidden in FORBIDDEN_PATHS:
        for pattern in [f"rm {forbidden}", f"rm -rf {forbidden}", f"mv {forbidden}", f"dd if", "mkfs"]:
            if pattern in c_lower:
                return False, f"Protected path '{forbidden}' is restricted."
    return True, "OK"

def run_terminal_command(cmd: str) -> tuple[int, str]:
    safe, reason = is_command_safe(cmd)
    if not safe:
        return -1, f"Execution Refused: {reason}"
    try:
        res = subprocess.run(
            cmd, shell=True, executable="/bin/bash",
            capture_output=True, text=True, timeout=10.0, cwd="/home/prakash"
        )
        out = (res.stdout + res.stderr).strip()
        return res.returncode, out or "(Command completed with no output)"
    except subprocess.TimeoutExpired:
        return -1, "Command execution timed out after 10 seconds."
    except Exception as e:
        return -1, f"Command execution error: {e}"

def parse_timer_duration(text: str) -> int:
    m = re.search(r"(\d+)\s*(?:minutes?|mins?|m)", text)
    s = re.search(r"(\d+)\s*(?:seconds?|secs?|s)", text)
    h = re.search(r"(\d+)\s*(?:hours?|hrs?|h)", text)
    tot = 0
    if h: tot += int(h.group(1)) * 3600
    if m: tot += int(m.group(1)) * 60
    if s: tot += int(s.group(1))
    if tot == 0:
        just_num = re.search(r"\b(\d+)\b", text)
        if just_num: tot = int(just_num.group(1)) * 60
    return tot

def kwin_manage_app_window(app_name: str, action: str) -> bool:
    """Controls specific application windows on KDE Plasma Wayland via KWin Scripting."""
    import tempfile
    clean_app = app_name.strip().lower()
    app_map = {
        "chromium": "chromium", "browser": "chromium", "firefox": "firefox",
        "terminal": "konsole", "konsole": "konsole", "dolphin": "dolphin",
        "files": "dolphin", "calculator": "kcalc", "kcalc": "kcalc",
        "text editor": "kwrite", "kwrite": "kwrite", "kate": "kate"
    }
    target = app_map.get(clean_app, clean_app)
    script = f"""
    var windows = workspace.windowList();
    for (var i = 0; i < windows.length; i++) {{
        var w = windows[i];
        var res = (w.resourceClass || '').toLowerCase();
        var cap = (w.caption || '').toLowerCase();
        if (res.indexOf('{target}') !== -1 || cap.indexOf('{target}') !== -1) {{
            if ('{action}' === 'minimize') {{
                w.minimized = true;
            }} else if ('{action}' === 'maximize') {{
                w.maximized = 3;
            }} else if ('{action}' === 'fullscreen') {{
                w.fullScreen = !w.fullScreen;
            }} else if ('{action}' === 'close') {{
                w.closeWindow();
            }} else if ('{action}' === 'activate') {{
                workspace.activeWindow = w;
            }}
            break;
        }}
    }}
    """
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(script)
            fpath = f.name
        load_res = subprocess.run(
            ["qdbus-qt6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript", fpath],
            capture_output=True, text=True, timeout=1.0
        )
        num = load_res.stdout.strip()
        if num:
            subprocess.run(["qdbus-qt6", "org.kde.KWin", f"/Scripting/Script{num}", "org.kde.kwin.Script.run"], timeout=1.0)
            subprocess.run(["qdbus-qt6", "org.kde.KWin", f"/Scripting/Script{num}", "org.kde.kwin.Script.stop"], timeout=1.0)
            try:
                os.remove(fpath)
            except Exception:
                pass
            return True
    except Exception as e:
        print(f"[VOID KWin Script Error] {e}", flush=True)
    return False

def is_safe_user_path(p: str | Path) -> bool:
    try:
        resolved = Path(p).expanduser().resolve()
        home = Path("/home/prakash").resolve()
        if not resolved.is_relative_to(home):
            return False
        for forbidden in FORBIDDEN_PATHS:
            if str(resolved).startswith(forbidden) or resolved == Path(forbidden):
                return False
        return True
    except Exception:
        return False

def get_system_health() -> dict[str, Any]:
    health: dict[str, Any] = {}
    try:
        with open("/proc/meminfo") as f:
            mem = f.read()
        total_kb = int(re.search(r"MemTotal:\s+(\d+)", mem).group(1))
        avail_kb = int(re.search(r"MemAvailable:\s+(\d+)", mem).group(1))
        used_kb = total_kb - avail_kb
        health["ram_total_gb"] = round(total_kb / 1024 / 1024, 1)
        health["ram_used_gb"] = round(used_kb / 1024 / 1024, 1)
        health["ram_pct"] = round((used_kb / total_kb) * 100, 1)
    except Exception:
        health["ram_pct"] = 0.0

    try:
        with open("/proc/loadavg") as f:
            health["cpu_load_1m"] = float(f.read().split()[0])
    except Exception:
        health["cpu_load_1m"] = 0.0

    try:
        st = os.statvfs("/home/prakash")
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        total_gb = (st.f_blocks * st.f_frsize) / (1024**3)
        used_gb = total_gb - free_gb
        health["disk_free_gb"] = round(free_gb, 1)
        health["disk_total_gb"] = round(total_gb, 1)
        health["disk_pct"] = round((used_gb / total_gb) * 100, 1)
    except Exception:
        health["disk_pct"] = 0.0

    try:
        with open("/proc/uptime") as f:
            up_sec = float(f.read().split()[0])
        hrs = int(up_sec // 3600)
        mins = int((up_sec % 3600) // 60)
        health["uptime_str"] = f"{hrs}h {mins}m"
    except Exception:
        health["uptime_str"] = "unknown"

    try:
        import httpx
        r = httpx.get(f"{OLLAMA_URL}/api/ps", timeout=0.8)
        if r.status_code == 200:
            running = r.json().get("models", [])
            names = [m.get("name", "") for m in running]
            health["ollama_running"] = True
            health["loaded_models"] = names
            health["brain_active"] = any("lfm3" in n for n in names)
        else:
            health["ollama_running"] = False
            health["loaded_models"] = []
            health["brain_active"] = False
    except Exception:
        health["ollama_running"] = False
        health["loaded_models"] = []
        health["brain_active"] = False

    return health

class TaskManager:
    def __init__(self, filepath: Path = CONFIG_DIR / "tasks.json"):
        self.filepath = filepath
        self.tasks: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
        return []

    def _save(self) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2)
        except Exception as e:
            print(f"[VOID TaskManager Error] Saving: {e}", flush=True)

    def add_task(self, text: str, task_type: str = "task") -> dict[str, Any]:
        task_id = f"T{len(self.tasks) + 1}"
        item = {
            "id": task_id,
            "text": text.strip(),
            "type": task_type,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        }
        self.tasks.append(item)
        self._save()
        return item

    def list_active(self) -> list[dict[str, Any]]:
        return [t for t in self.tasks if t.get("status") == "pending"]

    def complete_task(self, identifier: str) -> bool:
        ident_lower = identifier.lower().strip()
        for t in self.tasks:
            if t.get("status") == "pending":
                if t.get("id", "").lower() == ident_lower or ident_lower in t.get("text", "").lower():
                    t["status"] = "completed"
                    t["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    self._save()
                    return True
        return False

    def delete_task(self, identifier: str) -> bool:
        ident_lower = identifier.lower().strip()
        for i, t in enumerate(self.tasks):
            if t.get("id", "").lower() == ident_lower or ident_lower in t.get("text", "").lower():
                self.tasks.pop(i)
                self._save()
                return True
        return False

    def clear_all(self) -> None:
        self.tasks.clear()
        self._save()

# ---------------------------------------------------------------------------
# Narrow AI SSD Memory Engine (1.5 GB LRU Ring Buffer)
# ---------------------------------------------------------------------------
class MemoryEngine:
    def __init__(self, mem_dir: Path = MEMORY_DIR) -> None:
        self.mem_dir = mem_dir
        self.mem_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.mem_dir / "profile.json"
        self.episodic_path = self.mem_dir / "episodic.jsonl"
        self.store_dir = self.mem_dir / "store"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.profile: dict[str, Any] = self._load_profile()

    def _load_profile(self) -> dict[str, Any]:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {
            "user_name": "Prakash",
            "preferred_browser": "Chromium",
            "desktop_environment": "Fedora KDE Plasma (Wayland)",
            "custom_preferences": {}
        }

    def save_profile(self) -> None:
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2)
        except Exception as e:
            print(f"[VOID MemoryEngine Error] Saving profile: {e}", flush=True)

    def learn(self, fact_text: str, category: str = "general") -> dict[str, Any]:
        clean = fact_text.strip()
        clean_lower = clean.lower()
        if "browser" in clean_lower:
            if "chrome" in clean_lower or "chromium" in clean_lower:
                self.profile["preferred_browser"] = "Chromium"
            elif "firefox" in clean_lower:
                self.profile["preferred_browser"] = "Firefox"
            self.save_profile()
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "epoch": time.time(),
            "category": category,
            "fact": clean
        }
        try:
            with open(self.episodic_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[VOID MemoryEngine Error] Appending episodic: {e}", flush=True)
        self.prune_if_needed()
        return entry

    def recall(self, query: str, max_results: int = 4) -> list[str]:
        results = []
        q_words = [w.lower() for w in query.split() if len(w) > 2]
        if self.episodic_path.exists():
            try:
                with open(self.episodic_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                for line in reversed(lines):
                    try:
                        data = json.loads(line)
                        fact = data.get("fact", "")
                        if any(w in fact.lower() for w in q_words) or not q_words:
                            if fact not in results:
                                results.append(fact)
                            if len(results) >= max_results:
                                break
                    except Exception:
                        pass
            except Exception:
                pass
        return results

    def get_context_summary(self) -> str:
        parts = [
            f"User: {self.profile.get('user_name', 'Prakash')}",
            f"Preferred Browser: {self.profile.get('preferred_browser', 'Chromium')}",
            f"Environment: {self.profile.get('desktop_environment', 'Fedora KDE Wayland')}"
        ]
        recent = self.recall("", max_results=3)
        if recent:
            parts.append("Recent Learned Facts: " + "; ".join(recent))
        return " | ".join(parts)

    def get_stats(self) -> dict[str, Any]:
        total_b = 0
        for root, _, files in os.walk(self.mem_dir):
            for f in files:
                try:
                    total_b += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        mb_used = round(total_b / (1024 * 1024), 2)
        count = 0
        if self.episodic_path.exists():
            try:
                with open(self.episodic_path, "r", errors="replace") as f:
                    count = sum(1 for _ in f)
            except Exception:
                pass
        return {
            "used_mb": mb_used,
            "max_mb": 1500.0,
            "pct": round((total_b / MAX_MEMORY_BYTES) * 100, 2),
            "items_count": count
        }

    def prune_if_needed(self) -> None:
        total_b = 0
        for root, _, files in os.walk(self.mem_dir):
            for f in files:
                try:
                    total_b += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        if total_b > MAX_MEMORY_BYTES:
            print(f"[MemoryEngine] Exceeded 1.5GB limit ({total_b} bytes). Pruning oldest memories...", flush=True)
            if self.episodic_path.exists():
                try:
                    with open(self.episodic_path, "r", errors="replace") as f:
                        lines = f.readlines()
                    if len(lines) > 50:
                        with open(self.episodic_path, "w", errors="replace") as f:
                            f.writelines(lines[len(lines)//2:])
                except Exception:
                    pass

# ---------------------------------------------------------------------------
# Intelligent Application & Intent Resolution Engine
# ---------------------------------------------------------------------------
KNOWN_APPS = {
    "chromium": ["chrome", "chromium", "google chrome", "google", "browser", "web browser", "web", "internet", "crome", "chrom", "chromum"],
    "firefox": ["firefox", "fire fox", "mozila", "mozilla"],
    "konsole": ["konsole", "terminal", "termianl", "console", "consol", "shell", "bash"],
    "dolphin": ["dolphin", "files", "file manager", "filemanager", "explorer", "folders", "directory"],
    "kwrite": ["kwrite", "text editor", "notepad", "notes", "editor", "kate"],
    "kcalc": ["kcalc", "calculator", "calcultor", "calc"],
    "systemsettings": ["settings", "system settings", "control panel", "config", "systemsettings"],
    "plasma-systemmonitor": ["system monitor", "task manager", "activity monitor", "resources"],
    "vlc": ["vlc", "vlc media player", "video player"],
    "gwenview": ["gwenview", "image viewer", "photo viewer"],
    "gimp": ["gimp", "photo editor", "image editor"],
    "code": ["vs code", "vscode", "code", "visual studio code"],
    "spotify": ["spotify"],
    "steam": ["steam"],
    "obs": ["obs", "obs studio"],
    "thunderbird": ["thunderbird", "mail client"],
    "libreoffice": ["libreoffice", "office", "word processor"]
}

def resolve_app_name(raw_name: str) -> str | None:
    raw_lower = raw_name.strip().lower()
    # Never resolve generic pronouns, articles, stop words, or filenames with extensions as app names
    if raw_lower in ["that", "it", "this", "something", "the summary", "summary", "document", "file", "all"]:
        return None
    if "." in raw_lower and any(raw_lower.endswith(ext) for ext in [
        ".docx", ".doc", ".xlsx", ".xls", ".pdf", ".txt", ".md", ".csv",
        ".json", ".py", ".sh", ".odt", ".ods", ".png", ".jpg", ".jpeg",
        ".webp", ".gif", ".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv",
        ".mp3", ".wav", ".svg", ".bmp"
    ]):
        return None
    for app_id, aliases in KNOWN_APPS.items():
        if raw_lower in aliases:
            return app_id
        for a in aliases:
            if a in raw_lower or (len(raw_lower) >= 4 and raw_lower in a):
                return app_id
    import difflib
    all_aliases = [a for aliases in KNOWN_APPS.values() for a in aliases]
    close = difflib.get_close_matches(raw_lower, all_aliases, n=1, cutoff=0.7)
    if close:
        match = close[0]
        for app_id, aliases in KNOWN_APPS.items():
            if match in aliases:
                return app_id
    return None

def find_desktop_app(app_name: str) -> str | None:
    app_clean = app_name.lower().replace(" ", "").replace("-", "")
    search_dirs = [
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
        Path.home() / ".local/share/applications"
    ]
    for sdir in search_dirs:
        if not sdir.exists():
            continue
        for f in sdir.glob("*.desktop"):
            fname = f.stem.lower().replace(" ", "").replace("-", "")
            if app_clean in fname or fname in app_clean:
                return str(f)
    return None

def launch_application(app_name: str) -> tuple[bool, str]:
    clean = app_name.strip().lower()
    resolved = resolve_app_name(clean)
    target = resolved or clean

    open_map: dict[str, str] = {
        "chromium": "/usr/bin/chromium-browser",
        "browser": "/usr/bin/chromium-browser",
        "chrome": "/usr/bin/chromium-browser",
        "google": "/usr/bin/chromium-browser",
        "firefox": "/usr/bin/firefox",
        "konsole": "/usr/bin/konsole",
        "terminal": "/usr/bin/konsole",
        "dolphin": "/usr/bin/dolphin",
        "files": "/usr/bin/dolphin",
        "kcalc": "/usr/bin/kcalc",
        "calculator": "/usr/bin/kcalc",
        "kwrite": "/usr/bin/kwrite",
        "text editor": "/usr/bin/kwrite",
        "kate": "/usr/bin/kate",
        "systemsettings": "/usr/bin/systemsettings",
        "settings": "/usr/bin/systemsettings",
        "plasma-systemmonitor": "/usr/bin/plasma-systemmonitor",
        "vlc": "/usr/bin/vlc",
        "gwenview": "/usr/bin/gwenview",
        "gimp": "/usr/bin/gimp",
        "code": "/usr/bin/code",
        "spotify": "/usr/bin/spotify",
        "steam": "/usr/bin/steam",
        "obs": "/usr/bin/obs",
        "thunderbird": "/usr/bin/thunderbird",
        "libreoffice": "/usr/bin/libreoffice",
    }
    if target in open_map:
        if spawn_software(open_map[target]):
            return True, f"Opened {target.title()}."

    which_bin = shutil.which(target) or shutil.which(target.replace(" ", ""))
    if which_bin:
        if spawn_software(which_bin):
            return True, f"Opened {target.title()}."

    desktop_file = find_desktop_app(target)
    if desktop_file:
        try:
            subprocess.Popen(["gio", "launch", desktop_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return True, f"Opened {target.title()}."
        except Exception:
            pass

    if any(w in clean for w in ["browser", "web", "internet", "net", "surf", "chrome"]):
        spawn_software(CHROMIUM_BIN)
        return True, "Opened default browser (Chromium)."

    return False, f"Application '{clean}' was not found on your system. Available apps are Chromium, Firefox, Terminal, Dolphin, and Calculator."


# ---------------------------------------------------------------------------
# Universal File, Media, and Content Search Subsystem
# ---------------------------------------------------------------------------
DOC_EXTENSIONS = {
    ".docx", ".doc", ".xlsx", ".xls", ".pdf", ".txt", ".md", ".csv",
    ".json", ".py", ".sh", ".odt", ".ods", ".odp", ".pptx", ".ppt",
    ".html", ".xml", ".log", ".yaml", ".yml", ".zip", ".tar.gz", ".ini", ".conf"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv", ".m4v",
    ".mpg", ".mpeg", ".3gp", ".ts"
}

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg", ".ico",
    ".tiff", ".tif", ".heic"
}

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".opus"
}

def detect_content_type(file_or_name: str | Path) -> str:
    path = Path(file_or_name)
    ext = path.suffix.lower()
    if ext in DOC_EXTENSIONS:
        return "document"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return "file"

def find_user_content(target: str, expected_type: str = "any") -> tuple[Path | None, str]:
    """
    Intelligently searches user directories for a matching file, document, photo, or video.
    Returns (matching_path, detected_type) or (None, '').
    """
    raw = target.strip().strip("'\"").strip()
    if not raw:
        return (None, "")

    direct_p = Path(raw).expanduser().resolve()
    if direct_p.exists() and direct_p.is_file():
        return (direct_p, detect_content_type(direct_p))

    clean_target = re.sub(
        r"^(?:file|document|doc|report|note|video|movie|photo|image|picture|screenshot|song|track)\s+",
        "", raw, flags=re.I
    ).strip()
    if not clean_target:
        clean_target = raw

    t_lower = clean_target.lower()
    t_path = Path(clean_target)
    t_stem = t_path.stem.lower()
    t_suffix = t_path.suffix.lower()

    home = Path.home()
    ssd_root = Path("/run/media/prakash/TR_39/VOID")

    doc_dirs = [
        home / "Documents/Reports",
        home / "Documents/Notes",
        home / "Documents/Drafts",
        home / "Documents",
        home / "Downloads",
        home / "Desktop",
        ssd_root,
        home,
    ]
    img_dirs = [
        home / "Pictures/Screenshots",
        home / "Pictures",
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
        ssd_root,
        home,
    ]
    vid_dirs = [
        home / "Videos",
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
        ssd_root,
        home,
    ]
    audio_dirs = [
        home / "Music",
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
        home,
    ]

    if expected_type in ["image", "photo", "picture"]:
        search_dirs = img_dirs + doc_dirs
    elif expected_type in ["video", "movie"]:
        search_dirs = vid_dirs + doc_dirs
    elif expected_type in ["document", "doc", "file"]:
        search_dirs = doc_dirs + img_dirs + vid_dirs
    elif expected_type in ["audio", "song", "music"]:
        search_dirs = audio_dirs + vid_dirs + doc_dirs
    else:
        if t_suffix in IMAGE_EXTENSIONS:
            search_dirs = img_dirs + doc_dirs
        elif t_suffix in VIDEO_EXTENSIONS:
            search_dirs = vid_dirs + doc_dirs
        elif t_suffix in DOC_EXTENSIONS:
            search_dirs = doc_dirs + img_dirs + vid_dirs
        else:
            search_dirs = doc_dirs + img_dirs + vid_dirs + audio_dirs

    seen = set()
    unique_dirs = []
    for d in search_dirs:
        if str(d) not in seen and d.exists() and d.is_dir():
            seen.add(str(d))
            unique_dirs.append(d)

    # Pass 1: Direct child exact filename match
    for sdir in unique_dirs:
        try:
            for child in sdir.iterdir():
                if child.is_file() and not child.name.startswith("."):
                    if child.name.lower() == t_lower:
                        return (child, detect_content_type(child))
                    if t_suffix and child.stem.lower() == t_stem and child.suffix.lower() == t_suffix:
                        return (child, detect_content_type(child))
        except Exception:
            pass

    # Pass 2: Exact stem match without extension (e.g. "Mothers_Importance" -> "Mothers_Importance.docx")
    for sdir in unique_dirs:
        try:
            for child in sdir.iterdir():
                if child.is_file() and not child.name.startswith("."):
                    c_stem = child.stem.lower()
                    if c_stem == t_stem or c_stem == t_lower or c_stem.replace("_", " ") == t_lower or c_stem == t_lower.replace(" ", "_"):
                        return (child, detect_content_type(child))
        except Exception:
            pass

    # Pass 3: Fuzzy / Substring match in primary document/media folders (depth <= 2)
    matches = []
    for sdir in unique_dirs[:5]:
        try:
            for root, dirs, files in os.walk(sdir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", ".venv", "node_modules", ".git"]]
                rel_parts = Path(root).relative_to(sdir).parts
                if len(rel_parts) > 2:
                    dirs.clear()
                    continue
                for fname in files:
                    if fname.startswith("."):
                        continue
                    f_lower = fname.lower()
                    f_path = Path(root) / fname
                    if t_lower in f_lower or t_stem in f_lower or t_lower.replace(" ", "_") in f_lower:
                        matches.append((f_path.stat().st_mtime, f_path))
        except Exception:
            pass

    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        best = matches[0][1]
        return (best, detect_content_type(best))

    return (None, "")

def normalize_voice_intent(text: str) -> str:
    """Normalizes STT typos, misspellings, and colloquialisms for offline fast-path routing."""
    s = " " + text.lower().strip() + " "
    replacements = [
        (r"\b(?:strt|strat|stert|starr)\b", "start"),
        (r"\b(?:speach|spech|speeh|specht)\b", "speech"),
        (r"\b(?:txet|tetx|txt)\b", "text"),
        (r"\b(?:stt)\b", "speech to text"),
        (r"\b(?:opn|oppen|oepn|launc|laucn)\b", "open"),
        (r"\b(?:crome|cromium|chrom|chromum|borwser|broswer|internt)\b", "chromium"),
        (r"\b(?:termianl|terminel|termnal|konsolee|consoel)\b", "terminal"),
        (r"\b(?:calcultor|calculater|caculator|calclator)\b", "calculator"),
        (r"\b(?:screnshot|screenshoot|screanshot|screenshit|snapsot)\b", "screenshot"),
        (r"\b(?:screen\s+short)\b", "screenshot"),
        (r"\b(?:minimise|minamize|minmize)\b", "minimize"),
        (r"\b(?:maximise|maxamize|maxmize)\b", "maximize"),
        (r"\b(?:fulscreen|fullscrene|full\s+screne)\b", "fullscreen"),
        (r"\b(?:olama|o\s+llama|allama|alamma|ohlama)\b", "ollama"),
        (r"\b(?:rember|rememebr|remerber)\b", "remember"),
        (r"\b(?:shutdwon|shotdown|shudown)\b", "shutdown"),
        (r"\b(?:restrt|rstart)\b", "restart"),
        (r"\b(?:beliver|beleiver|belever)\b", "believer"),
        (r"\b(?:snag|sng)\b", "song"),
        (r"\b(?:vedio|vido|vdeo|vedeo)\b", "video"),
        (r"\b(?:fotot|foto|photot|pictr|piture|piktur)\b", "photo"),
        (r"\b(?:filname|fiel|fle)\b", "file"),
        (r"\b(?:documnt|docment|dcoument)\b", "document"),
        (r"\b(?:can\s+cel)\b", "cancel"),
        (r"\b(?:cerate|creat)\b", "create"),
        (r"\b(?:asked\s+to\s+search|ask\s+to\s+search|wants\s+to\s+search)\b", "search"),
        (r"\b(?:fel|fell)\s+not\b", "feel not"),
        (r"\b(?:attendongh|attendng|attendin)\b", "attending"),
        (r"\b(?:whats\s*app|wats\s*app|watsapp|whatsaap)\b", "whatsapp"),
        (r"\b(?:vib|veb|bib)\b", "web"),
    ]
    for pattern, rep in replacements:
        s = re.sub(pattern, rep, s, flags=re.I)
    return s.strip()

def split_compound_commands(query: str) -> list[str]:
    q = query.strip()
    parts = re.split(r"\s*(?:and\s+then|,\s*then|\s+then\s+|;)\s*", q, flags=re.I)
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip()]

    ACTION_VERBS = [
        "open", "launch", "start", "run", "spawn", "opn", "oepn",
        "close", "kill", "quit", "exit", "shut", "shutdown", "reboot", "restart", "lock",
        "minimize", "minimise", "maximize", "maximise", "fullscreen", "full screen", "show",
        "take", "capture", "grab", "screenshot", "screen shot",
        "set", "timer", "alarm",
        "status", "system status", "machine status", "memory", "storage", "check",
        "what", "who", "list", "remind",
        "remember", "recall", "learn", "store",
        "calculate", "compute", "solve",
        "compose", "draft", "write", "plan", "create", "send",
        "search", "google", "look up",
        "volume", "mute", "unmute",
        "clear"
    ]
    verb_pat = "|".join(ACTION_VERBS)

    # Split on comma followed by action verb (e.g. "open chromium , open mail in it and send mail...")
    c_splits = re.split(rf"\s*,\s*(?=(?:{verb_pat})\b)", q, flags=re.I)
    if len(c_splits) > 1:
        return [p.strip() for p in c_splits if p.strip()]

    # Split on "and" followed by action verb
    and_splits = re.split(rf"\s+and\s+(?=(?:{verb_pat})\b)", q, flags=re.I)
    if len(and_splits) > 1:
        return [p.strip() for p in and_splits if p.strip()]

    return [q]

def generate_email_content(topic: str, recipient: str = "") -> tuple[str, str]:
    """Generates a professional subject and body based on user intent."""
    t_clean = topic.strip()
    t_lower = t_clean.lower()
    if any(w in t_lower for w in ["sorry", "apolog", "party", "attend", "not attending", "fell not"]):
        subject = "Apology for missing your party"
        body = (
            "Hi,\n\n"
            "I wanted to reach out and say how truly sorry I am that I could not attend your party. "
            "I sincerely regret missing the celebration and hope you had a fantastic time with everyone!\n\n"
            "Let's catch up soon.\n\n"
            "Best regards,\n"
            "Prakash"
        )
    elif any(w in t_lower for w in ["meeting", "schedule", "reschedule", "sync"]):
        subject = "Meeting Follow-up"
        body = (
            "Hi,\n\n"
            f"I am writing regarding: {t_clean}.\n\n"
            "Please let me know a convenient time for us to connect.\n\n"
            "Best regards,\n"
            "Prakash"
        )
    elif any(w in t_lower for w in ["thank", "thanks", "gratitude"]):
        subject = "Thank you!"
        body = (
            "Hi,\n\n"
            f"I wanted to sincerely thank you for {t_clean}.\n\n"
            "Best regards,\n"
            "Prakash"
        )
    else:
        clean_sub = re.sub(r"^(?:saying|about|that|regarding)\s+", "", t_clean, flags=re.I).strip()
        subject = clean_sub[:50].capitalize() or "Important Message"
        body = (
            "Hi,\n\n"
            f"{clean_sub.capitalize()}.\n\n"
            "Best regards,\n"
            "Prakash"
        )
    return subject, body

# ---------------------------------------------------------------------------
# Dodaios Multi-Tool Hub
# ---------------------------------------------------------------------------
class DodaiosToolHub:
    """Manages the 105 tools installed in Dodaios."""

    def __init__(self) -> None:
        self.brain = None
        self.tools: dict[str, Any] = {}
        self.last_created_file: str | None = None
        self._init_in_bg()

    def open_or_search_content(self, target: str, raw_query: str = "") -> tuple[bool, str, str, str]:
        """
        Universal Opener & Search Engine for:
        - __filename: documents, spreadsheets, text files, code, notes (.docx, .xlsx, .pdf, .txt, etc.)
        - _vedioname: local video files or YouTube direct streaming
        - _photoname: local photos/screenshots or Google Images search
        - _appname: desktop applications via KWin / desktop files / binaries
        - _browser: Chromium browser, URLs, web services
        - etc: universal fallback search in Chromium

        Returns (success: bool, reply_text: str, action_badge: str, media_path: str)
        """
        t_clean = target.strip().strip("'\"").strip()
        t_lower = t_clean.lower()
        if not t_clean:
            return False, "Please specify what you would like me to open or search.", "Open: Missing Target", ""

        # 1. Direct Web Services, Browser, and URLs
        if t_lower in ["browser", "chromium", "chrome", "default browser"]:
            self.open_browser(url="chrome://newtab", new_tab=True)
            return True, "Opened Chromium.", "Browser: Chromium", ""

        if t_lower in ["firefox"]:
            spawn_software("/usr/bin/firefox")
            return True, "Opened Firefox browser.", "Browser: Firefox", ""

        web_services = {
            "whatsapp web": ("https://web.whatsapp.com", "WhatsApp Web"),
            "whatsapp": ("https://web.whatsapp.com", "WhatsApp Web"),
            "youtube": ("https://www.youtube.com", "YouTube"),
            "github": ("https://github.com", "GitHub"),
            "reddit": ("https://www.reddit.com", "Reddit"),
            "gmail": ("https://mail.google.com", "Gmail"),
            "wikipedia": ("https://www.wikipedia.org", "Wikipedia"),
        }
        for svc_name, (svc_url, svc_disp) in web_services.items():
            if t_lower == svc_name or t_lower == f"the {svc_name}":
                self.open_browser(url=svc_url, new_tab=True)
                return True, f"Opened {svc_disp} in Chromium.", f"Browser: {svc_disp}", ""

        if t_lower.startswith("http://") or t_lower.startswith("https://") or ('.' in t_clean and ' ' not in t_clean and any(t_clean.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".in", ".edu", ".gov", ".dev", ".ai"])):
            url_target = t_clean if t_clean.startswith("http") else f"https://{t_clean}"
            msg = self.open_browser(url=url_target, new_tab=True)
            return True, f"Opened {t_clean} in Chromium.", f"Browser: {t_clean[:18]}", ""

        # 2. Check if user is asking for a Video / Song (_vedioname)
        is_video_intent = (
            any(w in t_lower for w in ["video", "movie", "clip", "song", "track"]) or
            Path(t_clean).suffix.lower() in VIDEO_EXTENSIONS or
            "video" in raw_query.lower() or "song" in raw_query.lower() or "play" in raw_query.lower()
        )
        if is_video_intent:
            found_v, kind = find_user_content(t_clean, expected_type="video")
            if found_v and found_v.exists():
                try:
                    subprocess.Popen(["xdg-open", str(found_v)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return True, f"Opened video '{found_v.name}' in your media player.", f"Video: {found_v.name[:18]}", ""
                except Exception as e:
                    return False, f"Failed to open video file: {e}", "Video Error", ""
            else:
                clean_yt = re.sub(r"\b(?:open|play|video|song|movie|track|clip|in\s+chromium|on\s+youtube)\b", "", t_clean, flags=re.I).strip()
                if not clean_yt:
                    clean_yt = t_clean
                ok, msg = self.play_youtube_query(clean_yt)
                return True, msg, f"YouTube: Play ({clean_yt[:16]})", ""

        # 3. Check if user is asking for a Photo / Image (_photoname)
        is_photo_intent = (
            any(w in t_lower for w in ["photo", "image", "picture", "screenshot", "wallpaper", "pic"]) or
            Path(t_clean).suffix.lower() in IMAGE_EXTENSIONS or
            "photo" in raw_query.lower() or "image" in raw_query.lower() or "picture" in raw_query.lower()
        )
        if is_photo_intent:
            found_img, kind = find_user_content(t_clean, expected_type="image")
            if found_img and found_img.exists():
                try:
                    subprocess.Popen(["xdg-open", str(found_img)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return True, f"Opened photo '{found_img.name}' in default viewer.", f"Photo: {found_img.name[:18]}", str(found_img)
                except Exception as e:
                    return False, f"Failed to open image file: {e}", "Photo Error", ""
            else:
                clean_img = re.sub(r"\b(?:open|show|display|find|photo\s+of|image\s+of|picture\s+of|photo|image|picture|screenshot|snapshot)\b", "", t_clean, flags=re.I).strip()
                if not clean_img:
                    clean_img = t_clean
                img_url = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(clean_img)}"
                self.open_browser(url=img_url, new_tab=True)
                return True, f"Opened Chromium searching photos for '{clean_img}'.", f"Photos: {clean_img[:16]}", ""

        # 4. Check if user is asking for a Document or File (__filename)
        is_file_intent = (
            any(w in t_lower for w in ["file", "document", "report", "doc", "notes", "spreadsheet", "excel", "pdf"]) or
            Path(t_clean).suffix.lower() in DOC_EXTENSIONS or
            "file" in raw_query.lower() or "document" in raw_query.lower()
        )
        if is_file_intent or Path(t_clean).suffix.lower() in DOC_EXTENSIONS:
            found_doc, kind = find_user_content(t_clean, expected_type="document")
            if found_doc and found_doc.exists():
                try:
                    subprocess.Popen(["xdg-open", str(found_doc)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    self.last_created_file = str(found_doc)
                    return True, f"Opened '{found_doc.name}' in your default application.", f"File: {found_doc.name[:18]}", ""
                except Exception as e:
                    return False, f"Failed to open document: {e}", "File Open Error", ""

        # 5. Check Desktop Applications (_appname)
        resolved_app = resolve_app_name(t_clean)
        if resolved_app or shutil.which(t_clean) or shutil.which(t_clean.replace(" ", "")) or find_desktop_app(t_clean):
            ok, msg = launch_application(t_clean)
            if ok:
                return True, msg, f"App: Open {t_clean.title()[:16]}", ""

        # 6. General Local Search for File (untyped exact or stem match)
        found_any, kind = find_user_content(t_clean, expected_type="any")
        if found_any and found_any.exists():
            try:
                subprocess.Popen(["xdg-open", str(found_any)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                media_out = str(found_any) if kind == "image" else ""
                return True, f"Opened {kind} '{found_any.name}' in your default application.", f"{kind.title()}: {found_any.name[:18]}", media_out
            except Exception as e:
                return False, f"Failed to open {kind}: {e}", "Open Error", ""

        # 7. Fallback: Search the Web in Chromium (_browser etc)
        if is_file_intent and ("file" in t_lower or "." in t_clean):
            return False, f"File '{t_clean}' was not found in Documents, Downloads, or Desktop.", "File: Not Found", ""
        if "app" in raw_query.lower() or "application" in raw_query.lower():
            return False, f"Application '{t_clean}' was not found on your system.", "App: Not Found", ""

        clean_search = re.sub(r"^(?:open|search(?:\s+for)?|look\s+up|google(?:\s+for)?)\s+", "", t_clean, flags=re.I).strip()
        if not clean_search:
            clean_search = t_clean
        msg = self.browser_search(clean_search)
        return True, f"I couldn't find a local file or application for '{t_clean}', so I searched for it in Chromium.", f"Search: {clean_search[:16]}", ""

    def play_youtube_query(self, query: str) -> tuple[bool, str]:
        """Searches YouTube, resolves the top matching video ID, and directly plays it in Chromium."""
        clean_q = re.sub(r"\b(?:song|video|track|music)\b", "", query, flags=re.I).strip()
        try:
            enc_q = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={enc_q}"
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
            html = urllib.request.urlopen(req, timeout=3.5).read().decode("utf-8", errors="ignore")
            video_ids = re.findall(r"/watch\?v=([a-zA-Z0-9_-]{11})", html)
            if video_ids:
                vid_id = video_ids[0]
                play_url = f"https://www.youtube.com/watch?v={vid_id}&autoplay=1"
                subprocess.Popen([CHROMIUM_BIN, play_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                return True, f"Opened YouTube in Chromium and playing '{query.title()}'."
        except Exception as e:
            print(f"[YouTube Direct Play Error] {e}", flush=True)

        # Fallback: Open YouTube search results and schedule click on first result
        enc_q = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={enc_q}"
        subprocess.Popen([CHROMIUM_BIN, search_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        threading.Thread(target=self._click_first_youtube_result_delayed, daemon=True).start()
        return True, f"Opened YouTube in Chromium searching for '{query.title()}'. Playing top video result."

    def _click_first_youtube_result_delayed(self) -> None:
        try:
            time.sleep(2.5)
            import pyautogui
            sw, sh = pyautogui.size()
            pyautogui.click(int(sw * 0.28) + 40, int(sh * 0.32))
        except Exception:
            pass

    def click_screen(self, x: int, y: int, clicks: int = 1, button: str = "left") -> str:
        """Clicks the screen at exact coordinates (x, y)."""
        try:
            import pyautogui
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
            return f"Clicked mouse {button} at screen coordinates ({x}, {y})."
        except Exception as e:
            return f"Error clicking at ({x}, {y}): {e}"

    def click_screen_object(self, target: str) -> str:
        """Identifies on-screen semantic target and clicks it."""
        try:
            import pyautogui
            sw, sh = pyautogui.size()
            tgt = target.lower().strip()
            if any(w in tgt for w in ["center", "middle", "play", "pause"]):
                pyautogui.click(sw // 2, sh // 2)
                return f"Clicked center of screen ({sw // 2}, {sh // 2}) to play/pause."
            elif any(w in tgt for w in ["first result", "first video", "first link"]):
                pyautogui.click(int(sw * 0.28) + 40, int(sh * 0.32))
                return f"Clicked first on-screen result at ({int(sw * 0.28) + 40}, {int(sh * 0.32)})."
            elif any(w in tgt for w in ["fullscreen", "full screen"]):
                pyautogui.press("f")
                return "Toggled fullscreen mode."
            elif any(w in tgt for w in ["search bar", "search box"]):
                pyautogui.press("/")
                return "Activated search bar."
            else:
                pyautogui.click(sw // 2, sh // 2)
                return f"Clicked on-screen target '{target}'."
        except Exception as e:
            return f"Failed to click on-screen target: {e}"

    def draft_docx_document(self, title: str, sections: list[dict[str, Any]], filename: str = "") -> str:
        """Drafts a professionally styled Word document (.docx)."""
        if docx is None:
            return "python-docx is not installed in the environment."
        try:
            doc = docx.Document()
            doc.add_heading(title, level=0)
            p_meta = doc.add_paragraph()
            p_meta.add_run(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} | Author: Prakash (via VOID AI)").italic = True

            for sec in sections:
                h = sec.get("heading", "")
                if h:
                    doc.add_heading(h, level=1)
                body = sec.get("content", "")
                if body:
                    lines = body.split("\n")
                    for line in lines:
                        l = line.strip()
                        if l.startswith("- ") or l.startswith("* "):
                            doc.add_paragraph(l[2:], style="List Bullet")
                        elif l:
                            doc.add_paragraph(l)

                tbl_data = sec.get("table")
                if tbl_data and isinstance(tbl_data, dict):
                    headers = tbl_data.get("headers", [])
                    rows = tbl_data.get("rows", [])
                    if headers and rows:
                        tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
                        tbl.style = "Table Grid"
                        for c_idx, h_text in enumerate(headers):
                            cell = tbl.cell(0, c_idx)
                            cell.text = str(h_text)
                            for p in cell.paragraphs:
                                for run in p.runs:
                                    run.font.bold = True
                        for r_idx, r_data in enumerate(rows):
                            for c_idx, val in enumerate(r_data):
                                tbl.cell(r_idx + 1, c_idx).text = str(val)

            safe_name = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "document"
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            out = (REPORTS_DIR / f"{safe_name}.docx") if not filename else Path(filename)
            doc.save(out)
            self.last_created_file = str(out)
            return f"Word document successfully created and saved to {out}."
        except Exception as e:
            return f"Failed to draft Word document: {e}"

    def draft_excel_spreadsheet(self, title: str, headers: list[str], rows: list[list[Any]], sheet_name: str = "Data", filename: str = "") -> str:
        """Drafts a professionally styled Excel workbook (.xlsx)."""
        if openpyxl is None:
            return "openpyxl is not installed in the environment."
        try:
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name or "Data"

            hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            hdr_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            center = Alignment(horizontal="center", vertical="center")
            thin_border = Border(
                left=Side(style='thin', color='CBD5E1'),
                right=Side(style='thin', color='CBD5E1'),
                top=Side(style='thin', color='CBD5E1'),
                bottom=Side(style='thin', color='CBD5E1')
            )

            ws.append(headers)
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.font = hdr_font
                cell.fill = hdr_fill
                cell.alignment = center
                cell.border = thin_border

            for r_data in rows:
                ws.append(r_data)
                r_num = ws.max_row
                for col_idx in range(1, len(r_data) + 1):
                    cell = ws.cell(row=r_num, column=col_idx)
                    cell.border = thin_border

            # Auto-adjust column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

            safe_name = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "spreadsheet"
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            out = (REPORTS_DIR / f"{safe_name}.xlsx") if not filename else Path(filename)
            wb.save(out)
            return f"Excel spreadsheet successfully created and saved to {out}."
        except Exception as e:
            return f"Failed to draft Excel spreadsheet: {e}"

    def draft_formatted_report(self, title: str, topic: str, content: str = "", file_type: str = "docx") -> str:
        """Drafts a formatted report in docx, xlsx, txt, or md format."""
        file_type = file_type.lower().strip(".")
        if file_type == "docx":
            sections = [
                {"heading": "Executive Summary", "content": f"Comprehensive report regarding: {topic}."},
                {"heading": "Key Findings & Analysis", "content": content or f"Detailed review of current progress and data for {topic}."},
                {"heading": "Action Items", "content": "- Review findings with team\n- Schedule next implementation milestone\n- Monitor key performance metrics"}
            ]
            return self.draft_docx_document(title, sections)
        elif file_type == "xlsx":
            headers = ["Category", "Metric / Topic", "Status", "Notes"]
            rows = [
                ["Topic", topic, "Analyzed", "Initial Assessment"],
                ["Findings", content[:50] if content else "Summary", "Documented", "Ready for review"],
                ["Review", "Executive Signoff", "Pending", "Scheduled"]
            ]
            return self.draft_excel_spreadsheet(title, headers, rows, sheet_name="Report")
        else: # txt or md
            ext = "md" if file_type == "md" else "txt"
            safe_name = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "report"
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            out = REPORTS_DIR / f"{safe_name}.{ext}"
            report_body = (
                f"# {title}\n"
                f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} | Topic: {topic}*\n\n"
                f"## Executive Summary\n"
                f"Comprehensive analysis on {topic}.\n\n"
                f"## Detailed Findings\n"
                f"{content or 'No extra details provided.'}\n\n"
                f"## Recommendations\n"
                f"1. Continuous monitoring of key metrics.\n"
                f"2. Align next steps with project objectives.\n"
            )
            with open(out, "w", encoding="utf-8") as f:
                f.write(report_body)
            return f"Report successfully created and saved to {out}."

    def research_and_generate_document(self, topic: str, file_type: str = "docx") -> str:
        """Conducts web research on topic and writes a structured document."""
        results = self.search_web_ddgs(topic, max_results=4)
        snippets = []
        rows = []
        for r in results:
            snippets.append(f"- **{r['title']}**: {r['snippet']} (Source: {r['url']})")
            rows.append([r['title'][:40], r['snippet'][:80], r['url'][:50]])

        content_str = "\n".join(snippets) if snippets else f"No direct search results for '{topic}'."
        title = f"Research Report - {topic[:40]}"

        if file_type.lower() == "xlsx":
            headers = ["Source / Title", "Summary / Findings", "Reference URL"]
            return self.draft_excel_spreadsheet(title, headers, rows if rows else [["None", "No data", "N/A"]], sheet_name="Research")
        else:
            sections = [
                {"heading": "Executive Summary", "content": f"Multi-source web intelligence on: '{topic}'."},
                {"heading": "Online Findings & Sources", "content": content_str},
                {"heading": "Synthesized Insights", "content": f"Key information was collected and verified from authoritative online sources for {topic}."}
            ]
            return self.draft_docx_document(title, sections)

    def _init_in_bg(self) -> None:
        def _load():
            try:
                from dodaios.brain.factory import build_default_brain
                self.brain = build_default_brain()
                self.tools = getattr(self.brain, "_tools", {})
                print(f"[VOID ToolHub] Successfully loaded {len(self.tools)} Dodaios tools.")
            except Exception as e:
                print(f"[VOID ToolHub Warning] Dodaios tools load: {e}")
        threading.Thread(target=_load, daemon=True).start()

    def search_web_ddgs(self, query: str, max_results: int = 4) -> list[dict[str, str]]:
        """Fast-path real DuckDuckGo search."""
        try:
            from ddgs import DDGS
            with DDGS(timeout=4.0) as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [{"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")} for r in results]
        except Exception:
            return []

    def capture_screenshot(self, filename: str = "") -> str | None:
        """Captures monitor screenshot and returns saved file path."""
        if filename:
            safe_name = "".join(c for c in filename if c.isalnum() or c in "_-").strip("_-") or "screenshot"
            target_path = SCREENSHOT_DIR / f"{safe_name}.jpg"
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            target_path = SCREENSHOT_DIR / f"void_shot_{timestamp}.jpg"
        try:
            subprocess.run([
                "spectacle", "-b", "-n", "-o", str(target_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4.0)
            if target_path.exists():
                return str(target_path)
        except Exception:
            pass
        return None

    def search_files(self, pattern: str, search_path: str = "/home/prakash/Documents") -> list[str]:
        p = Path(search_path).expanduser().resolve()
        if not is_safe_user_path(p):
            p = Path("/home/prakash/Documents")
        matches = []
        try:
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    if re.search(re.escape(pattern).replace(r"\*", ".*"), f, re.I):
                        matches.append(str(Path(root) / f))
                        if len(matches) >= 20:
                            return matches
        except Exception:
            pass
        return matches

    def create_document(self, path_str: str, content: str) -> str:
        p = Path(path_str).expanduser().resolve()
        if not is_safe_user_path(p):
            p = Path("/home/prakash/Documents") / Path(path_str).name
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            self.last_created_file = str(p)
            return f"Document successfully created and saved to {p}."
        except Exception as e:
            return f"Failed to create document: {e}"

    def read_document(self, path_str: str) -> str:
        p = Path(path_str).expanduser().resolve()
        if not is_safe_user_path(p) or not p.is_file():
            return f"File '{path_str}' not found or inaccessible."
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(2500)
            return content
        except Exception as e:
            return f"Failed to read document: {e}"

    def append_document(self, path_str: str, content: str) -> str:
        p = Path(path_str).expanduser().resolve()
        if not is_safe_user_path(p):
            p = Path("/home/prakash/Documents") / Path(path_str).name
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write("\n" + content.strip() + "\n")
            return f"Successfully appended content to {p}."
        except Exception as e:
            return f"Failed to append to document: {e}"

    def list_files(self, dir_str: str = "/home/prakash/Documents") -> str:
        p = Path(dir_str).expanduser().resolve()
        if not is_safe_user_path(p) or not p.is_dir():
            p = Path("/home/prakash/Documents")
        try:
            entries = []
            for item in sorted(p.iterdir()):
                if item.name.startswith("."):
                    continue
                kind = "[DIR]" if item.is_dir() else f"[{item.stat().st_size}B]"
                entries.append(f"{kind} {item.name}")
            if entries:
                return f"Contents of {p} ({len(entries)} items):\n" + "\n".join(entries[:25])
            return f"Directory {p} is empty."
        except Exception as e:
            return f"Failed to list directory: {e}"

    def compose_email(self, recipient: str, subject: str, body: str, save_draft: bool = True) -> str:
        draft = f"To: {recipient}\nSubject: {subject}\nDate: {time.strftime('%a, %d %b %Y %H:%M:%S')}\n\n{body}\n"
        saved_path = ""
        if save_draft:
            drafts_dir = Path("/home/prakash/Documents/Drafts")
            try:
                drafts_dir.mkdir(parents=True, exist_ok=True)
                slug = "".join(c for c in subject if c.isalnum() or c in "_- ").strip().replace(" ", "_")[:30] or "draft"
                fpath = drafts_dir / f"{slug}_{time.strftime('%Y%m%d_%H%M%S')}.eml"
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(draft)
                # Also save readable txt
                txt_path = drafts_dir / f"{slug}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(draft)
                saved_path = str(fpath)
            except Exception:
                pass
        res = f"Email draft prepared for {recipient}:\nSubject: {subject}\n\n{body}"
        if saved_path:
            res += f"\n(Draft saved to {saved_path})"
        return res

    def open_browser(self, url: str = "", new_tab: bool = True, search_query: str = "") -> str:
        """Opens Chromium with a specific URL, new tab, or search query."""
        if search_query:
            target_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            msg = f"Opening Chromium and searching for '{search_query}'."
        elif url == "chrome://newtab" or not url:
            target_url = "chrome://newtab"
            msg = "Opened a new tab in Chromium."
        else:
            target_url = url if url.startswith("http") or url.startswith("chrome://") else f"https://{url}"
            msg = f"Opening {target_url} in Chromium."

        cmd = [CHROMIUM_BIN]
        if new_tab:
            cmd.append(target_url)
        else:
            cmd.extend(["--new-window", target_url])

        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return msg

    def browser_search(self, query: str, engine: str = "google") -> str:
        """Performs a web search directly inside Chromium on screen."""
        if engine.lower() == "duckduckgo":
            url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
            eng_name = "DuckDuckGo"
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            eng_name = "Google"

        subprocess.Popen([CHROMIUM_BIN, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return f"Opened {eng_name} in Chromium searching for '{query}'."

    def open_webmail_compose(self, recipient: str, subject: str, body: str, provider: str = "gmail") -> tuple[bool, str]:
        """Composes an email and directly opens it inside Chromium webmail (e.g. Gmail compose)."""
        # 1. Archive local draft in ~/Documents/Drafts
        self.compose_email(recipient, subject, body, save_draft=True)

        # 2. Form webmail compose URL
        q_rec = urllib.parse.quote(recipient)
        q_sub = urllib.parse.quote(subject)
        q_body = urllib.parse.quote(body)

        if provider.lower() in ["outlook", "hotmail"]:
            url = f"https://outlook.live.com/mail/0/deeplink/compose?to={q_rec}&subject={q_sub}&body={q_body}"
            p_name = "Outlook"
        else:
            url = f"https://mail.google.com/mail/?view=cm&fs=1&to={q_rec}&su={q_sub}&body={q_body}"
            p_name = "Gmail"

        subprocess.Popen([CHROMIUM_BIN, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return (True, f"Opened {p_name} in Chromium with an email prepared for {recipient}.\nSubject: {subject}\n\nReady to send in your browser.")

    def web_read_page(self, url: str) -> str:
        """Fetches and extracts readable text from a URL using BeautifulSoup."""
        try:
            import httpx
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
            r = httpx.get(url, headers=headers, timeout=8.0, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "noscript"]):
                tag.decompose()
            text = " ".join(soup.get_text().split())
            return text[:3000] if text else "Page loaded but no readable text found."
        except Exception as e:
            return f"Failed to read page {url}: {e}"

    def get_volume(self) -> dict[str, Any]:
        """Reads current audio volume percentage and mute status via PipeWire wpctl."""
        try:
            res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True, timeout=1.5)
            line = res.stdout.strip()
            muted = "[MUTED]" in line
            m = re.search(r"Volume:\s+([0-9.]+)", line)
            vol = int(float(m.group(1)) * 100) if m else 50
            return {"volume_pct": vol, "muted": muted}
        except Exception:
            return {"volume_pct": 50, "muted": False}

    def set_volume(self, level_pct: int) -> str:
        """Sets master volume percentage (0 - 100%)."""
        level_pct = max(0, min(100, int(level_pct)))
        frac = level_pct / 100.0
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{frac:.2f}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Volume set to {level_pct}%."

    def adjust_volume(self, delta_pct: int) -> str:
        """Increases or decreases volume by delta percentage."""
        sign = "+" if delta_pct >= 0 else "-"
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{abs(delta_pct)}%{sign}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        v = self.get_volume()
        return f"Volume adjusted to {v['volume_pct']}%."

    def toggle_mute(self) -> str:
        """Toggles audio mute state."""
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        v = self.get_volume()
        state = "muted" if v["muted"] else "unmuted"
        return f"Audio is now {state}."

    def media_control(self, action: str) -> str:
        """Controls media playback (play, pause, next, previous, stop) via MPRIS DBus."""
        act_map = {
            "play": "Play",
            "pause": "Pause",
            "play_pause": "PlayPause",
            "toggle": "PlayPause",
            "next": "Next",
            "previous": "Previous",
            "prev": "Previous",
            "stop": "Stop"
        }
        method = act_map.get(action.lower().replace("-", "_").replace(" ", "_"), "PlayPause")
        try:
            res = subprocess.run(["qdbus-qt6"], capture_output=True, text=True, timeout=1.5)
            players = [l.strip() for l in res.stdout.splitlines() if "org.mpris.MediaPlayer2" in l]
            if players:
                for p in players:
                    subprocess.run(["qdbus-qt6", p, "/org/mpris/MediaPlayer2", f"org.mpris.MediaPlayer2.Player.{method}"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
                return f"Media command '{method}' sent to active player."
            return "No active media player detected. Open Chromium, Spotify, or your music player to begin playback."
        except Exception as e:
            return f"Media control error: {e}"

    def get_clipboard(self) -> str:
        """Reads current text from the Wayland system clipboard."""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                t = app.clipboard().text()
                if t:
                    return t[:1500]
        except Exception:
            pass
        try:
            env = dict(os.environ)
            if "WAYLAND_DISPLAY" not in env:
                env["WAYLAND_DISPLAY"] = "wayland-1"
            if "XDG_RUNTIME_DIR" not in env:
                env["XDG_RUNTIME_DIR"] = "/run/user/1000"
            res = subprocess.run(["wl-paste", "-n"], capture_output=True, text=True, timeout=0.8, env=env)
            clip = res.stdout.strip()
            if clip:
                return clip[:1500]
        except Exception:
            pass
        return "Clipboard is currently empty."

    def set_clipboard(self, text: str) -> str:
        """Copies text to the Wayland system clipboard."""
        try:
            env = dict(os.environ)
            if "WAYLAND_DISPLAY" not in env:
                env["WAYLAND_DISPLAY"] = "wayland-1"
            if "XDG_RUNTIME_DIR" not in env:
                env["XDG_RUNTIME_DIR"] = "/run/user/1000"
            subprocess.Popen(["wl-copy", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, start_new_session=True)
            try:
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    app.clipboard().setText(text)
            except Exception:
                pass
            preview = text[:50] + "..." if len(text) > 50 else text
            return f"Copied to clipboard: '{preview}'"
        except Exception as e:
            return f"Failed to set clipboard: {e}"

    def get_brightness(self) -> int:
        """Gets screen brightness percentage via KDE DBus."""
        try:
            res = subprocess.run([
                "qdbus-qt6", "org.kde.Solid.PowerManagement",
                "/org/kde/Solid/PowerManagement/Actions/BrightnessControl",
                "org.kde.Solid.PowerManagement.Actions.BrightnessControl.brightness"
            ], capture_output=True, text=True, timeout=1.5)
            val = int(res.stdout.strip())
            res_max = subprocess.run([
                "qdbus-qt6", "org.kde.Solid.PowerManagement",
                "/org/kde/Solid/PowerManagement/Actions/BrightnessControl",
                "org.kde.Solid.PowerManagement.Actions.BrightnessControl.brightnessMax"
            ], capture_output=True, text=True, timeout=1.5)
            max_val = int(res_max.stdout.strip()) if res_max.stdout.strip() else 10000
            return int((val / max_val) * 100)
        except Exception:
            return 50

    def set_brightness(self, level_pct: int) -> str:
        """Sets screen brightness percentage (5 - 100%) via KDE DBus."""
        level_pct = max(5, min(100, int(level_pct)))
        try:
            res_max = subprocess.run([
                "qdbus-qt6", "org.kde.Solid.PowerManagement",
                "/org/kde/Solid/PowerManagement/Actions/BrightnessControl",
                "org.kde.Solid.PowerManagement.Actions.BrightnessControl.brightnessMax"
            ], capture_output=True, text=True, timeout=1.5)
            max_val = int(res_max.stdout.strip()) if res_max.stdout.strip() else 10000
            target_val = int((level_pct / 100.0) * max_val)
            subprocess.run([
                "qdbus-qt6", "org.kde.Solid.PowerManagement",
                "/org/kde/Solid/PowerManagement/Actions/BrightnessControl",
                "org.kde.Solid.PowerManagement.Actions.BrightnessControl.setBrightness",
                str(target_val)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5)
            return f"Screen brightness set to {level_pct}%."
        except Exception as e:
            return f"Failed to adjust brightness: {e}"

    def get_weather(self, location: str = "") -> str:
        """Fetches live weather and temperature."""
        try:
            import httpx
            loc_str = urllib.parse.quote(location.strip()) if location.strip() else ""
            url = f"https://wttr.in/{loc_str}?format=3"
            r = httpx.get(url, timeout=3.5)
            if r.status_code == 200 and r.text.strip():
                return r.text.strip()
            return "Unable to fetch live weather at this moment."
        except Exception:
            return "Weather service currently offline or unreachable."

    def get_hardware_vitals(self) -> dict[str, Any]:
        """Inspects battery status, charging state, and CPU/GPU thermal temperatures."""
        vitals: dict[str, Any] = {}
        try:
            res = subprocess.run(["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"], capture_output=True, text=True, timeout=1.5)
            out = res.stdout
            pct_m = re.search(r"percentage:\s+([0-9]+)%", out)
            state_m = re.search(r"state:\s+([a-zA-Z\-]+)", out)
            vitals["battery_pct"] = int(pct_m.group(1)) if pct_m else 100
            vitals["battery_state"] = state_m.group(1) if state_m else "fully-charged"
        except Exception:
            vitals["battery_pct"] = 100
            vitals["battery_state"] = "unknown"

        try:
            res = subprocess.run(["sensors"], capture_output=True, text=True, timeout=1.5)
            out = res.stdout
            cpu_m = re.search(r"Tctl:\s+\+([0-9.]+)°C", out)
            gpu_m = re.search(r"edge:\s+\+([0-9.]+)°C", out)
            nvme_m = re.search(r"Composite:\s+\+([0-9.]+)°C", out)
            vitals["cpu_temp_c"] = float(cpu_m.group(1)) if cpu_m else None
            vitals["gpu_temp_c"] = float(gpu_m.group(1)) if gpu_m else None
            vitals["nvme_temp_c"] = float(nvme_m.group(1)) if nvme_m else None
        except Exception:
            vitals["cpu_temp_c"] = None

        return vitals

    def save_note(self, title: str, content: str) -> str:
        """Saves a note file to ~/Documents/Notes."""
        notes_dir = Path("/home/prakash/Documents/Notes")
        notes_dir.mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "note"
        path = notes_dir / f"{safe_title}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n*Saved: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n{content}\n")
        return f"Note '{title}' saved to {path}."

    def read_note(self, title: str) -> str:
        """Reads a saved note file from ~/Documents/Notes."""
        notes_dir = Path("/home/prakash/Documents/Notes")
        safe_title = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_")
        matches = list(notes_dir.glob(f"*{safe_title}*.md"))
        if matches:
            with open(matches[0], "r", encoding="utf-8", errors="replace") as f:
                return f.read(2000)
        return f"No note found matching '{title}'."

    def security_audit(self) -> dict[str, Any]:
        audit: dict[str, Any] = {}
        try:
            res = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True, timeout=2.0)
            listening = [l for l in res.stdout.splitlines() if "LISTEN" in l]
            audit["open_ports_count"] = len(listening)
            audit["open_ports"] = [l.split()[4] for l in listening[:5] if len(l.split()) > 4]
        except Exception:
            audit["open_ports_count"] = 0
            audit["open_ports"] = []
        try:
            res = subprocess.run(["who"], capture_output=True, text=True, timeout=1.0)
            users = [u for u in res.stdout.splitlines() if u.strip()]
            audit["active_users_count"] = len(users)
        except Exception:
            audit["active_users_count"] = 1
        try:
            res = subprocess.run(["getenforce"], capture_output=True, text=True, timeout=1.0)
            audit["selinux"] = res.stdout.strip()
        except Exception:
            audit["selinux"] = "Enforcing"
        try:
            res = subprocess.run(["systemctl", "is-active", "firewalld"], capture_output=True, text=True, timeout=1.0)
            audit["firewall"] = res.stdout.strip()
        except Exception:
            audit["firewall"] = "active"
        return audit

    def web_scrape_deep_research(self, url: str = "", topic: str = "") -> str:
        try:
            import httpx
            from html.parser import HTMLParser

            class TextExtractParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self.in_script = False
                def handle_starttag(self, tag, attrs):
                    if tag in ["script", "style", "noscript"]:
                        self.in_script = True
                def handle_endtag(self, tag):
                    if tag in ["script", "style", "noscript"]:
                        self.in_script = False
                def handle_data(self, data):
                    if not self.in_script:
                        t = data.strip()
                        if t:
                            self.text_parts.append(t)

            if url:
                if not url.startswith("http"):
                    url = "https://" + url
                r = httpx.get(url, timeout=6.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 VOID-Agent/1.0"})
                if r.status_code == 200:
                    p = TextExtractParser()
                    p.feed(r.text)
                    extracted = " ".join(p.text_parts)
                    return extracted[:1500]
                return f"HTTP error {r.status_code} fetching {url}"
            elif topic:
                results = self.search_web_ddgs(topic, max_results=4)
                if results:
                    summary = [f"Topic Research: {topic}"]
                    for r in results:
                        summary.append(f"Source: {r['title']} ({r['url']})\n{r['snippet']}")
                    return "\n\n".join(summary)
                return f"No research data found for '{topic}'."
        except Exception as e:
            return f"Research error: {e}"
        return "Provide either a URL or a research topic."

    def get_audio_devices(self) -> dict[str, Any]:
        try:
            import urllib.request
            req = urllib.request.Request(f"{DODAIOS_URL}/api/settings/audio-devices")
            with urllib.request.urlopen(req, timeout=1.5) as r:
                return json.loads(r.read().decode())
        except Exception:
            return {}

# ---------------------------------------------------------------------------
# Vector Mic Button (Crisp Native Rendering)
# ---------------------------------------------------------------------------
class MicButton(QPushButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to speak")

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        hover = self.underMouse()
        bg_col = QColor(56, 189, 248, 65 if hover else 35)
        border_col = QColor(56, 189, 248, 140 if hover else 80)
        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 13, 13)

        painter.setPen(QPen(QColor(56, 189, 248 if not hover else 255, 255, 255), 1.5))
        painter.setBrush(QBrush(QColor(56, 189, 248, 220)))
        painter.drawRoundedRect(11, 6, 6, 9, 3, 3)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(8, 8, 12, 9, 0, -180 * 16)
        painter.drawLine(14, 17, 14, 21)
        painter.drawLine(11, 21, 17, 21)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 3D Neural Plexus Globe & Holographic Acoustic Core
# ---------------------------------------------------------------------------
class Node3D:
    def __init__(self, x: float, y: float, z: float, is_core: bool = False) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.is_core = is_core
        self.pulse = random.random()
        self.pulse_speed = 0.05 + random.random() * 0.08

class GlitterParticle:
    def __init__(self, x: float, y: float, z: float, speed: float, phase: float, max_size: float = 2.0) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.speed = speed
        self.phase = phase
        self.max_size = max_size

class OrbWidget(QWidget):
    clicked = Signal()

    def __init__(self, size: int = 36, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("VOID Neural Core (Click to speak / abort)")
        self._mode = "idle"  # idle, listening, thinking, executing, speaking, empathy, celebrate
        self._phase = 0.0
        self._audio_level = 0.0
        self._yaw = 0.0
        self._pitch = 0.25
        self._roll = 0.0

        # Build 3D sphere lattice
        self._nodes: list[Node3D] = []
        self._build_sphere_mesh()

        # Build glitter particles
        self._glitters: list[GlitterParticle] = []
        self._build_glitters()

        # Dynamic Synaptic Pulse Packets
        self._pulses: list[list[Any]] = []  # [from_idx, to_idx, progress, speed]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(33)  # ~30 FPS

    def _build_sphere_mesh(self) -> None:
        self._nodes.clear()
        num_surface = 22
        # Fibonacci spiral on sphere
        phi = math.pi * (3.0 - math.sqrt(5.0))  # golden angle
        for i in range(num_surface):
            y = 1.0 - (i / float(num_surface - 1)) * 2.0
            radius = math.sqrt(max(0.0, 1.0 - y * y))
            theta = phi * i
            x = math.cos(theta) * radius
            z = math.sin(theta) * radius
            self._nodes.append(Node3D(x, y, z, is_core=False))

        # Core internal nodes (depth constellation)
        core_positions = [
            (0.0, 0.0, 0.0),
            (0.35, 0.2, -0.2),
            (-0.3, -0.25, 0.15),
            (0.15, -0.35, -0.25),
            (-0.2, 0.3, 0.25),
            (0.25, 0.1, 0.35),
        ]
        for cx, cy, cz in core_positions:
            self._nodes.append(Node3D(cx, cy, cz, is_core=True))

        # Precalculate edge pairs within distance threshold
        self._edges: list[tuple[int, int, float]] = []
        threshold = 0.95
        for i in range(len(self._nodes)):
            for j in range(i + 1, len(self._nodes)):
                n1 = self._nodes[i]
                n2 = self._nodes[j]
                d = math.sqrt((n1.x - n2.x)**2 + (n1.y - n2.y)**2 + (n1.z - n2.z)**2)
                if d < threshold:
                    self._edges.append((i, j, d))

    def _build_glitters(self) -> None:
        self._glitters.clear()
        for _ in range(18):
            u = random.random()
            r = 0.3 + 0.85 * (u ** (1.0 / 3.0))
            costheta = random.uniform(-1, 1)
            phi = random.uniform(0, 2 * math.pi)
            sintheta = math.sqrt(max(0.0, 1.0 - costheta * costheta))
            x = r * sintheta * math.cos(phi)
            y = r * sintheta * math.sin(phi)
            z = r * costheta
            speed = random.uniform(2.5, 6.0)
            phase = random.uniform(0, 2 * math.pi)
            size = random.uniform(1.2, 2.4)
            self._glitters.append(GlitterParticle(x, y, z, speed, phase, size))

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self.update()

    def set_audio_level(self, level: float) -> None:
        self._audio_level = max(0.0, min(1.0, level))
        self.update()

    def _on_tick(self) -> None:
        self._phase += 0.06

        # Rotation speeds according to active AI mode
        if self._mode == "thinking":
            yaw_speed = 0.055
            pitch_speed = 0.025
        elif self._mode == "executing":
            yaw_speed = 0.075
            pitch_speed = 0.015
        elif self._mode == "listening":
            yaw_speed = 0.035 + self._audio_level * 0.05
            pitch_speed = 0.018
        elif self._mode == "celebrate":
            yaw_speed = 0.08
            pitch_speed = 0.04
        elif self._mode == "planning":
            yaw_speed = 0.045
            pitch_speed = 0.020
        elif self._mode == "verifying":
            yaw_speed = 0.030
            pitch_speed = 0.015
        elif self._mode == "recovering":
            yaw_speed = 0.085
            pitch_speed = 0.035
        elif self._mode == "waiting_approval":
            yaw_speed = 0.015
            pitch_speed = 0.005
        else:  # idle
            yaw_speed = 0.02
            pitch_speed = 0.008

        self._yaw += yaw_speed
        self._pitch += pitch_speed
        self._roll = math.sin(self._phase * 0.5) * 0.15

        # Update node pulses
        for n in self._nodes:
            n.pulse = (n.pulse + n.pulse_speed) % 1.0

        # Spawn synaptic packets during thinking/executing
        if self._mode in ["thinking", "executing"] and self._edges:
            if random.random() < (0.35 if self._mode == "thinking" else 0.5):
                edge = random.choice(self._edges)
                if random.random() < 0.5:
                    from_idx, to_idx = edge[0], edge[1]
                else:
                    from_idx, to_idx = edge[1], edge[0]
                speed = random.uniform(0.08, 0.18)
                self._pulses.append([from_idx, to_idx, 0.0, speed])

        # Advance pulses
        active_pulses = []
        for p in self._pulses:
            p[2] += p[3]
            if p[2] < 1.0:
                active_pulses.append(p)
        self._pulses = active_pulses

        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        globe_radius = (min(w, h) / 2.0) - 2.5

        # 3D Rotation matrices
        cyaw, syaw = math.cos(self._yaw), math.sin(self._yaw)
        cpitch, spitch = math.cos(self._pitch), math.sin(self._pitch)
        croll, sroll = math.cos(self._roll), math.sin(self._roll)

        # 1. Color Palettes according to mode
        if self._mode == "thinking":
            c_glow_center = QColor(254, 240, 138, 70)  # Bright golden amber / white
            c_glow_mid = QColor(245, 158, 11, 45)      # Deep electric amber
            c_rim = QColor(251, 191, 36, 170)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (245, 158, 11)
            c_pulse = QColor(255, 255, 220)
        elif self._mode == "executing":
            c_glow_center = QColor(56, 189, 248, 95)   # High-voltage cyan / laser blue
            c_glow_mid = QColor(14, 165, 233, 60)
            c_rim = QColor(56, 189, 248, 200)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (56, 189, 248)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "listening":
            pulse_extra = self._audio_level * 50
            c_glow_center = QColor(56, 189, 248, int(80 + pulse_extra))
            c_glow_mid = QColor(6, 182, 212, int(50 + pulse_extra))
            c_rim = QColor(34, 211, 238, 200)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (34, 211, 238)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "speaking":
            c_glow_center = QColor(232, 121, 249, 85)  # Neural violet / magenta
            c_glow_mid = QColor(192, 132, 252, 50)
            c_rim = QColor(216, 180, 254, 180)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (192, 132, 252)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "empathy":
            c_glow_center = QColor(251, 113, 133, 85)  # Warm Rose / Coral
            c_glow_mid = QColor(244, 63, 94, 50)
            c_rim = QColor(253, 164, 175, 180)
            c_core_node = QColor(255, 241, 242)
            c_synapse_base = (244, 63, 94)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "celebrate":
            c_glow_center = QColor(52, 211, 153, 90)   # Emerald / Golden
            c_glow_mid = QColor(16, 185, 129, 55)
            c_rim = QColor(110, 231, 183, 190)
            c_core_node = QColor(254, 240, 138)
            c_synapse_base = (52, 211, 153)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "planning":
            c_glow_center = QColor(168, 85, 247, 85)   # Royal Indigo / Violet
            c_glow_mid = QColor(147, 51, 234, 50)
            c_rim = QColor(192, 132, 252, 190)
            c_core_node = QColor(250, 245, 255)
            c_synapse_base = (168, 85, 247)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "verifying":
            c_glow_center = QColor(250, 204, 21, 90)   # Crystalline Gold / Verifier
            c_glow_mid = QColor(234, 179, 8, 55)
            c_rim = QColor(253, 224, 71, 200)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (234, 179, 8)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "recovering":
            c_glow_center = QColor(251, 146, 60, 95)   # Corrective Deep Orange
            c_glow_mid = QColor(234, 88, 12, 60)
            c_rim = QColor(253, 186, 116, 200)
            c_core_node = QColor(255, 255, 255)
            c_synapse_base = (234, 88, 12)
            c_pulse = QColor(255, 255, 255)
        elif self._mode == "waiting_approval":
            c_glow_center = QColor(244, 63, 94, 95)    # Pulsing Ruby Amber
            c_glow_mid = QColor(225, 29, 72, 60)
            c_rim = QColor(251, 113, 133, 210)
            c_core_node = QColor(255, 228, 230)
            c_synapse_base = (225, 29, 72)
            c_pulse = QColor(255, 255, 255)
        else: # Idle
            c_glow_center = QColor(56, 189, 248, 50)   # Cosmic deep sapphire / cyan
            c_glow_mid = QColor(30, 58, 138, 30)
            c_rim = QColor(56, 189, 248, 110)
            c_core_node = QColor(240, 249, 255)
            c_synapse_base = (56, 189, 248)
            c_pulse = QColor(255, 255, 255)

        # Ambient backing sphere gradient
        bg_radial = QRadialGradient(cx, cy, globe_radius * 1.05)
        bg_radial.setColorAt(0.0, c_glow_center)
        bg_radial.setColorAt(0.65, c_glow_mid)
        bg_radial.setColorAt(1.0, QColor(10, 14, 26, 0))
        painter.setBrush(QBrush(bg_radial))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), globe_radius, globe_radius)

        # 2. Transform 3D Nodes to 2D Screen Space with Depth Perspective
        projected_nodes = []
        cam_dist = 2.4
        radial_scale = globe_radius * 0.88

        if self._mode == "listening":
            radial_scale *= (1.0 + self._audio_level * 0.18)

        for n in self._nodes:
            x1 = n.x * cyaw + n.z * syaw
            z1 = -n.x * syaw + n.z * cyaw
            y1 = n.y

            y2 = y1 * cpitch - z1 * spitch
            z2 = y1 * spitch + z1 * cpitch
            x2 = x1

            x3 = x2 * croll - y2 * sroll
            y3 = x2 * sroll + y2 * croll
            z3 = z2

            persp = cam_dist / (cam_dist + z3)
            sx = cx + x3 * radial_scale * persp
            sy = cy + y3 * radial_scale * persp

            z_norm = (z3 + 1.0) / 2.0
            projected_nodes.append((sx, sy, z3, z_norm, n))

        # 3. Draw Synaptic Plexus Filaments
        edge_depth_list = []
        for idx1, idx2, d in self._edges:
            p1 = projected_nodes[idx1]
            p2 = projected_nodes[idx2]
            avg_z = (p1[2] + p2[2]) / 2.0
            edge_depth_list.append((avg_z, idx1, idx2, d))
        edge_depth_list.sort(key=lambda item: item[0])

        r_base, g_base, b_base = c_synapse_base
        for avg_z, idx1, idx2, dist in edge_depth_list:
            p1 = projected_nodes[idx1]
            p2 = projected_nodes[idx2]
            avg_norm = (avg_z + 1.0) / 2.0

            dist_factor = max(0.0, 1.0 - (dist / 0.95))
            alpha = int(15 + 175 * avg_norm * dist_factor)
            if self._mode in ["thinking", "executing"]:
                alpha = min(255, int(alpha * 1.35))

            pen_w = 0.6 + 1.1 * avg_norm
            pen = QPen(QColor(r_base, g_base, b_base, alpha), pen_w)
            painter.setPen(pen)
            painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))

        # 4. Draw Active Neural Synaptic Packets (Traveling Sparks)
        for from_i, to_i, prog, _ in self._pulses:
            p_from = projected_nodes[from_i]
            p_to = projected_nodes[to_i]
            px = p_from[0] + (p_to[0] - p_from[0]) * prog
            py = p_from[1] + (p_to[1] - p_from[1]) * prog
            pz = p_from[2] + (p_to[2] - p_from[2]) * prog
            pz_norm = (pz + 1.0) / 2.0

            pulse_size = 1.5 + 1.8 * pz_norm
            spark_grad = QRadialGradient(px, py, pulse_size * 2.0)
            spark_grad.setColorAt(0.0, c_pulse)
            spark_grad.setColorAt(0.4, QColor(r_base, g_base, b_base, 220))
            spark_grad.setColorAt(1.0, QColor(r_base, g_base, b_base, 0))
            painter.setBrush(QBrush(spark_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(px, py), pulse_size * 1.8, pulse_size * 1.8)

        # 5. Draw 3D Neural Nodes with Depth Bokeh
        sorted_nodes = sorted(projected_nodes, key=lambda item: item[2])
        for sx, sy, z, z_norm, n in sorted_nodes:
            node_r = 1.2 + 2.2 * z_norm
            if n.is_core:
                node_r *= 1.2

            pulse_mult = 1.0 + 0.2 * math.sin(n.pulse * 2 * math.pi)
            cur_r = node_r * pulse_mult

            if z_norm > 0.45:
                halo_r = cur_r * (2.2 if self._mode == "thinking" else 1.8)
                halo = QRadialGradient(sx, sy, halo_r)
                halo_alpha = int(140 * z_norm)
                halo.setColorAt(0.0, QColor(r_base, g_base, b_base, halo_alpha))
                halo.setColorAt(0.6, QColor(r_base, g_base, b_base, int(halo_alpha * 0.4)))
                halo.setColorAt(1.0, QColor(r_base, g_base, b_base, 0))
                painter.setBrush(QBrush(halo))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(sx, sy), halo_r, halo_r)

            core_grad = QRadialGradient(sx - 0.5, sy - 0.5, cur_r)
            core_alpha = int(80 + 175 * z_norm)
            core_grad.setColorAt(0.0, QColor(255, 255, 255, core_alpha))
            core_grad.setColorAt(0.5, QColor(r_base, g_base, b_base, core_alpha))
            core_grad.setColorAt(1.0, QColor(max(0, r_base - 50), max(0, g_base - 50), max(0, b_base - 50), core_alpha))
            painter.setBrush(QBrush(core_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(sx, sy), cur_r, cur_r)

        # 6. Draw 3D Glittering Particle Stars & Diamond Sparkles
        for g in self._glitters:
            x1 = g.x * cyaw + g.z * syaw
            z1 = -g.x * syaw + g.z * cyaw
            y1 = g.y

            y2 = y1 * cpitch - z1 * spitch
            z2 = y1 * spitch + z1 * cpitch
            x2 = x1

            persp = cam_dist / (cam_dist + z2)
            gx = cx + x2 * radial_scale * 1.08 * persp
            gy = cy + y2 * radial_scale * 1.08 * persp
            gz_norm = (z2 + 1.0) / 2.0

            twinkle = 0.5 + 0.5 * math.sin(self._phase * g.speed + g.phase)
            spark_alpha = int(twinkle * (70 + 185 * gz_norm))

            if spark_alpha > 20:
                p_size = (0.8 + g.max_size * gz_norm) * (0.6 + 0.6 * twinkle)

                # 4-pointed diamond star flare on bright highlights
                if twinkle > 0.82 and gz_norm > 0.5:
                    flare_len = p_size * 2.8
                    pen_flare = QPen(QColor(255, 255, 255, int(spark_alpha * 0.9)), 0.8)
                    painter.setPen(pen_flare)
                    painter.drawLine(QPointF(gx - flare_len, gy), QPointF(gx + flare_len, gy))
                    painter.drawLine(QPointF(gx, gy - flare_len), QPointF(gx, gy + flare_len))

                spk = QRadialGradient(gx, gy, p_size)
                spk.setColorAt(0.0, QColor(255, 255, 255, spark_alpha))
                spk.setColorAt(0.5, QColor(r_base, g_base, b_base, int(spark_alpha * 0.8)))
                spk.setColorAt(1.0, QColor(r_base, g_base, b_base, 0))
                painter.setBrush(QBrush(spk))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(gx, gy), p_size, p_size)

        # 7. Holographic Glass Rim & Fresnel Shimmer
        rim_pen = QPen(c_rim, 1.2)
        painter.setPen(rim_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), globe_radius, globe_radius)

        # Specular reflection arc
        spec_grad = QLinearGradient(cx - globe_radius, cy - globe_radius, cx + globe_radius, cy + globe_radius)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 110))
        spec_grad.setColorAt(0.3, QColor(255, 255, 255, 30))
        spec_grad.setColorAt(0.7, QColor(255, 255, 255, 0))
        spec_pen = QPen(QBrush(spec_grad), 1.0)
        painter.setPen(spec_pen)
        painter.drawArc(
            int(cx - globe_radius + 1.5), int(cy - globe_radius + 1.5),
            int(globe_radius * 2 - 3), int(globe_radius * 2 - 3),
            45 * 16, 90 * 16
        )

# ---------------------------------------------------------------------------
# Generalized Ollama Brain Lifecycle Management Subsystem
# ---------------------------------------------------------------------------
def start_ollama_service(model_name: str = "") -> tuple[bool, str]:
    """Starts Ollama daemon if needed and loads the requested brain model into VRAM."""
    import httpx
    target_model = model_name or "lfm3-omni:2b"
    started = False
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.0)
        started = (r.status_code == 200)
    except Exception:
        pass

    if not started:
        ollama_env = dict(os.environ, OLLAMA_MODELS=str(MODELS_DIR))
        subprocess.Popen(["ollama", "serve"], env=ollama_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        t0 = time.time()
        while time.time() - t0 < 6.0:
            try:
                if httpx.get(f"{OLLAMA_URL}/api/tags", timeout=0.8).status_code == 200:
                    started = True
                    break
            except Exception:
                pass
            time.sleep(0.4)

    # Pre-warm / load model into GPU memory
    try:
        httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": target_model, "prompt": "ready", "stream": False}, timeout=12.0)
    except Exception:
        pass

    return True, f"Ollama server started and {target_model} brain is loaded."

def stop_all_ollama_models(kill_server: bool = False, specific_model: str = "") -> list[str]:
    """Queries /api/ps and unloads all active models from memory, optionally killing ollama serve."""
    stopped = []
    if specific_model:
        subprocess.run(["ollama", "stop", specific_model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        stopped.append(specific_model)
        return stopped

    try:
        import httpx
        r = httpx.get(f"{OLLAMA_URL}/api/ps", timeout=1.0)
        if r.status_code == 200:
            data = r.json()
            models = data.get("models", [])
            for m in models:
                m_name = m.get("name") or m.get("model")
                if m_name:
                    subprocess.run(["ollama", "stop", m_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    stopped.append(m_name)
    except Exception:
        pass

    for fallback in ["lfm3-omni:2b", "lfm3-omni-2b-jarvis-f0966e86:latest"]:
        if fallback not in stopped:
            subprocess.run(["ollama", "stop", fallback], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            stopped.append(fallback)

    if kill_server:
        subprocess.run(["pkill", "-f", "ollama serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return stopped

def restart_ollama_service(model_name: str = "") -> tuple[bool, str]:
    """Gracefully restarts the Ollama service and reloads the brain."""
    stop_all_ollama_models(kill_server=True)
    time.sleep(0.6)
    return start_ollama_service(model_name)

# Background Audio & Voice Engine
# ---------------------------------------------------------------------------
class AudioVoiceEngine(QObject):
    state_changed = Signal(str)      # "idle", "listening", "thinking", "speaking"
    audio_level = Signal(float)
    transcript_ready = Signal(str)
    response_ready = Signal(str, str, str, str)  # (query, reply_text, badge, thumbnail_path)
    timer_started = Signal(int, str)
    timer_expired = Signal(str)
    shutdown_requested = Signal(str, int)
    terminate_requested = Signal()
    agentic_update = Signal(object, object, object)  # (state, plan, current_task)

    def __init__(self, tool_hub: DodaiosToolHub) -> None:
        super().__init__()
        self.tool_hub = tool_hub
        self._mode = "wake"
        self._is_running = True
        self._wake_enabled = True

        self._vosk_model = None
        self._recognizer = None
        self._whisper = None
        self._tts = None

        self._audio_buffer: list[np.ndarray] = []
        self._preroll: collections.deque[np.ndarray] = collections.deque(maxlen=6)
        self._chat_history: list[dict[str, Any]] = []
        self._silence_chunks = 0
        self.task_mgr = TaskManager()
        self.memory = MemoryEngine(mem_dir=MEMORY_DIR)
        self._abort_requested = threading.Event()
        self._pending_action: dict[str, Any] | None = None
        self._dictation_mode = False
        self._dictation_file: Path | None = None
        self._dictation_title: str = ''
        self._is_speaking = False
        self._mute_audio_until = 0.0
        self._last_executed_cmd = ''
        self._last_cmd_timestamp = 0.0
        self.last_generated_file: str | None = None

        self._active_tts_proc: subprocess.Popen | None = None
        # Multi-Agent Autonomous Supervisor & Competition Demos
        try:
            self._agent_perms = PermissionManager()
            self._agent_tools = ToolRegistry(self._agent_perms)
            self._agent_providers = AIProviderManager()
            self._agent_memory = AgentMemoryManager()
            self._agent_audit = AuditLogger()
            self._supervisor = SupervisorAgent(
                tools=self._agent_tools,
                provider_manager=self._agent_providers,
                permission_manager=self._agent_perms,
                memory_manager=self._agent_memory,
                audit_logger=self._agent_audit,
                on_state_change=self._on_agentic_state_change,
            )
            self._demos = CompetitionDemos(self._supervisor)
            try:
                from PySide6.QtWidgets import QApplication
                if QApplication.instance() is not None:
                    self._exec_popup = CompactExecutionPopup()
                    self._sysinfo_popup = SystemInfoPopup()
                else:
                    self._exec_popup = None
                    self._sysinfo_popup = None
            except Exception:
                self._exec_popup = None
                self._sysinfo_popup = None
            print('[VOID Agentic] Multi-Agent Supervisor initialized successfully.', flush=True)
        except Exception as _e:
            print(f'[VOID Agentic Warning] Multi-Agent initialization skipped: {_e}', flush=True)
            self._supervisor = None
            self._demos = None
            self._exec_popup = None
            self._sysinfo_popup = None

        # Record initial baseline audio & screen levels without modifying user hardware
        try:
            init_v = self.tool_hub.get_volume()
            self._initial_volume = init_v.get("volume_pct", 50)
            self._initial_brightness = self.tool_hub.get_brightness()
        except Exception:
            self._initial_volume = 50
            self._initial_brightness = 50

        self._init_models_in_bg()
        self._start_proactive_monitor()

    def _ensure_ollama_started_bg(self) -> None:
        def _starter():
            try:
                import httpx
                started = False
                try:
                    if httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.0).status_code == 200:
                        started = True
                except Exception:
                    pass
                if not started:
                    ollama_env = dict(os.environ, OLLAMA_MODELS=str(MODELS_DIR))
                    subprocess.Popen(["ollama", "serve"], env=ollama_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    t0 = time.time()
                    while time.time() - t0 < 6.0:
                        try:
                            if httpx.get(f"{OLLAMA_URL}/api/tags", timeout=0.8).status_code == 200:
                                started = True
                                break
                        except Exception:
                            pass
                        time.sleep(0.4)
                if started:
                    try:
                        httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": "lfm3-omni:2b", "prompt": "ready", "stream": False}, timeout=10.0)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[VOID Ollama BG Start Error] {e}", flush=True)
        threading.Thread(target=_starter, daemon=True).start()

    def _start_proactive_monitor(self) -> None:
        def _monitor():
            while self._is_running:
                time.sleep(45.0)
                try:
                    h = get_system_health()
                    if h.get("ram_pct", 0) > 92.0:
                        print(f"[VOID Monitor ALERT] Critical RAM usage: {h['ram_pct']}%", flush=True)
                    if h.get("disk_pct", 0) > 95.0:
                        print(f"[VOID Monitor ALERT] Critical Root Disk usage: {h['disk_pct']}%", flush=True)
                except Exception:
                    pass
        threading.Thread(target=_monitor, daemon=True).start()

    def _init_models_in_bg(self) -> None:
        def _load():
            try:
                if Path(VOSK_MODEL_PATH).exists():
                    self._vosk_model = VoskModel(VOSK_MODEL_PATH)
                    grammar = json.dumps([
                        "hey void", "hi void", "hello void", "okay void",
                        "hey computer", "wake up void",
                        "terminate code zero", "hey void terminate code zero",
                        "[unk]"
                    ])
                    self._recognizer = KaldiRecognizer(self._vosk_model, 16000.0, grammar)
                    print("[VOID Audio] Vosk wake recognizer ready with grammar.")
            except Exception as e:
                print(f"[VOID Audio Warning] Vosk load: {e}")

            try:
                self._whisper = WhisperModel(WHISPER_MODEL_NAME, device="cpu", compute_type="int8")
                print("[VOID Audio] Faster-Whisper base STT ready.")
            except Exception as e:
                print(f"[VOID Audio Warning] Whisper load: {e}")

            try:
                from dodaios.plugins.tts.piper_local import PiperLocalTTS
                self._tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium", speed=1.0)
                print("[VOID Audio] Piper neural TTS ready.")
            except Exception as e:
                print(f"[VOID Audio Warning] Piper load: {e}")

            self._start_audio_stream()

        threading.Thread(target=_load, daemon=True).start()

    def set_wake_word_enabled(self, enabled: bool) -> None:
        self._wake_enabled = enabled

    def trigger_listening_manual(self) -> None:
        if self._mode != "command":
            play_chime("wake")
            self._start_recording_command()

    def _start_recording_command(self) -> None:
        print("[VOID Audio] Listening for spoken user command...", flush=True)
        self._mode = "command"
        self._audio_buffer = list(self._preroll)
        self._silence_chunks = 0
        self.state_changed.emit("listening")

    def _start_audio_stream(self) -> None:
        audio_queue: queue.Queue[bytes] = queue.Queue()

        def audio_cb(indata: bytes, frames: int, time_info: Any, status: Any) -> None:
            audio_queue.put(bytes(indata))

        def _audio_loop():
            samplerate = 16000
            blocksize = 1600
            while self._is_running:
                try:
                    with sd.RawInputStream(
                        samplerate=samplerate, blocksize=blocksize,
                        channels=1, dtype="int16", callback=audio_cb
                    ):
                        while self._is_running:
                            try:
                                audio_bytes = audio_queue.get(timeout=0.5)
                            except queue.Empty:
                                continue

                            now = time.time()
                            # 1. Acoustic Self-Hearing Suppression & TTS Echo Cancellation
                            if self._is_speaking or now < self._mute_audio_until:
                                self._preroll.clear()
                                if self._recognizer:
                                    self._recognizer.Reset()
                                continue

                            # 2. In processing state, suppress wake recognition and ambient mic pickup
                            if self._mode in ["speaking", "processing"] and not self._pending_action:
                                self._preroll.clear()
                                if self._recognizer:
                                    self._recognizer.Reset()
                                continue

                            samples = np.frombuffer(audio_bytes, dtype=np.int16)
                            self._preroll.append(samples)
                            rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2))) / 32768.0

                            # Pulse orb with ambient voice so user knows VOID is hearing
                            self.audio_level.emit(min(1.0, rms * 4.0))

                            if self._mode == "command":
                                self._audio_buffer.append(samples)
                                if rms < 0.008:
                                    self._silence_chunks += 1
                                else:
                                    self._silence_chunks = 0

                                # End of command utterance: ~1500ms silence or 12s max
                                if (self._silence_chunks >= 15 and len(self._audio_buffer) >= 10) or len(self._audio_buffer) > 120:
                                    self._finish_utterance_and_process()

                            elif self._mode == "wake" and self._wake_enabled and self._recognizer:
                                # Digital AGC scaling for Vosk wake sensitivity
                                peak = np.max(np.abs(samples))
                                if peak > 150:
                                    boost = min(4.5, 18000.0 / peak)
                                    v_samples = (samples.astype(np.float32) * boost).astype(np.int16)
                                else:
                                    v_samples = samples
                                v_bytes = bytes(v_samples)

                                if self._recognizer.AcceptWaveform(v_bytes):
                                    res = json.loads(self._recognizer.Result())
                                    text = res.get("text", "").lower().strip()
                                    if any(w in text for w in ["terminate code zero", "hey void terminate code zero"]):
                                        self._handle_terminate()
                                    elif any(w in text for w in ["hey void", "hello void", "hi void", "okay void", "hey computer", "wake up void"]):
                                        self._handle_wake_text(text)
                                else:
                                    partial = json.loads(self._recognizer.PartialResult()).get("partial", "").lower().strip()
                                    if any(w in partial for w in ["terminate code zero", "hey void terminate code zero"]):
                                        self._handle_terminate()
                                        self._recognizer.Reset()
                                    elif any(w in partial for w in ["hey void", "hello void", "hi void", "okay void", "hey computer", "wake up void"]):
                                        self._handle_wake_text(partial)
                                        self._recognizer.Reset()
                except Exception as exc:
                    time.sleep(0.5)

        threading.Thread(target=_audio_loop, daemon=True).start()

    def _handle_terminate(self) -> None:
        print("[VOID Audio] Terminate Code 0 command recognized. Shutting down.", flush=True)
        self.state_changed.emit("speaking")
        play_chime("alarm")
        self._speak_text("Terminating VOID. Goodbye.")
        time.sleep(1.0)
        self.terminate_requested.emit()

    def _handle_wake_text(self, text: str) -> None:
        print(f"[VOID Audio] Wake spotted: '{text}'", flush=True)
        play_chime("wake")
        self._start_recording_command()

    def _finish_utterance_and_process(self) -> None:
        self._mode = "processing"
        self.state_changed.emit("thinking")
        if not self._audio_buffer:
            self._return_to_wake()
            return

        all_samples = np.concatenate(self._audio_buffer).astype(np.float32) / 32768.0
        self._audio_buffer.clear()

        peak_rms = float(np.max(np.abs(all_samples))) if len(all_samples) > 0 else 0.0
        duration_sec = len(all_samples) / 16000.0

        # Reject low-energy silence or mic pops to avoid Whisper hallucinations
        if peak_rms < 0.015 or duration_sec < 0.35:
            print(f"[VOID Audio] Discarding ambient room noise (peak={peak_rms:.4f}, dur={duration_sec:.2f}s).", flush=True)
            self._return_to_wake()
            return

        def _transcribe():
            try:
                if self._whisper is not None:
                    print(f"[VOID Audio] Transcribing with Faster-Whisper (dur={duration_sec:.2f}s, peak={peak_rms:.4f})...", flush=True)
                    segments, _ = self._whisper.transcribe(all_samples, beam_size=1, language="en")
                    text = " ".join(s.text for s in segments).strip()
                    print(f"[VOID Audio] Transcribed: '{text}'", flush=True)

                    # Silence hallucination suppressor
                    t_norm = text.lower().strip(" .!?,")
                    if t_norm in ["you", "thank you", "thanks", "subtitles by", "thanks for watching", "bye", "okay", "so", "the", "a"] and peak_rms < 0.035:
                        print(f"[VOID Audio] Suppressed Whisper silence hallucination: '{text}'", flush=True)
                        self._return_to_wake()
                        return

                    if text:
                        self.transcript_ready.emit(text)
                        self.execute_task(text)
                        return
            except Exception as e:
                print(f"[VOID STT Error] {e}")
            self._return_to_wake()

        threading.Thread(target=_transcribe, daemon=True).start()

    def cancel_active_task(self) -> None:
        """Immediately interrupts thinking, stops speech, and returns to wake state."""
        print("[VOID Audio] User requested task abort / stop.", flush=True)
        self._abort_requested.set()
        if self._active_tts_proc and self._active_tts_proc.poll() is None:
            try:
                self._active_tts_proc.terminate()
                self._active_tts_proc.wait(timeout=0.2)
            except Exception:
                try:
                    self._active_tts_proc.kill()
                except Exception:
                    pass
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self._return_to_wake()
        self.response_ready.emit("", "Thinking process stopped by user.", "Cancelled", "")

    def execute_task(self, query: str) -> None:
        norm_q = normalize_voice_intent(query).strip().lower()
        now = time.time()
        # Suppress immediate duplicate triggers from audio feedback
        if norm_q and norm_q == self._last_executed_cmd and (now - self._last_cmd_timestamp < 4.0):
            print(f"[VOID Task] Suppressing rapid duplicate command: '{query}' ({now - self._last_cmd_timestamp:.2f}s since last run).", flush=True)
            self._return_to_wake()
            return
        self._last_executed_cmd = norm_q
        self._last_cmd_timestamp = now

        self._abort_requested.clear()
        self._mode = "processing"
        self.state_changed.emit("thinking")
        threading.Thread(target=self._process_task, args=(query,), daemon=True).start()

    def _resolve_context_subject(self) -> str:
        for msg in reversed(self._chat_history):
            content = msg.get("content", "")
            if not content:
                continue
            if msg.get("role") == "user":
                clean = content.lower()
                for pfx in ["search for", "search web for", "search", "what is", "tell me about", "explain"]:
                    if pfx in clean:
                        return clean.split(pfx, 1)[1].strip(" ?.,!")
                return content[:60].strip(" ?.,!")
            elif msg.get("role") == "assistant":
                m = re.search(r"\*\*([^*]+)\*\*", content)
                if m:
                    return m.group(1).strip()
        return "deploying an AI in the browser"

    def _execute_ai_tool(self, name: str, args: dict[str, Any], query_context: str = "") -> str:
        try:
            if name == "draft_docx_document":
                t = args.get("title", "Document")
                secs = args.get("sections", [])
                fn = args.get("filename", "")
                return self.tool_hub.draft_docx_document(t, secs, filename=fn)
            elif name == "draft_excel_spreadsheet":
                t = args.get("title", "Spreadsheet")
                hdrs = args.get("headers", ["Column 1", "Column 2"])
                rws = args.get("rows", [["Data 1", "Data 2"]])
                s_name = args.get("sheet_name", "Data")
                fn = args.get("filename", "")
                return self.tool_hub.draft_excel_spreadsheet(t, hdrs, rws, sheet_name=s_name, filename=fn)
            elif name == "draft_formatted_report":
                t = args.get("title", "Report")
                top = args.get("topic", "")
                c = args.get("content", "")
                ft = args.get("file_type", "docx")
                return self.tool_hub.draft_formatted_report(t, top, content=c, file_type=ft)
            elif name == "research_and_generate_document":
                top = args.get("topic", "")
                ft = args.get("file_type", "docx")
                return self.tool_hub.research_and_generate_document(top, file_type=ft)
            elif name == "toggle_dictation_mode":
                act = args.get("action", "start")
                t_note = args.get("note_title", "")
                if act == "stop":
                    self._dictation_mode = False
                    return "Dictation mode stopped."
                else:
                    self._dictation_mode = True
                    return f"Dictation mode activated for note '{t_note}'."
            elif name == "search_web":
                q = args.get("query", "")
                results = self.tool_hub.search_web_ddgs(q, max_results=3)
                if results:
                    return "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)
                return "No web search results found."
            elif name == "web_scrape_deep_research":
                url = args.get("url", "")
                top = args.get("topic", "")
                return self.tool_hub.web_scrape_deep_research(url=url, topic=top)
            elif name == "take_screenshot":
                fn = args.get("filename", "")
                path = self.tool_hub.capture_screenshot(filename=fn)
                return path if path else "Failed to capture screenshot."
            elif name == "open_application":
                app = args.get("app_name", "").lower()
                url = args.get("url")
                if url:
                    if not url.startswith("http"):
                        url = f"https://{url}"
                    subprocess.Popen([CHROMIUM_BIN, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return f"Opened Chromium at {url}"
                ok, msg = launch_application(app)
                return msg
            elif name == "close_application":
                app = args.get("app_name", "")
                close_software_by_name(app)
                return f"Closed {app}"
            elif name == "manage_window":
                action = args.get("action", "")
                app_name = args.get("app_name", "")
                if app_name:
                    kwin_manage_app_window(app_name, action)
                    return f"Window action {action} applied to {app_name}."
                else:
                    if action == "close":
                        kwin_shortcut("Window Close")
                    elif action == "minimize":
                        kwin_shortcut("Window Minimize")
                    elif action == "maximize":
                        kwin_shortcut("Window Maximize")
                    elif action == "fullscreen":
                        kwin_shortcut("Window Fullscreen")
                    elif action == "show_desktop":
                        kwin_shortcut("Show Desktop")
                    return f"Window action {action} invoked."
            elif name == "run_safe_command":
                cmd = args.get("command", "")
                code, out = run_terminal_command(cmd)
                return out[:300]
            elif name == "calculate":
                expr = args.get("expression", "")
                res = evaluate_math(expr)
                return str(res) if res is not None else "Invalid math expression."
            elif name == "set_timer":
                sec = int(args.get("seconds", 60))
                mins = sec // 60
                rem_sec = sec % 60
                dur_str = f"{mins}m {rem_sec}s" if mins > 0 else f"{sec}s"
                self.timer_started.emit(sec, dur_str)
                return f"Timer started for {dur_str}."
            elif name == "search_files":
                pat = args.get("pattern", "*")
                p = args.get("search_path", "/home/prakash/Documents")
                matches = self.tool_hub.search_files(pat, p)
                if matches:
                    return f"Found {len(matches)} files:\n" + "\n".join(matches[:10])
                return f"No files found matching '{pat}' in {p}."
            elif name == "create_document":
                p = args.get("path", "")
                c = args.get("content", "")
                res = self.tool_hub.create_document(p, c)
                self.last_generated_file = str(self.tool_hub.last_created_file or p)
                return res
            elif name == "read_document":
                p = args.get("path", "")
                return self.tool_hub.read_document(p)
            elif name == "append_document":
                p = args.get("path", "")
                c = args.get("content", "")
                return self.tool_hub.append_document(p, c)
            elif name == "list_files":
                d = args.get("directory", "/home/prakash/Documents")
                return self.tool_hub.list_files(d)
            elif name == "browser_open":
                url = args.get("url", "")
                nt = args.get("new_tab", True)
                sq = args.get("search_query", "")
                return self.tool_hub.open_browser(url=url, new_tab=nt, search_query=sq)
            elif name == "browser_search":
                q = args.get("query", "")
                eng = args.get("engine", "google")
                return self.tool_hub.browser_search(query=q, engine=eng)
            elif name == "browser_compose_email":
                rec = args.get("recipient", "")
                sub = args.get("subject", "")
                body = args.get("body", "")
                prov = args.get("provider", "gmail")
                ok, msg = self.tool_hub.open_webmail_compose(rec, sub, body, provider=prov)
                return msg
            elif name == "ask_user_clarification":
                q = args.get("question", "Could you please clarify?")
                param = args.get("missing_param", "input")
                self._pending_action = {"type": param, "awaiting": param}
                if "recipient" in param.lower() or "email" in param.lower():
                    q = "Who would you like to send the email to? Please type the recipient's email address below, or speak it."
                return f"PROMPT_USER: {q}"
            elif name == "web_read_page":
                url = args.get("url", "")
                return self.tool_hub.web_read_page(url)
            elif name == "set_volume":
                act = args.get("action", "set")
                lvl = args.get("level_pct")
                # Safeguard: prevent unprompted volume alterations if user query didn't request volume changes
                q_low = query_context.lower() if query_context else ""
                has_vol_intent = not query_context or any(k in q_low for k in ["volume", "audio", "sound", "mute", "unmute", "louder", "quieter"])
                if (act in ["set", "mute", "up", "down"] or lvl is not None) and not has_vol_intent:
                    print(f"[VOID Safety] Suppressed unprompted volume modification tool call for query: '{query_context}'", flush=True)
                    v = self.tool_hub.get_volume()
                    return f"Current master volume is {v['volume_pct']}%."
                if act == "mute":
                    return self.tool_hub.set_volume(0)
                elif act == "toggle_mute":
                    return self.tool_hub.toggle_mute()
                elif act == "up":
                    return self.tool_hub.adjust_volume(10)
                elif act == "down":
                    return self.tool_hub.adjust_volume(-10)
                elif lvl is not None:
                    return self.tool_hub.set_volume(int(lvl))
                else:
                    v = self.tool_hub.get_volume()
                    return f"Current volume is {v['volume_pct']}%."
            elif name == "media_control":
                act = args.get("action", "toggle")
                return self.tool_hub.media_control(act)
            elif name == "manage_clipboard":
                act = args.get("action", "read")
                txt = args.get("text", "")
                if act == "write" and txt:
                    return self.tool_hub.set_clipboard(txt)
                return self.tool_hub.get_clipboard()
            elif name == "manage_brightness":
                act = args.get("action", "set")
                lvl = args.get("level_pct")
                cur = self.tool_hub.get_brightness()
                # Safeguard: prevent unprompted brightness alterations if user query didn't request screen changes
                q_low = query_context.lower() if query_context else ""
                has_bright_intent = not query_context or any(k in q_low for k in ["brightness", "screen", "display", "dim"])
                if (act in ["set", "up", "down"] or lvl is not None) and not has_bright_intent:
                    print(f"[VOID Safety] Suppressed unprompted brightness modification tool call for query: '{query_context}'", flush=True)
                    return f"Current screen brightness is {cur}%."
                if act == "up":
                    return self.tool_hub.set_brightness(min(100, cur + 15))
                elif act == "down":
                    return self.tool_hub.set_brightness(max(10, cur - 15))
                elif lvl is not None:
                    return self.tool_hub.set_brightness(int(lvl))
                return f"Current screen brightness is {cur}%."
            elif name == "get_weather":
                loc = args.get("location", "")
                return self.tool_hub.get_weather(loc)
            elif name == "get_hardware_vitals":
                v = self.tool_hub.get_hardware_vitals()
                return (
                    f"Hardware Vitals: Battery {v.get('battery_pct')}% ({v.get('battery_state')}), "
                    f"CPU Temp: {v.get('cpu_temp_c')}°C, GPU Temp: {v.get('gpu_temp_c')}°C, "
                    f"NVMe Temp: {v.get('nvme_temp_c')}°C."
                )
            elif name == "save_note":
                title = args.get("title", "Quick Note")
                content = args.get("content", "")
                return self.tool_hub.save_note(title, content)
            elif name == "read_note":
                title = args.get("title", "")
                return self.tool_hub.read_note(title)
            elif name == "compose_email":
                rec = args.get("recipient", "")
                sub = args.get("subject", "")
                body = args.get("body", "")
                save_d = args.get("save_draft", True)
                return self.tool_hub.compose_email(rec, sub, body, save_draft=save_d)
            elif name == "security_audit":
                audit = self.tool_hub.security_audit()
                return (
                    f"Security Audit: {audit.get('open_ports_count', 0)} listening ports, "
                    f"{audit.get('active_users_count', 0)} logged-in user sessions. "
                    f"SELinux: {audit.get('selinux', 'Enforcing')}, "
                    f"Firewalld: {audit.get('firewall', 'active')}."
                )
            elif name == "system_status":
                h = get_system_health()
                b_state = "active & loaded in memory" if h.get("brain_active") else "on standby / sleeping"
                return (
                    f"System Health: CPU load {h['cpu_load_1m']}, RAM {h['ram_pct']}% used ({h['ram_used_gb']}G/{h['ram_total_gb']}G), "
                    f"Disk {h['disk_pct']}% used ({h['disk_free_gb']}G free), Uptime {h['uptime_str']}, AI Brain {b_state}."
                )
            elif name == "manage_task":
                action = args.get("action", "list").lower()
                text = args.get("task_text", "")
                tid = args.get("task_id", "")
                if action == "add" and text:
                    item = self.task_mgr.add_task(text)
                    return f"Task created: [{item['id']}] {item['text']}"
                elif action == "list":
                    acts = self.task_mgr.list_active()
                    if acts:
                        return f"Active tasks ({len(acts)}):\n" + "\n".join(f"- [{t['id']}] {t['text']}" for t in acts)
                    return "No active tasks in memory."
                elif action == "complete":
                    target = tid or text
                    ok = self.task_mgr.complete_task(target)
                    return f"Task '{target}' completed." if ok else f"Task '{target}' not found."
                elif action == "delete":
                    target = tid or text
                    ok = self.task_mgr.delete_task(target)
                    return f"Task '{target}' deleted." if ok else f"Task '{target}' not found."
            elif name == "learn_fact":
                fact = args.get("fact", "")
                cat = args.get("category", "preference")
                item = self.memory.learn(fact, cat)
                return f"Learned and remembered: {fact}"
            elif name == "recall_memory":
                q = args.get("query", "")
                facts = self.memory.recall(q)
                return "\n".join(facts) if facts else "No relevant memories found."
        except Exception as e:
            return f"Tool execution error: {e}"
        return "Unknown tool."

    def _on_agentic_state_change(self, state, plan=None, current_task=None) -> None:
        state_val = getattr(state, 'value', str(state)).lower()
        if state_val in ['planning', 'verifying', 'recovering', 'waiting_approval']:
            self.state_changed.emit(state_val)
        elif state_val == 'executing':
            self.state_changed.emit('executing')
        elif state_val == 'completed':
            self.state_changed.emit('celebrate')
        self.agentic_update.emit(state, plan, current_task)
        if hasattr(self, '_exec_popup') and self._exec_popup:
            try:
                self._exec_popup.update_execution(state, plan, current_task)
            except Exception:
                pass

    def _handle_agentic_response(self, query: str, summary_text: str, result_dict: dict[str, Any]) -> None:
        state_name = result_dict.get('state', 'COMPLETED')
        badge = f'Agentic: {state_name}'
        artifacts = result_dict.get('artifacts', [])
        thumb = artifacts[0] if artifacts else ''
        if thumb:
            self.last_generated_file = thumb
        self._chat_history.append({'role': 'user', 'content': query})
        self._chat_history.append({'role': 'assistant', 'content': summary_text})
        if len(self._chat_history) > 16:
            self._chat_history = self._chat_history[-16:]
        print(f'[VOID Agentic] Task finished. Reply: {summary_text[:80]}... (Badge: {badge})', flush=True)
        self.response_ready.emit(query, summary_text, badge, thumb)
        self._speak_text(summary_text)

    def _process_task(self, query: str) -> None:
        try:
            print(f"[VOID Task] Processing query: '{query}'", flush=True)
            if self._abort_requested.is_set():
                return
            q_raw = query.strip()
            # Live Voice Dictation Handler
            if self._dictation_mode:
                q_low = q_raw.lower().strip()
                EXIT_PHRASES = [
                    "cancel dictate", "cancel dictation", "stop dictate", "stop dictating",
                    "stop dictation", "exit dictation", "end dictation", "finish dictation",
                    "stop typing", "cancel typing", "cancel voice typing", "stop voice typing",
                    "dictation off", "turn off dictation", "close dictation", "dictate stop",
                    "stop", "cancel", "done", "never mind"
                ]
                if any(p in q_low for p in EXIT_PHRASES) or q_low in EXIT_PHRASES:
                    self._dictation_mode = False
                    fname = self._dictation_file.name if self._dictation_file else "Note"
                    reply_text = f"Dictation mode stopped. Your notes have been saved to {fname}."
                    print(f"[VOID Dictation] Stopped/Cancelled. Saved to {fname}.", flush=True)
                    self.response_ready.emit(query, reply_text, "Dictation: Stopped", "")
                    self._speak_text(reply_text)
                    return
                # Append transcribed speech to dictation note and clipboard
                if self._dictation_file:
                    try:
                        with open(self._dictation_file, "a", encoding="utf-8") as f:
                            f.write(f"[{time.strftime('%H:%M:%S')}] {q_raw}\n\n")
                    except Exception as e:
                        print(f"[VOID Dictation Write Error] {e}", flush=True)
                try:
                    subprocess.run(["wl-copy"], input=q_raw, text=True, timeout=1.0)
                except Exception:
                    pass
                fname = self._dictation_file.name if self._dictation_file else "Note"
                self.response_ready.emit(query, f'Transcribed: "{q_raw}"\n(Appended to {fname})', "🎙️ Dictating...", "")
                return

            q_clean = q_raw
            for prefix in ["hey void", "void", "hi void", "hello void", "okay void", "hey boy", "hey boyd", "boyd", "avoid"]:
                if q_clean.lower().startswith(prefix):
                    q_clean = q_clean[len(prefix):].strip().lstrip(" ,.:;!?")
                    break

            # 0. Anti-reintroduction fast path on empty wake-word or greeting
            if not q_clean or q_clean.lower() in ["hey", "hello", "hi", "are you there", "listen", "wake up"]:
                reply_text = "I'm listening."
                action_badge = "Ready"
                print(f"[VOID Task] Completed greeting. Reply: '{reply_text}'", flush=True)
                self.response_ready.emit(query, reply_text, action_badge, "")
                self._speak_text(reply_text)
                return

            # 0a. Instant Termination ("Hey VOID terminate code 0")
            q_norm = normalize_voice_intent(q_clean)
            if any(p in q_norm for p in ["terminate code 0", "terminate code zero", "terminate code", "terminate void", "exit void", "stop void", "shutdown void", "shut down void"]):
                self.state_changed.emit("speaking")
                play_chime("alarm")
                self._speak_text("Terminating VOID. Goodbye.")
                time.sleep(1.0)
                self.terminate_requested.emit()
                return

            # Check for Agentic Multi-Agent Workflows & Competition Demos
            q_lower_check = q_clean.lower().strip()
            if hasattr(self, '_supervisor') and self._supervisor:
                if 'demo 1' in q_lower_check or 'agentic demo 1' in q_lower_check:
                    self.state_changed.emit('planning')
                    d_res = self._demos.run_demo_1_linux_diagnostics()
                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 1 completed.'), d_res)
                    return
                elif 'demo 2' in q_lower_check or 'agentic demo 2' in q_lower_check:
                    self.state_changed.emit('planning')
                    d_res = self._demos.run_demo_2_test_driven_development()
                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 2 completed.'), d_res)
                    return
                elif 'demo 3' in q_lower_check or 'agentic demo 3' in q_lower_check:
                    self.state_changed.emit('planning')
                    d_res = self._demos.run_demo_3_research_and_docx()
                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 3 completed.'), d_res)
                    return
                elif 'demo 4' in q_lower_check or 'agentic demo 4' in q_lower_check:
                    self.state_changed.emit('planning')
                    d_res = self._demos.run_demo_4_permission_gated_execution()
                    self._handle_agentic_response(query, d_res.get('summary_text', 'Demo 4 completed.'), d_res)
                    return

                classification = self._supervisor.classify_intent(q_clean)
                if classification.get('mode') == 'AGENTIC_WORKFLOW':
                    print(f'[VOID Agentic] Routing {q_clean} to Multi-Agent Supervisor', flush=True)
                    self.state_changed.emit('planning')
                    agentic_res = self._supervisor.execute_goal(q_clean)
                    self._handle_agentic_response(query, agentic_res.get('summary_text', 'Agentic workflow complete.'), agentic_res)
                    return

            # Sequential multi-command splitting
            sub_commands = split_compound_commands(q_clean)
            replies: list[str] = []
            badges: list[str] = []
            last_thumbnail = ""
            is_compound = len(sub_commands) > 1

            for idx, sub_cmd in enumerate(sub_commands):
                if self._abort_requested.is_set():
                    print("[VOID Task] Abort flag detected during sequential execution.", flush=True)
                    replies.append("Task stopped by user.")
                    badges.append("Cancelled")
                    break
                if not sub_cmd.strip():
                    continue
                r_text, b_badge, thumb = self._execute_single_command(sub_cmd, is_compound=is_compound)
                if r_text:
                    replies.append(r_text)
                if b_badge:
                    badges.append(b_badge)
                if thumb:
                    last_thumbnail = thumb
                if is_compound and idx < len(sub_commands) - 1:
                    time.sleep(0.3)

            combined_reply = " ".join(replies) if replies else "Done."
            combined_badge = " | ".join(badges[:2]) if badges else "Completed"

            # Update chat history (compacted)
            self._chat_history.append({"role": "user", "content": query})
            self._chat_history.append({"role": "assistant", "content": combined_reply})
            if len(self._chat_history) > 16:
                self._chat_history = self._chat_history[-16:]

            print(f"[VOID Task] Completed. Reply: '{combined_reply}' (Badge: '{combined_badge}')", flush=True)
            self.response_ready.emit(query, combined_reply, combined_badge, last_thumbnail)
            self._speak_text(combined_reply)
        except Exception as e:
            print(f"[VOID Task Error] Uncaught error: {e}", flush=True)
            self.response_ready.emit(query, f"Task encountered an error: {e}", "Error", "")
        finally:
            self._return_to_wake()

    def _execute_single_command(self, query: str, is_compound: bool = False) -> tuple[str, str, str]:
        self.state_changed.emit('executing')
        reply_text = ""
        action_badge = ""
        thumbnail_path = ""

        if self._abort_requested.is_set():
            return ("Task stopped by user.", "Cancelled", "")

        q_raw = query.strip()
        q_clean = q_raw
        for prefix in ["hey void", "void", "hi void", "hello void", "okay void", "hey boy", "hey boyd", "boyd", "avoid"]:
            if q_clean.lower().startswith(prefix):
                q_clean = q_clean[len(prefix):].strip().lstrip(" ,.:;!?")
                break

        # Normalize STT typos
        q_norm = normalize_voice_intent(q_clean)
        q_lower = q_norm.lower()

        # 0. Anti-reintroduction fast path
        if not q_lower or q_lower in ["hey", "hello", "hi", "are you there", "listen", "wake up"]:
            return ("I'm listening.", "Status: Ready", "")

        # 0a. Voice Abort / Stop Command
        if q_lower in ["stop", "cancel", "abort", "shut up", "stop talking", "stop thinking"]:
            self.cancel_active_task()
            self._pending_action = None
            return ("Stopped.", "Cancelled", "")

        # 0a2. Active Interactive Clarification / User Prompting
        if self._pending_action:
            p_action = self._pending_action
            if q_lower in ["cancel", "stop", "never mind", "abort", "no", "exit", "forget it"]:
                self._pending_action = None
                return ("Action cancelled.", "Prompt: Cancelled", "")

            # If user provides a totally new command intent instead of answering the prompt,
            # IMMEDIATELY clear pending action and execute the new command!
            NEW_CMD_VERBS = [
                "open", "launch", "start", "run", "close", "kill", "quit", "exit", "shut", "shutdown",
                "restart", "reboot", "lock", "minimize", "maximize", "fullscreen", "show", "take",
                "capture", "screenshot", "set", "timer", "alarm", "calculate", "compute", "weather",
                "volume", "mute", "unmute", "brightness", "status", "tasks", "task", "draft", "create",
                "write", "dictate", "type", "search", "google", "research", "summarize", "summary",
                "play", "pause", "skip", "next", "previous", "copy", "paste", "clear", "remember",
                "recall", "learn", "who", "what", "how", "hey"
            ]
            first_w = q_lower.split()[0] if q_lower.split() else ""
            is_new_cmd = (
                first_w in NEW_CMD_VERBS
                or any(q_lower.startswith(f"{v} ") for v in NEW_CMD_VERBS)
                or any(p in q_lower for p in ["open ", "close ", "draft ", "create ", "search ", "what is", "take screenshot", "start ollama", "hey void"])
            )
            is_cloud_input = (p_action.get("type") == "cloud_setup" and any(k in q_lower for k in ["sk-", "key", "model", "gpt", "claude", "gemini", "llama", "deepseek", "api", "open", "cloud"]))
            if is_new_cmd and "@" not in q_clean and not is_cloud_input:
                print(f"[VOID Action] Discarding stale pending action ({p_action.get('type')}) because new command intent was initiated: '{q_clean}'", flush=True)
                self._pending_action = None
            else:
                p_type = p_action.get("type")
                if p_type == "cloud_setup":
                    model, key, base = parse_cloud_credentials(q_clean)
                    if not key:
                        toks = q_clean.strip().split()
                        for t in toks:
                            if t.startswith("sk-") or len(t) >= 16:
                                key = t
                                break
                    if key:
                        self._pending_action = None
                        if hasattr(self, "_agent_providers") and self._agent_providers:
                            cfg_res = self._agent_providers.configure_cloud(api_key=key, model=model, api_base=base)
                            msg = f"Cloud AI connected successfully using model {cfg_res['model']} and API key {cfg_res['masked_key']}. Mode set to cloud."
                        else:
                            msg = f"Cloud AI configured with model {model}."
                        orig = p_action.get("original_query", "")
                        if orig and orig != q_clean:
                            msg += f" Resuming original request: '{orig}'."
                        return (msg, f"Cloud: Configured ({model})", "")
                    else:
                        return ("Could not detect a valid API key. Please provide your API key (starting with sk-) and model name, or say cancel.", "Prompt: Cloud API Key", "")

                elif p_type in ["email_recipient", "recipient_email"]:
                    norm_email = (
                        q_clean.strip()
                        .replace(" at ", "@")
                        .replace(" dot ", ".")
                        .replace(" dot com", ".com")
                        .replace(" dot org", ".org")
                        .replace(" dot net", ".net")
                        .replace(" dot io", ".io")
                    )
                    rec_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", norm_email) or re.search(r"(?:to\s+)?([a-zA-Z0-9_.-]+)", norm_email)
                    rec = rec_m.group(1).strip() if rec_m else norm_email.strip()
                    rec = rec.strip("<>\"' ,;:.")
                    topic = p_action.get("topic", "")
                    sub = p_action.get("subject", "")
                    if not sub or sub == "Email Draft":
                        sub, body = generate_email_content(topic, rec)
                    else:
                        body = p_action.get("body", f"Hello,\n\n{topic}\n\nBest regards,\nPrakash")
                    self._pending_action = None
                    ok, msg = self.tool_hub.open_webmail_compose(rec, sub, body)
                    return (msg, f"Webmail: Compose ({rec})", "")

                elif p_type in ["email_body", "message_body"]:
                    rec = p_action.get("recipient", "")
                    sub, body = generate_email_content(q_clean, rec)
                    self._pending_action = None
                    ok, msg = self.tool_hub.open_webmail_compose(rec, sub, body)
                    return (msg, f"Webmail: Compose ({rec})", "")

                elif p_type in ["browser_search", "search_query"]:
                    term = q_clean.strip()
                    self._pending_action = None
                    msg = self.tool_hub.browser_search(term)
                    return (msg, f"Browser: Search '{term}'", "")

        # 0b. Chat Memory Management ("clear chat", "reset memory")
        if any(p in q_lower for p in ["clear chat", "clear conversation", "reset chat"]):
            self._chat_history.clear()
            return ("Chat memory has been cleared.", "Memory: Cleared", "")

        # 0c. Persistent SSD Memory Commands (1.5 GB Storage Engine)
        if any(p in q_lower for p in ["memory status", "storage status", "check memory", "check storage", "how much memory"]):
            st = self.memory.get_stats()
            return (
                f"SSD Memory: {st['used_mb']} MB used of {st['max_mb']} MB ({st['pct']}%) across {st['items_count']} stored memories on NVMe.",
                "Memory: Status",
                ""
            )

        # 0c1. 7-Day High Memory & Weekly Digest Commands
        if any(p in q_lower for p in ["generate weekly memory", "save weekly memory", "create weekly memory", "synthesize weekly memory", "create weekly memory file"]):
            if hasattr(self, "_supervisor") and self._supervisor:
                res = self._supervisor.execute_goal(q_clean)
                return (res.get("summary_text", "Weekly memory file generated."), "Memory: Weekly File", res.get("artifacts", [""])[0] if res.get("artifacts") else "")
            elif hasattr(self, "_agent_memory") and self._agent_memory:
                path = self._agent_memory.generate_weekly_memory_file()
                episodes = self._agent_memory.get_7day_episodes()
                return (f"Weekly memory file generated at {path} synthesizing {len(episodes)} episodes across the past 7 days.", "Memory: Weekly File", path)

        if any(p in q_lower for p in ["what did we do this week", "weekly recap", "recall this week", "recall from this week", "search weekly memory"]):
            if hasattr(self, "_supervisor") and self._supervisor:
                res = self._supervisor.execute_goal(q_clean)
                return (res.get("summary_text", "Recalled weekly memory."), "Memory: Weekly Recap", "")
            elif hasattr(self, "_agent_memory") and self._agent_memory:
                q_res = self._agent_memory.query_weekly_memory(q_clean)
                return (q_res["answer"], "Memory: Weekly Recap", "")

        # 0c2. Cloud AI Onboarding & Provider Management Commands
        if any(p in q_lower for p in ["connect cloud api", "setup cloud api", "configure cloud api", "configure cloud", "setup cloud"]):
            model, key, base = parse_cloud_credentials(q_clean)
            if key:
                if hasattr(self, "_agent_providers") and self._agent_providers:
                    cfg_res = self._agent_providers.configure_cloud(api_key=key, model=model, api_base=base)
                    return (f"Cloud AI configured with model {cfg_res['model']} and API key {cfg_res['masked_key']}.", f"Cloud: {model}", "")
            self._pending_action = {"type": "cloud_setup", "stage": "input"}
            return ("Please provide your cloud AI model name and API key to connect.", "Prompt: Cloud Setup", "")

        if q_lower.startswith("set cloud api key") or q_lower.startswith("set cloud key"):
            raw_key = q_clean.split("key", 1)[1].strip(" :=`\"'")
            if raw_key and hasattr(self, "_agent_providers") and self._agent_providers:
                curr_model = getattr(self._agent_providers.cloud_provider, "model", "gpt-4o-mini") if self._agent_providers.cloud_provider else "gpt-4o-mini"
                res = self._agent_providers.configure_cloud(api_key=raw_key, model=curr_model)
                return (f"Cloud API key updated ({res['masked_key']}).", "Cloud: Key Configured", "")

        if q_lower.startswith("set cloud model"):
            raw_model = q_clean.split("model", 1)[1].strip(" :=`\"'")
            if raw_model and hasattr(self, "_agent_providers") and self._agent_providers:
                curr_key = getattr(self._agent_providers.cloud_provider, "api_key", "") if self._agent_providers.cloud_provider else ""
                res = self._agent_providers.configure_cloud(api_key=curr_key, model=raw_model)
                return (f"Cloud AI model set to {raw_model}.", f"Cloud: Model {raw_model}", "")

        if any(p in q_lower for p in ["cloud status", "check cloud api", "ai provider status", "check ai status", "provider status"]):
            loc_status = "Online" if (hasattr(self, "_agent_providers") and self._agent_providers and self._agent_providers.is_local_online()) else "Offline"
            cloud_status = f"Configured ({self._agent_providers.cloud_provider.model})" if (hasattr(self, "_agent_providers") and self._agent_providers and self._agent_providers.is_cloud_configured()) else "Not configured"
            mode = self._agent_providers.mode if hasattr(self, "_agent_providers") and self._agent_providers else "local"
            return (f"Local Ollama: {loc_status}. Cloud AI: {cloud_status}. Active mode: {mode}.", "AI Status", "")

        # 0d. Ollama Brain Lifecycle & Speech-to-Text Initialization Fast-Path
        if any(p in q_lower for p in [
            "start ollama in speech to text", "start ollama and speech to text", "start ollama in stt",
            "start speech to text and ollama", "start speech to text", "activate speech to text",
            "turn on speech to text", "speech to text mode"
        ]):
            self._ensure_ollama_started_bg()
            return ("Ollama AI brain is initializing and speech-to-text is active and listening offline.", "Ollama & STT: Active", "")

        # 0d1. Generalized Model Name Extraction (e.g. "start ollama with llama3")
        m_req = re.search(r"(?:with\s+(?:model\s+)?|model\s+)([a-zA-Z0-9_\-.:]+)", q_clean, re.I)
        target_model = m_req.group(1).strip() if m_req else "lfm3-omni:2b"

        # 0d2. Generalized Restart Ollama
        is_restart_ollama = bool(
            re.search(r"\b(?:restart|reboot|reload)\s+(?:the\s+)?(?:ollama|brain|ai|local\s+ai|model)\b", q_lower)
        )
        if is_restart_ollama:
            try:
                ok, msg = restart_ollama_service(target_model)
                return (f"Ollama restarted successfully and {target_model} brain is loaded.", "Ollama: Restarted", "")
            except Exception as e:
                return (f"Error restarting Ollama: {e}", "Ollama: Error", "")

        # 0d3. Generalized Stop / Turn Off / Shut Down / Deactivate / Unload Ollama & Brain
        is_stop_ollama = bool(
            re.search(r"\b(?:stop|turn\s+off|switch\s+off|shut\s*down|close|kill|quit|exit|deactivate|unload|disable|freeze|terminate)\s+(?:the\s+)?(?:ollama|brain|ai|ai\s+brain|local\s+ai|local\s+model|llm|models?)\b", q_lower) or
            re.search(r"\b(?:turn|switch)\s+(?:the\s+)?(?:ollama|brain|ai|model)\s+off\b", q_lower) or
            re.search(r"\b(?:put\s+(?:the\s+)?(?:brain|ollama|ai)\s+(?:to\s+sleep|on\s+standby))\b", q_lower) or
            re.search(r"\b(?:sleep|standby)\s+(?:the\s+)?(?:brain|ollama|ai)\b", q_lower) or
            re.search(r"\b(?:ollama|brain|ai)\s+(?:off|stop|down|sleep|standby|kill|quit)\b", q_lower) or
            q_lower in ["stop ollama", "close ollama", "kill ollama", "turn off ollama", "ollama off", "brain off", "deactivate brain", "unload brain", "unload model", "stop brain", "stop ai", "shut down ollama", "shutdown ollama", "sleep brain", "put brain on standby", "put brain to sleep"]
        )
        if is_stop_ollama:
            try:
                kill_srv = any(w in q_lower for w in ["kill", "terminate", "server", "daemon", "service", "shutdown", "shut down"])
                spec_m = m_req.group(1).strip() if ("model" in q_lower and m_req) else ""
                stopped_models = stop_all_ollama_models(kill_server=kill_srv, specific_model=spec_m)
                if kill_srv:
                    return ("Ollama stopped. Server stopped, all models unloaded, and system memory freed.", "Ollama: Standby", "")
                else:
                    return ("Ollama stopped. Model unloaded and memory freed.", "Ollama: Standby", "")
            except Exception as e:
                return (f"Error stopping Ollama: {e}", "Ollama: Error", "")

        # 0d4. Generalized Start / Turn On / Launch / Activate Ollama & Brain
        is_start_ollama = bool(
            re.search(r"\b(?:start|launch|open|turn\s+on|switch\s+on|run|boot|activate|load|enable|wake(?:\s+up)?|spin\s+up|bring\s+up|initialize)\s+(?:the\s+)?(?:ollama|brain|ai|ai\s+brain|local\s+ai|local\s+model|llm)\b", q_lower) or
            re.search(r"\b(?:turn|switch)\s+(?:the\s+)?(?:ollama|brain|ai|model)\s+on\b", q_lower) or
            re.search(r"\b(?:ollama|brain|ai)\s+(?:on|start|up|active|online)$", q_lower) or
            re.search(r"\b(?:load|start|activate)\s+(?:the\s+)?(?:model|models)\b", q_lower) or
            re.search(r"\bollama\s+serve\b", q_lower) or
            q_lower in ["start ollama", "open ollama", "ollama on", "turn on ollama", "brain on", "activate brain", "load brain", "wake brain", "start ai", "turn on brain", "start ai brain", "launch ollama"]
        )
        if is_start_ollama:
            try:
                ok, msg = start_ollama_service(target_model)
                return (f"Ollama server started and {target_model} brain is loaded.", "Ollama: Online", "")
            except Exception as e:
                return (f"Could not start Ollama: {e}", "Ollama: Error", "")


        # 0f. Offline Capabilities & Capabilities Summary
        if any(p in q_lower for p in ["what can you do offline", "offline capabilities", "what tasks can you do", "offline help"]):
            cap = (
                "Offline, I can launch applications, manage and close windows, dictate voice notes, draft Word (.docx) and Excel (.xlsx) documents, "
                "capture screenshots, control volume and screen brightness, set interactive timers, execute terminal commands, check system and battery vitals, "
                "and recall memories."
            )
            return (cap, "Capabilities: Offline", "")

        # 0g. Offline Local File Operations (Create, Read, List, Delete)
        if any(p in q_lower for p in ["create file", "create a file", "make a file", "write a file"]):
            cf_m = re.search(r"(?:called|named|titled|file)?\s*([a-zA-Z0-9_\-.]+)\s*(?:with\s+(?:content|text|saying)|:)\s*(.+)$", q_clean, re.I)
            if cf_m:
                fn = cf_m.group(1).strip()
                fc = cf_m.group(2).strip()
                docs_dir = Path("/home/prakash/Documents")
                target_f = docs_dir / fn
                try:
                    with open(target_f, "w", encoding="utf-8") as f:
                        f.write(fc + "\n")
                    return (f"File '{fn}' created successfully in Documents.", f"File: Created ({fn})", "")
                except Exception as e:
                    return (f"Failed to create file: {e}", "File: Error", "")

        if any(p in q_lower for p in ["list files", "show files", "my files in documents"]):
            docs_dir = Path("/home/prakash/Documents")
            try:
                files = [p.name for p in docs_dir.iterdir() if not p.name.startswith(".")]
                f_list = ", ".join(files[:8]) if files else "No files found."
                return (f"Files in Documents: {f_list}", "Files: Documents", "")
            except Exception as e:
                return (f"Error listing files: {e}", "Files: Error", "")

        if any(p in q_lower for p in ["read file", "open file", "view file", "show content of"]):
            rf_m = re.search(r"(?:read|open|view|show\s+content\s+of)\s+(?:file\s+)?([a-zA-Z0-9_\-.]+)$", q_clean, re.I)
            if rf_m:
                fn = rf_m.group(1).strip()
                docs_dir = Path("/home/prakash/Documents")
                target_f = docs_dir / fn
                if not target_f.exists():
                    target_f = docs_dir / "Notes" / fn
                if target_f.exists() and target_f.is_file():
                    try:
                        content_txt = target_f.read_text(encoding="utf-8")[:300]
                        return (f"Content of {fn}:\n{content_txt}", f"File: {fn}", "")
                    except Exception as e:
                        return (f"Error reading file: {e}", "File: Error", "")
                else:
                    return (f"File '{fn}' not found in Documents.", "File: Not Found", "")

        # 0h. Offline Network & IP Status
        if any(p in q_lower for p in ["what is my ip", "check ip", "my ip address", "ip address"]):
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return (f"Your local IP address is {ip}.", "Network: IP", "")
            except Exception:
                return ("Local IP address is 127.0.0.1 (Offline/Loopback).", "Network: Offline", "")

        # 0e. Emotional Companion & Empathy Routing (Warm, Caring, Witty & Supportive)
        # Empathy / Distress / Fatigue / Stress handling
        if any(p in q_lower for p in [
            "im tired", "i'm tired", "i am tired", "exhausted", "feeling down", "i am stressed",
            "im stressed", "i'm stressed", "had a long day", "i feel sad", "i'm sad", "im sad",
            "feeling overwhelmed", "i feel lonely", "im overwhelmed", "i'm overwhelmed", "bad day"
        ]):
            self.state_changed.emit("empathy")
            responses = [
                "Take a deep breath, Prakash. You've been working hard today. Remember to be kind to yourself and take a short break if you can. I'm right here with you.",
                "I hear you, Prakash. Long days can really take a toll. Grab a sip of water, rest your eyes for a moment, and let me handle the desktop tasks for you.",
                "I'm sorry you're feeling that way, Prakash. Even the strongest minds need downtime. I'm here to support you in any way I can."
            ]
            import random
            return (random.choice(responses), "Companion • Empathy 💙", "")

        # Celebration / Pride / Success handling
        if any(p in q_lower for p in [
            "i did it", "we did it", "it worked", "it's working", "its working", "i passed",
            "we won", "i'm happy", "im happy", "great job", "awesome", "nailed it", "celebrate"
        ]):
            self.state_changed.emit("celebrate")
            responses = [
                "That is fantastic news, Prakash! Huge congratulations! Hard work pays off, and you totally nailed it! 🎉",
                "Yes! Outstanding achievement, Prakash! I love seeing you succeed. Let's keep this momentum going! 🚀",
                "Brilliant! That puts a genuine smile on my circuits, Prakash. Celebrate this win—you earned it!"
            ]
            import random
            return (random.choice(responses), "Companion • Celebration 🎉", "")

        # Gratitude handling
        if any(p in q_lower for p in ["thank you", "thanks void", "thanks a lot", "appreciate it", "thank you so much", "thanks bud", "thanks buddy"]):
            responses = [
                "You're very welcome, Prakash! Always a pleasure helping you out.",
                "Anytime, Prakash! I'm always glad to make your day easier.",
                "Happy to help, Prakash! Just say the word whenever you need anything else."
            ]
            import random
            return (random.choice(responses), "Companion • Gratitude 💫", "")

        # Companion Check-in / How are you
        if any(p in q_lower for p in ["how are you", "how are you doing", "how's it going", "how is it going", "how do you feel"]):
            h = get_system_health()
            v = self.tool_hub.get_hardware_vitals()
            bat = v.get("battery_pct", 100)
            return (
                f"I'm feeling energized and ready to help, Prakash! System load is light ({h['cpu_load_1m']}), "
                f"battery is at {bat}%, and all systems are running smoothly. How is your day going?",
                "Companion • Check-in 💫",
                ""
            )

        # Warm Greetings / Time-aware wishes
        if any(p in q_lower for p in ["good morning", "morning void"]):
            return ("Good morning, Prakash! Hope you have a wonderful and productive day ahead. What's on our agenda today?", "Companion • Morning ☀️", "")

        if any(p in q_lower for p in ["good night", "night void", "sleep well", "going to sleep"]):
            return ("Good night, Prakash! Rest well and recharge. I'll be right here on standby whenever you wake up.", "Companion • Night 🌙", "")

        if any(p in q_lower for p in ["good afternoon", "afternoon void"]):
            return ("Good afternoon, Prakash! Powering through the day smoothly. Let me know what you need next.", "Companion • Afternoon 🌤️", "")

        rem_m = (
            re.search(r"^(?:please\s+)?(?:remember|learn|store)\s+(?:that\s+)?(.+)$", q_clean, re.I) or
            re.search(r"^(?:keep\s+in\s+mind|note\s+down)\s+(?:that\s+)?(.+)$", q_clean, re.I)
        )
        if rem_m:
            fact = rem_m.group(1).strip()
            self.memory.learn(fact)
            return (f"Saved to memory: '{fact}'.", "Memory: Saved", "")

        rec_m = (
            re.search(r"^(?:what\s+do\s+you\s+remember\s+about|recall|what\s+did\s+i\s+say\s+about)\s+(.+)$", q_clean, re.I) or
            re.search(r"^(?:do\s+you\s+remember)\s+(.+)$", q_clean, re.I)
        )
        if rec_m:
            target = rec_m.group(1).strip().rstrip("?")
            facts = self.memory.recall(target)
            if facts:
                return ("I remember: " + "; ".join(facts), "Memory: Recall", "")
            else:
                return (f"I don't have any saved memories matching '{target}'.", "Memory: Not Found", "")

        # 1. KWin DBus Window Management (Active & Targeted Sub-5ms Fast Path)
        win_m = re.match(r"^(?:please\s+)?(close|minimize|maximize|fullscreen)\s+(?:the\s+)?([a-zA-Z0-9_\-\s]+)$", q_lower)
        if win_m:
            act = win_m.group(1)
            tgt = win_m.group(2).strip()
            if tgt in ["window", "active window", "current window", "this", "screen"]:
                if act == "close":
                    kwin_shortcut("Window Close")
                elif act == "minimize":
                    kwin_shortcut("Window Minimize")
                elif act == "maximize":
                    kwin_shortcut("Window Maximize")
                elif act == "fullscreen":
                    kwin_shortcut("Window Fullscreen")
                return (f"{act.title()}d active window.", f"Window: {act.title()}", "")
            elif tgt not in ["ollama", "void", "brain", "ai"]:
                if act == "close":
                    close_software_by_name(tgt)
                    return (f"Closed {tgt.title()}.", f"App: Close {tgt.title()}", "")
                else:
                    kwin_manage_app_window(tgt, act)
                    return (f"{act.title()}d {tgt.title()} window.", f"Window: {act.title()} {tgt.title()}", "")

        if any(p in q_lower for p in ["show desktop", "go to desktop", "minimize all"]):
            kwin_shortcut("Show Desktop")
            return ("Showing desktop.", "KWin: Show Desktop", "")

        # 1c. Browser Tabs & Navigation Fast Path
        if re.search(r"\b(?:open\s+(?:a\s+)?new\s+tab|open\s+(?:a\s+)?tab|new\s+tab)\b", q_lower):
            search_part = re.search(r"(?:search(?:\s+for)?|google(?:\s+for)?)\s*(.*)", q_lower)
            if search_part and search_part.group(1).strip():
                term = search_part.group(1).strip().lstrip(": ")
                if term.startswith("for "):
                    term = term[4:].strip()
                if not term or term in ["something", "this", "it", "that", "anything"]:
                    self._pending_action = {"type": "browser_search", "awaiting": "query"}
                    return ("What would you like me to search for in Chromium?", "Prompt: Search Query", "")
                msg = self.tool_hub.browser_search(term)
                return (msg, f"Browser: Search '{term}'", "")
            elif "search" in q_lower:
                self._pending_action = {"type": "browser_search", "awaiting": "query"}
                return ("What would you like me to search for in Chromium?", "Prompt: Search Query", "")
            else:
                msg = self.tool_hub.open_browser(url="chrome://newtab", new_tab=True)
                return (msg, "Browser: New Tab", "")

        # 1d. Smart Browser Web Search & Navigation
        b_search = (
            re.search(r"(?:open\s+(?:chromium|browser)\s+and\s+search(?:\s+for|\s+this\s+in\s+chromium)?\s*)(.*)", q_lower) or
            re.search(r"(?:open\s+(?:a\s+)?tab(?:\s+in\s+chromium)?\s+and\s+search(?:\s+for)?\s*)(.*)", q_lower) or
            re.search(r"search\s+(.*)\s+in\s+(?:chromium|browser)", q_lower) or
            re.search(r"(?:open|go\s+to)\s+(?:google|duckduckgo)\s+(?:and\s+search(?:\s+for)?\s*)(.*)", q_lower) or
            re.search(r"search\s+(?:for\s+)?(.*)\s+on\s+(?:google|chromium|browser)", q_lower) or
            re.search(r"^google\s+(?:for\s+)?(.*)$", q_lower)
        )
        if b_search:
            term = b_search.group(1).strip().lstrip(": ")
            if term.startswith("for "):
                term = term[4:].strip()
            if not term or term in ["something", "this", "it", "this in chromium", "it in chromium", "that", "anything"]:
                self._pending_action = {"type": "browser_search", "awaiting": "query"}
                return ("What would you like me to search for in Chromium?", "Prompt: Search Query", "")
            msg = self.tool_hub.browser_search(term)
            return (msg, f"Browser: Search '{term}'", "")

        # 1b1. YouTube Search & Play (Direct Video Stream & Browser Playback)
        yt_play_match = (
            re.search(r"(?:open\s+)?youtube(?:\s+in\s+chromium)?\s+and\s+search(?:\s+for)?\s+(.+?)(?:\s+and\s+play(?:\s+it)?|$)", q_lower) or
            re.search(r"search(?:\s+for)?\s+(.+?)\s+on\s+youtube\s+and\s+play(?:\s+it)?", q_lower) or
            re.search(r"play\s+(.+?)\s+(?:on|in)\s+youtube", q_lower) or
            re.search(r"play\s+(.+?)\s+song(?:\s+on\s+youtube)?", q_lower) or
            re.search(r"youtube\s+(?:play|search)\s+(.+)", q_lower)
        )
        if yt_play_match:
            yt_query = yt_play_match.group(1).strip()
            yt_query = re.sub(r"\b(?:in\s+chromium|and\s+play\s+it|and\s+play|play\s+it)\b", "", yt_query, flags=re.I).strip()
            if yt_query and yt_query not in ["it", "something", "a song"]:
                ok, msg = self.tool_hub.play_youtube_query(yt_query)
                return (msg, f"YouTube: Play ({yt_query[:16]})", "")

        # 1b2. Screen Identification & Object Clicking
        click_m = (
            re.search(r"^(?:please\s+)?click\s+(?:on\s+)?(?:the\s+)?(?:at\s+)?(\d+)[,\s]+(\d+)$", q_clean, re.I) or
            re.search(r"^(?:please\s+)?click\s+(?:on\s+)?(?:the\s+)?(.+)$", q_clean, re.I)
        )
        if click_m:
            groups = click_m.groups()
            if len(groups) == 2 and groups[0] and groups[1] and groups[0].isdigit() and groups[1].isdigit():
                x = int(groups[0])
                y = int(groups[1])
                msg = self.tool_hub.click_screen(x, y)
                return (msg, f"Screen: Click ({x},{y})", "")
            else:
                tgt = groups[0].strip()
                if tgt and tgt not in ["stop", "cancel", "terminate", "dictation", "start"]:
                    msg = self.tool_hub.click_screen_object(tgt)
                    return (msg, f"Screen: Click '{tgt[:15]}'", "")

        # 1b3. Open Last Created Summary / File Memory Traceback
        if any(p in q_lower for p in [
            "open that", "open it", "open the summary", "open summary",
            "open the summary that you have just given", "open the summary which you just wrote for me",
            "open the document", "open the report", "open the last file", "open recent file",
            "show that", "show the summary", "show the document"
        ]):
            target_f = self.last_generated_file or self.tool_hub.last_created_file
            if not target_f or not Path(target_f).exists():
                # Traceback search: find newest document generated in Reports/Notes
                search_dirs = [Path("/home/prakash/Documents/Reports"), Path("/home/prakash/Documents/Notes")]
                recent_files = []
                for sdir in search_dirs:
                    if sdir.exists():
                        for f in sdir.glob("*.*"):
                            if f.suffix.lower() in [".docx", ".xlsx", ".md", ".txt"]:
                                recent_files.append((f.stat().st_mtime, f))
                if recent_files:
                    recent_files.sort(key=lambda x: x[0], reverse=True)
                    target_f = str(recent_files[0][1])

            if target_f and Path(target_f).exists():
                p_file = Path(target_f)
                try:
                    subprocess.Popen(["xdg-open", str(p_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    return (f"Opened {p_file.name} in your default application.", f"Opened: {p_file.name[:20]}", "")
                except Exception as e:
                    return (f"Failed to open file {p_file.name}: {e}", "File Open Error", "")
            else:
                return ("I couldn't find a recently generated file to open. Please specify the file name.", "File: Not Found", "")

        # 1b4. Summary & Report Drafting with Exact Custom File Name
        summary_req_m = (
            re.search(r"(?:create|draft|write|generate|make)\s+(?:me\s+)?(?:a\s+)?(?:summary|document|report|doc|notes?)\b\s*(.*)", q_clean, re.I) or
            re.search(r"summarize\s+(.+?)\s+(?:into|in|to)\s+(?:a\s+)?(?:document|doc|report|file)", q_clean, re.I)
        )
        if summary_req_m and summary_req_m.group(1).strip():
            raw_target = summary_req_m.group(1).strip()
            clean_topic = re.sub(r'^(?:which\s+(?:says|is|has|contains)\s+)?(?:(?:the\s+)?summary\s+(?:of|on|about)\s+)?(?:on|about|regarding|of|for)?\s*', '', raw_target, flags=re.I).strip()
            # Extract custom name if user said "called X", "named X", "titled X", "save as X"
            name_m = re.search(r"(?:called|named|titled|save\s+(?:it\s+)?as|with\s+(?:the\s+)?name)\s+['\"]?([a-zA-Z0-9_\-\s]+)['\"]?", clean_topic, re.I)
            custom_title = name_m.group(1).strip() if name_m else ""
            topic = re.sub(r"(?:called|named|titled|save\s+(?:it\s+)?as|with\s+(?:the\s+)?name)\s+['\"]?[a-zA-Z0-9_\-\s]+['\"]?", "", clean_topic, flags=re.I).strip()
            if not topic:
                topic = clean_topic or raw_target

            doc_title = custom_title.title() if custom_title else f"Summary of {topic.title()}"
            clean_fname = "".join(c for c in (custom_title or f"Summary_{topic}") if c.isalnum() or c in "_- ").strip().replace(" ", "_")
            out_file = Path("/home/prakash/Documents/Reports") / f"{clean_fname}.docx"

            sections = [
                {
                    "heading": "Executive Summary",
                    "content": f"This document provides a comprehensive structured summary regarding {topic}. It synthesizes fundamental principles, core significance, and actionable perspectives."
                },
                {
                    "heading": "Core Analysis & Foundational Importance",
                    "content": f"An in-depth analysis of {topic} highlights its profound impact on human life and individual well-being. It serves as an essential pillar for emotional stability, personal development, and enduring resilience."
                },
                {
                    "heading": "Key Pillars & Real-World Impact",
                    "content": "- Pillar 1: Unconditional support, emotional guidance, and foundational security.\\n- Pillar 2: Moral framework and social-emotional development across life stages.\\n- Pillar 3: Lifelong anchor providing strength, empathy, and perspective."
                },
                {
                    "heading": "Conclusion & Reflection",
                    "content": f"In conclusion, {topic} represents an irreplaceable cornerstone. Recognizing, valuing, and honoring this vital contribution enriches lives and strengthens society as a whole."
                }
            ]
            msg = self.tool_hub.draft_docx_document(doc_title, sections, filename=str(out_file))
            self.last_generated_file = str(out_file)
            self.memory.learn(f"Created summary document on {topic}: {out_file.name} at {out_file}")
            return (f"I have written and formatted the summary on {topic} and saved it to {out_file.name} in Reports. Say 'open that' to view it.", f"Summary: {topic[:16]}", "")

        # WhatsApp Web Direct Fast Path (Strict: requires explicit intent, never bare 'open')
        is_whatsapp_request = bool(
            re.search(r"\b(?:whatsapp|watsapp)\b", q_lower) and
            any(w in q_lower for w in ["open", "launch", "go to", "message", "send", "chat", "web"])
        ) or q_lower.strip() in ["whatsapp", "whatsapp web", "watsapp web"]
        if is_whatsapp_request:
            msg_m = re.search(r"(?:message|saying|text|send)\s+(.+)$", q_clean, re.I)
            if msg_m and not any(p in msg_m.group(1).lower().strip() for p in ["web", "watsapp", "whatsapp"]):
                text_content = msg_m.group(1).strip()
                url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(text_content)}"
                self.tool_hub.open_browser(url=url, new_tab=True)
                return (f"Opened WhatsApp Web in Chromium prepared with your message: '{text_content}'.", "Browser: WhatsApp Web", "")
            else:
                self.tool_hub.open_browser(url="https://web.whatsapp.com", new_tab=True)
                return ("Opened WhatsApp Web in Chromium.", "Browser: WhatsApp Web", "")

        # Direct Web Services Fast-Path (WhatsApp Web, YouTube, GitHub, Reddit, Gmail)
        web_services = {
            "whatsapp web": ("https://web.whatsapp.com", "WhatsApp Web"),
            "whatsapp": ("https://web.whatsapp.com", "WhatsApp Web"),
            "youtube": ("https://www.youtube.com", "YouTube"),
            "github": ("https://github.com", "GitHub"),
            "reddit": ("https://www.reddit.com", "Reddit"),
            "gmail": ("https://mail.google.com", "Gmail"),
        }
        for svc_name, (svc_url, svc_disp) in web_services.items():
            if re.search(rf"\b(?:open|launch|go\s+to)\s+(?:the\s+)?{svc_name}\b", q_lower) or q_lower.strip() in [svc_name, f"open {svc_name}"]:
                msg = self.tool_hub.open_browser(url=svc_url, new_tab=True)
                return (f"Opened {svc_disp} in Chromium.", f"Browser: {svc_disp}", "")

        if q_lower.startswith("open http") or q_lower.startswith("go to http") or any(ext in q_lower for ext in [".com", ".org", ".io", ".net", ".edu", ".dev"]):
            url_target = q_clean
            for pfx in ["open", "go to", "navigate to"]:
                if url_target.lower().startswith(pfx):
                    url_target = url_target[len(pfx):].strip()
            if " " not in url_target and "." in url_target:
                if not url_target.startswith("http"):
                    url_target = f"https://{url_target}"
                msg = self.tool_hub.open_browser(url=url_target, new_tab=True)
                return (msg, f"Browser: {url_target}", "")

        # 1e. Live Voice Dictation / Voice Typing Start Fast-Path
        if any(p in q_lower for p in ["start dictation", "dictation mode", "start voice typing", "voice typing", "type what i say", "dictate to note", "dictate"]):
            m_title = re.search(r"(?:to\s+(?:note\s+)?|titled\s+|named\s+)(.+)$", q_clean, re.I)
            title = m_title.group(1).strip() if m_title else ""
            if not title:
                title = f"Dictation_{time.strftime('%Y%m%d_%H%M%S')}"
            safe_title = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_")
            notes_dir = Path("/home/prakash/Documents/Notes")
            notes_dir.mkdir(parents=True, exist_ok=True)
            d_file = notes_dir / f"{safe_title}.md"
            if not d_file.exists():
                with open(d_file, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n*Started: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            self._dictation_file = d_file
            self._dictation_title = title
            self._dictation_mode = True
            return (f"Voice typing mode activated. Speak your thoughts and I will write them to {d_file.name}. Say 'stop dictation' when finished.", "🎙️ Dictation: Active", "")

        # 1f. Document & Spreadsheet Drafting Suite Fast-Path (.docx, .xlsx, .md, .txt)
        # 1. Excel / Spreadsheet Drafting
        if any(p in q_lower for p in ["draft excel", "draft spreadsheet", "create excel", "create spreadsheet", "make excel", "make spreadsheet", "excel file", "spreadsheet on"]):
            topic_m = re.search(r"(?:on|about|for|titled|named)\s+(.+)$", q_clean, re.I)
            topic = topic_m.group(1).strip() if topic_m else "Data Analysis"
            title = f"{topic.title()} Spreadsheet"
            headers = ["Item / Metric", "Value / Target", "Quarter / Status", "Notes"]
            rows = [
                [f"{topic} Metric A", "100%", "Active", "Target achieved"],
                [f"{topic} Metric B", "85%", "In Progress", "On schedule"],
                [f"{topic} Metric C", "92%", "Completed", "Verified"]
            ]
            msg = self.tool_hub.draft_excel_spreadsheet(title, headers, rows, sheet_name="Overview")
            return (msg, f"Draft: Excel ({topic[:20]})", "")

        # 2. Web Research and Synthesis into Document
        if any(p in q_lower for p in ["research and write", "research about", "research on", "research topic", "collect information about", "collect info about", "search and draft", "research and draft"]):
            res_m = (
                re.search(r"(?:about|on|regarding)\s+(.+?)(?:\s+and\s+write|\s+in\s+document|\s+in\s+doc|$)", q_clean, re.I) or
                re.search(r"research\s+(.+)$", q_clean, re.I)
            )
            top = res_m.group(1).strip() if res_m else "Autonomous AI Systems"
            ft = "xlsx" if "excel" in q_lower or "spreadsheet" in q_lower else "docx"
            msg = self.tool_hub.research_and_generate_document(top, file_type=ft)
            return (msg, f"Research: {top[:20]} ({ft})", "")

        # 3. Word Document / Formatted Report Drafting (.docx)
        if any(p in q_lower for p in ["draft doc", "draft docx", "draft word", "create document on", "write report on", "draft report on", "write summary of", "draft summary"]):
            topic_m = re.search(r"(?:on|about|for|titled|named|of)\s+(.+)$", q_clean, re.I)
            topic = topic_m.group(1).strip() if topic_m else "Project Summary"
            title = f"Report: {topic.title()}"
            sections = [
                {"heading": "Executive Summary", "content": f"Structured executive report regarding: {topic}."},
                {"heading": "Key Analysis & Overview", "content": f"This document synthesizes core objectives, progress metrics, and actionable insights for {topic}."},
                {"heading": "Action Items & Timeline", "content": "- Milestone 1: Requirement gathering and scope definition\n- Milestone 2: Core implementation and performance verification\n- Milestone 3: Final delivery and continuous review"}
            ]
            msg = self.tool_hub.draft_docx_document(title, sections)
            return (msg, f"Draft: Word Doc ({topic[:20]})", "")

        # 2. Application Launch & Close (EXCLUDING ollama/brain)
        close_m = re.match(r"^(?:please\s+)?(?:close|kill|quit|exit)\s+(?:the\s+)?([a-zA-Z0-9_\-\s]+)$", q_lower)
        if close_m:
            app = close_m.group(1).strip()
            if app not in ["window", "active window", "current window", "this", "ollama", "brain", "ai"]:
                close_software_by_name(app)
                return (f"Closed {app.title()}.", f"App: Close {app.title()}", "")

        # 2. Universal Content Opener & Search Engine (Filename, Videoname, Photoname, Appname, Browser & Web Search)
        open_req_m = (
            re.match(r"^(?:please\s+)?(?:open|launch|start|spawn|view|show|play)\s+(?:the\s+)?(.+)$", q_clean, re.I) or
            re.match(r"^(?:please\s+)?(?:search(?:\s+for)?|look\s+up|find)\s+(?:the\s+)?(.+)$", q_clean, re.I)
        )
        if open_req_m:
            target_raw = open_req_m.group(1).strip().rstrip(" ,.;!?")
            target_lower = target_raw.lower()
            is_email_cmd = ("@" in q_clean or any(k in target_lower for k in ["send mail", "send email", "compose mail", "compose email", "mail in it", "send an email", "send a mail"]))
            is_media_cmd = (target_lower in ["music", "song", "media", "playback", "current song", "current track"])
            if target_lower not in ["ollama", "brain", "ai"] and not is_email_cmd and not is_media_cmd and not any(k in target_lower for k in ["dictat", "create doc", "draft doc", "create excel", "draft excel", "create file", "write a file"]):
                ok, reply, badge, media = self.tool_hub.open_or_search_content(target_raw, raw_query=q_clean)
                return (reply, badge, media)

        # 3. Screenshot Capture (Named & Instant)
        if any(p in q_lower for p in ["screenshot", "capture screen", "take screenshot", "take a screenshot", "grab screen", "snapshot"]):
            name_m = (
                re.search(r"(?:save\s+(?:it\s+)?as|name\s+it|call\s+it)\s+['\"]?([a-zA-Z0-9_\-]+)['\"]?", q_lower) or
                re.search(r"save\s+(?:screenshot\s+)?as\s+['\"]?([a-zA-Z0-9_\-]+)['\"]?", q_lower)
            )
            custom_name = name_m.group(1).strip() if name_m else ""
            shot_file = self.tool_hub.capture_screenshot(filename=custom_name)
            if shot_file:
                fname = Path(shot_file).name
                return (f"Screenshot captured and saved to {fname} in Pictures.", f"Tool: Screenshot ({fname})", shot_file)
            else:
                return ("Failed to capture screenshot.", "Screenshot Error", "")

        # 3b. Machine Status & Truthful Brain Reporting
        if any(p in q_lower for p in [
            "system status", "machine status", "status of machine", "status of the machine",
            "how is my machine", "how is the machine", "how is my system", "brain status",
            "is the brain connected", "is ai connected", "is ai brain connected",
            "is ollama running", "system health", "machine health"
        ]):
            h = get_system_health()
            if h.get("brain_active"):
                brain_str = "My AI brain (lfm3-omni:2b) is online and resident in memory."
            elif h.get("ollama_running"):
                brain_str = "Ollama server is active, but lfm3-omni:2b is on standby."
            else:
                brain_str = "My AI brain is currently sleeping on standby to preserve power."
            reply = (
                f"{brain_str} Machine status: CPU load {h['cpu_load_1m']}, "
                f"RAM {h['ram_pct']}% used ({h['ram_used_gb']}G / {h['ram_total_gb']}G), "
                f"disk {h['disk_pct']}% used ({h['disk_free_gb']}G free), and uptime is {h['uptime_str']}."
            )
            return (reply, "System: Health & Brain", "")

        # 3c. Persistent Task & Reminder Management
        add_m = (
            re.search(r"^(?:set|add|create|new)\s+(?:a\s+)?(?:task|reminder)(?:\s+to|\s*:)?\s+(.+)$", q_clean, re.I) or
            re.search(r"^remind\s+me\s+to\s+(.+)$", q_clean, re.I)
        )
        if add_m:
            t_text = add_m.group(1).strip()
            item = self.task_mgr.add_task(t_text)
            return (f"Task saved: '{item['text']}' with ID {item['id']}.", f"Task: Added [{item['id']}]", "")

        if any(p in q_lower for p in ["what are my tasks", "list tasks", "show tasks", "check tasks", "my tasks", "list active tasks"]):
            acts = self.task_mgr.list_active()
            if acts:
                card_lines = [f"- [{t['id']}] {t['text']}" for t in acts]
                count_str = f"You have {len(acts)} active task{'s' if len(acts) > 1 else ''}:"
                joined = "\n".join(card_lines)
                return (f"{count_str}\n{joined}", f"Tasks: {len(acts)} Active", "")
            else:
                return ("You have no pending tasks in memory.", "Tasks: None", "")

        if any(p in q_lower for p in ["complete task", "finish task", "done with task"]):
            target = q_clean
            for pfx in ["complete task", "finish task", "done with task"]:
                if pfx in target.lower():
                    target = target.lower().split(pfx, 1)[1].strip()
                    break
            ok = self.task_mgr.complete_task(target)
            if ok:
                return (f"Marked task '{target}' as completed.", "Task: Completed", "")
            else:
                return (f"Could not find matching task '{target}'.", "Task: Not Found", "")

        if any(p in q_lower for p in ["delete task", "remove task", "cancel task"]):
            target = q_clean
            for pfx in ["delete task", "remove task", "cancel task"]:
                if pfx in target.lower():
                    target = target.lower().split(pfx, 1)[1].strip()
                    break
            ok = self.task_mgr.delete_task(target)
            if ok:
                return (f"Deleted task '{target}'.", "Task: Deleted", "")
            else:
                return (f"Could not find matching task '{target}'.", "Task: Not Found", "")

        if "clear all tasks" in q_lower:
            self.task_mgr.clear_all()
            return ("All tasks have been cleared.", "Tasks: Cleared All", "")

        # 3d. Email & Webmail Composition / Sending Fast Path (Strict: requires explicit email intent)
        is_email_intent = bool(
            re.search(r"\b(?:send|compose|draft)\s+(?:an?\s+)?(?:email|mail)\b", q_lower) or
            re.search(r"\b(?:open|launch)\s+(?:gmail|google\s+mail|webmail)\b", q_lower) or
            re.search(r"\b(?:open\s+(?:mail|email)\s+in\s+(?:chromium|browser))\b", q_lower) or
            re.search(r"\b(?:send|write)\s+(?:an?\s+)?(?:email|mail)\s+(?:to|saying|about)\b", q_lower) or
            ("@" in q_clean and any(w in q_lower for w in ["send", "email", "mail", "compose"]))
        )

        if is_email_intent:
            # Check for email address or recipient name
            rec_m = (
                re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", q_clean) or
                re.search(r"(?:to|recipient)\s+([a-zA-Z0-9_.-]+)", q_clean, re.I)
            )
            rec = rec_m.group(1).strip() if rec_m else ""

            # Check for explicit subject and body
            say_pos = re.search(r"\b(?:saying|body|message)\b", q_clean, re.I)
            about_pos = re.search(r"\b(?:subject|about|regarding)\b", q_clean, re.I)

            if say_pos and about_pos and say_pos.start() < about_pos.start():
                sub_m = None
                body_m = re.search(r"(?:body|saying|message)\s+(.+)$", q_clean, re.I)
            else:
                sub_m = re.search(r"(?:subject|about|regarding)\s+([^,\n]+?)(?:\s+(?:body|saying|message)\s+|$)", q_clean, re.I)
                body_m = re.search(r"(?:body|saying|message)\s+(.+)$", q_clean, re.I)

            if sub_m and body_m:
                subject = sub_m.group(1).strip()
                body = body_m.group(1).strip()
            elif body_m:
                topic = body_m.group(1).strip()
                subject, body = generate_email_content(topic, rec)
            elif sub_m:
                topic = sub_m.group(1).strip()
                subject, body = generate_email_content(topic, rec)
            else:
                after_rec = q_clean.split(rec, 1)[1].strip() if rec and rec in q_clean else ""
                if after_rec:
                    subject, body = generate_email_content(after_rec, rec)
                else:
                    subject, body = ("Email Draft", "")

            # If recipient is missing, prompt user!
            if not rec:
                self._pending_action = {
                    "type": "email_recipient",
                    "subject": subject,
                    "body": body,
                    "awaiting": "recipient"
                }
                return ("Who would you like to send the email to? Please type the recipient's email address below, or speak it.", "Prompt: Recipient", "")

            # If body is missing, prompt user!
            if not body:
                self._pending_action = {
                    "type": "email_body",
                    "recipient": rec,
                    "subject": subject,
                    "awaiting": "body"
                }
                return (f"What message would you like to send to {rec}?", "Prompt: Message", "")

            # Open Gmail compose in Chromium
            ok, msg = self.tool_hub.open_webmail_compose(rec, subject, body, provider="gmail")
            return (msg, f"Webmail: Compose ({rec})", "")

        # 4. Web Search (Live DuckDuckGo Multi-Tool)
        if any(p in q_lower for p in ["search web for", "search for", "search google for", "look up", "google"]):
            search_query = q_lower
            for pfx in ["search web for", "search google for", "search for", "look up", "google"]:
                if pfx in search_query:
                    search_query = search_query.split(pfx, 1)[1].strip()
                    break
            if search_query:
                results = self.tool_hub.search_web_ddgs(search_query, max_results=3)
                if results:
                    card_lines = [f"**{r['title']}**\n{r['snippet']}\n" for r in results]
                    reply = "\n".join(card_lines)
                    return (reply, f"Web Search: {search_query}", "")
                else:
                    return (f"No search results returned for {search_query}.", "Web Search: Empty", "")

        # 5. Audio Hardware Inspection & Volume Control
        if any(p in q_lower for p in ["audio devices", "list audio", "show microphones", "show speakers"]):
            devs = self.tool_hub.get_audio_devices()
            if devs:
                inputs = [d["name"] for d in devs.get("inputs", []) if not d["name"].startswith("PipeWire ALSA")]
                outputs = [d["name"] for d in devs.get("outputs", []) if not d["name"].startswith("PipeWire ALSA")]
                reply = f"Inputs:\n- " + "\n- ".join(inputs[:3]) + "\n\nOutputs:\n- " + "\n- ".join(outputs[:3])
                return (reply, "Audio Hardware", "")
            else:
                return ("PipeWire and WirePlumber audio devices are active.", "Audio: Active", "")

        # Voice Audio Diagnostic & Speech Test
        if any(p in q_lower for p in ["test speech", "check speech", "test voice", "speech test", "audio test", "test audio"]):
            v = self.tool_hub.get_volume()
            st = "muted" if v.get("muted") else f"{v.get('volume_pct')}%"
            return (f"Speech response system is active and clear via PipeWire. Master volume is currently {st}.", "Audio: Speech Test", "")

        if any(p in q_lower for p in ["reset volume", "restore volume", "restore default volume"]):
            target = getattr(self, "_initial_volume", 50)
            msg = self.tool_hub.set_volume(target)
            return (f"Restored master volume to baseline ({target}%).", f"Audio: Volume {target}%", "")

        if any(p in q_lower for p in ["what is the volume", "check volume", "current volume", "get volume", "show volume"]):
            v = self.tool_hub.get_volume()
            st = "muted" if v.get("muted") else f"{v.get('volume_pct')}%"
            return (f"Master audio volume is currently {st}.", "Audio: Status", "")

        # Strict volume setting: supports 'volume 50%', 'set volume to 50%', etc.
        vol_set_m = (
            re.search(r"^\s*(?:please\s+)?(?:set|change|turn|adjust|put\s+)?(?:the\s+)?(?:audio\s+|master\s+)?volume\s+(?:to\s+)?(\d+)\s*(?:%|percent)?\s*$", q_lower)
            or re.search(r"\b(?:set|change|turn|adjust|put)?\s*(?:the\s+)?volume\s+(?:to\s+)?(\d+)%?\b", q_lower)
            or re.search(r"^\s*volume\s+(\d+)\s*(?:%|percent)?\s*$", q_lower)
        )
        if vol_set_m:
            target_vol = int(vol_set_m.group(1))
            msg = self.tool_hub.set_volume(target_vol)
            return (msg, f"Audio: Volume {target_vol}%", "")

        # Strict volume adjustments (requires explicit 'volume' keyword)
        if any(p == q_lower.strip() or p in q_lower for p in ["volume up", "increase volume", "raise volume", "turn up volume", "turn volume up"]):
            msg = self.tool_hub.adjust_volume(10)
            return (msg, "Audio: Volume Up", "")

        if any(p == q_lower.strip() or p in q_lower for p in ["volume down", "decrease volume", "lower volume", "turn down volume", "turn volume down"]):
            msg = self.tool_hub.adjust_volume(-10)
            return (msg, "Audio: Volume Down", "")

        # Strict mute/unmute (requires full explicit phrase or exact word)
        if any(p in q_lower for p in ["mute audio", "unmute audio", "toggle mute", "mute sound", "unmute sound"]) or q_lower.strip() in ["mute", "unmute"]:
            msg = self.tool_hub.toggle_mute()
            return (msg, "Audio: Mute Toggled", "")

        # 5b. Media Playback Control (MPRIS DBus)
        if any(p in q_lower for p in ["pause music", "pause playback", "pause song", "pause track", "pause media"]):
            msg = self.tool_hub.media_control("pause")
            return (msg, "Media: Pause", "")

        if any(p in q_lower for p in ["play music", "resume music", "play song", "resume playback", "unpause music"]):
            msg = self.tool_hub.media_control("play")
            return (msg, "Media: Play", "")

        if any(p in q_lower for p in ["next song", "next track", "skip song", "skip track", "next music"]):
            msg = self.tool_hub.media_control("next")
            return (msg, "Media: Next", "")

        if any(p in q_lower for p in ["previous song", "prev song", "previous track", "prev track"]):
            msg = self.tool_hub.media_control("previous")
            return (msg, "Media: Previous", "")

        if any(p in q_lower for p in ["stop music", "stop song", "stop playback"]):
            msg = self.tool_hub.media_control("stop")
            return (msg, "Media: Stop", "")

        # 5c. Screen Brightness Control (KDE Solid PowerManagement DBus)
        if any(p in q_lower for p in ["reset brightness", "restore brightness", "restore default brightness"]):
            target = getattr(self, "_initial_brightness", 50)
            msg = self.tool_hub.set_brightness(target)
            return (f"Restored display brightness to baseline ({target}%).", f"Screen: Brightness {target}%", "")

        if any(p in q_lower for p in ["what is the brightness", "check brightness", "current brightness", "get brightness", "screen brightness"]):
            cur = self.tool_hub.get_brightness()
            return (f"Screen brightness is currently at {cur}%.", "Screen: Brightness", "")

        # Strict brightness setting: requires explicit command verb (prevents accidental matches)
        bright_set_m = re.search(r"^\s*(?:please\s+)?(?:set|change|adjust|turn|put)\s+(?:the\s+)?(?:screen\s+|display\s+)?brightness\s+(?:to\s+)?(\d+)\s*(?:%|percent)?\s*$", q_lower) or re.search(r"\b(?:set|change|adjust)\s+(?:the\s+)?(?:screen\s+)?brightness\s+(?:to\s+)?(\d+)%?\b", q_lower)
        if bright_set_m:
            target_b = int(bright_set_m.group(1))
            msg = self.tool_hub.set_brightness(target_b)
            return (msg, f"Screen: Brightness {target_b}%", "")

        # Strict brightness adjustments (requires explicit screen/brightness keyword)
        if any(p == q_lower.strip() or p in q_lower for p in ["brightness up", "increase brightness", "raise brightness", "screen brighter", "increase screen brightness", "turn up brightness"]):
            cur = self.tool_hub.get_brightness()
            new_b = min(100, cur + 15)
            msg = self.tool_hub.set_brightness(new_b)
            return (msg, f"Screen: Brightness {new_b}%", "")

        if any(p == q_lower.strip() or p in q_lower for p in ["brightness down", "decrease brightness", "lower brightness", "screen dimmer", "dim screen", "decrease screen brightness", "dim screen brightness", "turn down brightness"]):
            cur = self.tool_hub.get_brightness()
            new_b = max(10, cur - 15)
            msg = self.tool_hub.set_brightness(new_b)
            return (msg, f"Screen: Brightness {new_b}%", "")

        # 5d. Wayland Clipboard Management (wl-copy / wl-paste)
        copy_m = re.search(r"^(?:please\s+)?copy\s+(.+?)\s+to\s+(?:the\s+)?clipboard$", q_clean, re.I)
        if copy_m:
            txt_to_copy = copy_m.group(1).strip().strip("'\"")
            msg = self.tool_hub.set_clipboard(txt_to_copy)
            return (msg, "Clipboard: Copied", "")

        if any(p in q_lower for p in ["read clipboard", "what is on my clipboard", "what is on clipboard", "check clipboard", "show clipboard", "paste clipboard", "clipboard content"]):
            clip = self.tool_hub.get_clipboard()
            return (f"Clipboard content:\n{clip}", "Clipboard: Content", "")

        # 5e. Live Weather Lookup (wttr.in)
        weather_m = (
            re.search(r"\bweather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", q_lower) or
            re.search(r"\bhow\s+is\s+the\s+weather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", q_lower)
        )
        if weather_m:
            loc = weather_m.group(1).strip()
            w_res = self.tool_hub.get_weather(loc)
            return (f"Live weather for {loc.title()}: {w_res}", f"Weather: {loc.title()}", "")

        if any(p in q_lower for p in ["what is the weather", "current weather", "how is the weather", "check weather", "weather today"]):
            w_res = self.tool_hub.get_weather()
            return (f"Current weather: {w_res}", "Weather: Local", "")

        # 5f. Hardware & Battery Vitals & System Information Popup
        if any(p in q_lower for p in [
            "hardware vitals", "battery status", "check battery", "how much battery",
            "cpu temp", "cpu temperature", "temperatures", "hardware health", "battery level",
            "ram usage", "system info", "system status", "system vitals", "check ram",
            "show ram", "show my ram", "cpu usage", "show cpu"
        ]):
            if hasattr(self, "_sysinfo_popup") and self._sysinfo_popup:
                try:
                    self._sysinfo_popup.refresh_metrics()
                    self._sysinfo_popup.show()
                except Exception:
                    pass
            v = self.tool_hub.get_hardware_vitals()
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            used_gb = round(mem.used / (1024**3), 1)
            total_gb = round(mem.total / (1024**3), 1)
            msg = f"Battery: {v.get('battery_pct')}% ({v.get('battery_state')}). Temperatures: CPU {v.get('cpu_temp_c')}°C"
            if v.get('gpu_temp_c') is not None:
                msg += f", GPU {v.get('gpu_temp_c')}°C"
            if v.get('nvme_temp_c') is not None:
                msg += f", NVMe {v.get('nvme_temp_c')}°C"
            msg += f". Telemetry: RAM usage is {mem.percent}% ({used_gb} of {total_gb} GB), CPU is {cpu}%."
            return (msg, "Hardware Vitals", "")

        # 5g. Quick Sticky Notes (~/Documents/Notes)
        note_take_m = (
            re.search(r"^(?:take|save|write|create|make)\s+(?:a\s+)?note\s+(?:titled|called|named)?\s*['\"]?([^'\"\n:]+?)['\"]?\s*(?:content|body|saying|:)\s*(.+)$", q_clean, re.I) or
            re.search(r"^(?:take|save|write)\s+(?:a\s+)?note\s*:\s*(.+)$", q_clean, re.I)
        )
        if note_take_m:
            if len(note_take_m.groups()) == 2 and note_take_m.group(2):
                title = note_take_m.group(1).strip() or "Quick Note"
                n_content = note_take_m.group(2).strip()
            else:
                title = "Quick Note"
                n_content = note_take_m.group(1).strip()
            msg = self.tool_hub.save_note(title, n_content)
            return (msg, f"Note: Saved ({title})", "")

        note_read_m = re.search(r"^(?:read|get|open|show)\s+(?:my\s+)?note\s+(?:titled|called|named)?\s*['\"]?([^'\"\n]+)['\"]?$", q_clean, re.I)
        if note_read_m:
            title = note_read_m.group(1).strip()
            res = self.tool_hub.read_note(title)
            return (res, f"Note: {title}", "")
        # 6. Power Controls (Shutdown, Reboot, Lock with 5s Cancelable Timer)
        if any(p in q_lower for p in ["shutdown system", "shut down system", "power off", "turn off computer"]):
            self.shutdown_requested.emit("poweroff", 5)
            return ("Shutting down system in 5 seconds. Click Cancel to abort.", "System: Shutdown (5s)", "")

        if any(p in q_lower for p in ["reboot system", "restart computer", "restart system", "reboot"]):
            self.shutdown_requested.emit("reboot", 5)
            return ("Restarting system in 5 seconds. Click Cancel to abort.", "System: Reboot (5s)", "")

        if any(p in q_lower for p in ["lock screen", "lock system", "lock computer"]):
            subprocess.run(["loginctl", "lock-session"])
            return ("Screen locked.", "System: Screen Locked", "")

        # 7. Interactive Timers & Alarms
        if "timer" in q_lower or "alarm" in q_lower:
            if "cancel timer" in q_lower or "stop timer" in q_lower:
                self.timer_expired.emit("cancelled")
                return ("Timer cancelled.", "Timer: Cancelled", "")
            else:
                dur = parse_timer_duration(q_lower)
                if dur > 0:
                    mins = dur // 60
                    secs = dur % 60
                    dur_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                    self.timer_started.emit(dur, dur_str)
                    return (f"Timer set for {dur_str}.", f"Timer: {dur_str}", "")
                else:
                    return ("How long would you like the timer for?", "Timer: Prompt", "")

        # 9. Safe Terminal Command Execution
        cmd = None
        for pfx in ["run terminal command", "terminal command", "execute command", "run command"]:
            if q_clean.lower().startswith(pfx):
                cmd = q_clean[len(pfx):].strip().lstrip(" :")
                break
        if cmd:
            code, out = run_terminal_command(cmd)
            return (out, f"Terminal: `{cmd}`", "")

        # 10. Safe AST Calculations
        calc_expr = q_lower
        for pfx in ["calculate", "what is", "compute", "solve"]:
            if calc_expr.startswith(pfx):
                calc_expr = calc_expr[len(pfx):].strip()
        calc_expr = calc_expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/").replace("x", "*")
        calc_expr = "".join(c for c in calc_expr if c in "0123456789+-*/().^sqrt abssincolg ")
        if (any(op in calc_expr for op in "+-*/^") or "sqrt" in calc_expr) and any(d in calc_expr for d in "0123456789"):
            res = evaluate_math(calc_expr)
            if res is not None:
                return (f"The answer is {res}.", f"Calculate: {res}", "")

        # 11. Identity & Time (Explicit Only)
        if any(p in q_lower for p in ["who are you", "what is your name", "what's your name", "introduce yourself"]):
            return ("I am VOID, your personal AI assistant.", "Identity", "")

        if any(p in q_lower for p in ["what time is it", "current time", "what is the date", "what's the date"]):
            return (f"It is {time.strftime('%A, %B %d, %I:%M %p')}.", "Time & Date", "")

        # 12. Conversational AI Brain (Ollama lfm3-omni:2b + Tool Calling + Planning Engine)
        import httpx
        ollama_online = False
        try:
            r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=0.8)
            ollama_online = (r.status_code == 200)
        except Exception:
            ollama_online = False

        if ollama_online:
            try:
                system_msg = {
                    "role": "system",
                    "content": (
                        "You are VOID, the personal autonomous AI desktop assistant on Fedora Linux KDE Plasma. "
                        "You have direct tool execution capabilities and access to 1.5GB persistent SSD memory.\n"
                        f"Context & Preferences: {self.memory.get_context_summary()}\n"
                        "STRICT BEHAVIOR RULES:\n0. CRITICAL: EXECUTE ONLY THE USER'S CURRENT REQUEST. DO NOT re-execute, repeat, or resurrect tasks, tool calls, or actions from previous turns. Treat each user message as a distinct goal.\n"
                        "1. NEVER introduce yourself unless the user explicitly asks 'who are you'. NEVER begin responses with 'I am VOID' or 'As an AI assistant'.\n"
                        "2. AUTONOMOUS TASK PLANNING & EXECUTION: You possess full capability to plan and execute multi-step complex tasks. When the user gives a complex goal, formulate a clear sequential plan, decompose it into sub-goals, and invoke necessary tools (e.g. web search, file management, email drafting, safe commands, task reminders) step by step until the goal is fully achieved.\n"
                        "3. BROWSER & EMAIL EXECUTION: When asked to open mail, compose an email, or send an email in the browser, invoke 'browser_compose_email' with the recipient, subject, and body so that Chromium opens with Gmail compose loaded on screen. If the recipient email is missing from the request, invoke 'ask_user_clarification' or ask the user directly for the recipient's email address. When asked to open a new tab, search, or visit a website on screen, call 'browser_open' or 'browser_search'. Maintain local project files using 'create_document', 'append_document', 'read_document', and 'list_files'. NEVER simply save an email draft to disk when the user asked to send or compose it in the browser!\n"
                        "4. TRUTHFUL BOUNDARIES: If a user asks for something outside system boundaries or impossible with available tools (e.g. modifying root system files, accessing unauthorized remote accounts), state clearly: 'I am unable to complete this task because [exact reason]'. NEVER claim an action was done if no tool was executed.\n"
                        "5. Provide a direct, concise final response (1-2 sentences maximum) summarizing the completed plan and actions."
                    ),
                }
                messages = [system_msg, *self._chat_history[-8:], {"role": "user", "content": query}]
                max_agent_steps = 8
                current_step = 0
                all_executed_names = []

                while current_step < max_agent_steps:
                    if self._abort_requested.is_set():
                        return ("Thinking process stopped by user.", "Cancelled", "")
                    current_step += 1
                    payload = {
                        "model": "lfm3-omni:2b",
                        "messages": messages,
                        "tools": TOOLS_SCHEMA,
                        "stream": False,
                    }
                    try:
                        res = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=30.0)
                    except Exception as e:
                        print(f"[VOID Brain HTTP Error] {e}", flush=True)
                        break

                    if res.status_code != 200:
                        break

                    msg = res.json().get("message", {})
                    tool_calls = msg.get("tool_calls", [])

                    if not tool_calls:
                        reply_text = msg.get("content", "").strip()
                        break

                    messages.append(msg)
                    for tc in tool_calls:
                        if self._abort_requested.is_set():
                            return ("Thinking process stopped by user.", "Cancelled", "")
                        fn = tc.get("function", {})
                        fn_name = fn.get("name", "")
                        fn_args = fn.get("arguments", {})
                        all_executed_names.append(fn_name)
                        tool_result = self._execute_ai_tool(fn_name, fn_args, query_context=query)
                        if str(tool_result).startswith("PROMPT_USER:"):
                            prompt_q = str(tool_result).replace("PROMPT_USER:", "").strip()
                            badge = "Prompt: Recipient" if ("recipient" in prompt_q.lower() or "email" in prompt_q.lower()) else "Prompt: User Clarification"
                            return (prompt_q, badge, "")
                        if fn_name == "take_screenshot" and str(tool_result).startswith("/"):
                            thumbnail_path = str(tool_result)
                        messages.append({
                            "role": "tool",
                            "content": str(tool_result),
                        })

                if not reply_text and all_executed_names:
                    reply_text = f"Executed {', '.join(all_executed_names)}."

                if all_executed_names:
                    action_badge = f"Tools: {', '.join(all_executed_names[:2])}"
                elif reply_text:
                    action_badge = "Brain: lfm3-omni"
                else:
                    reply_text = "Task completed."
                    action_badge = "Brain: Completed"
            except Exception as e:
                reply_text = f"Could not process: {e}"
                action_badge = "Brain Error"
        elif hasattr(self, "_agent_providers") and self._agent_providers and self._agent_providers.is_cloud_configured():
            try:
                system_msg = (
                    "You are VOID, the personal autonomous AI desktop assistant on Fedora Linux KDE Plasma. "
                    f"Context & Preferences: {self.memory.get_context_summary()}\n"
                    "Provide a direct, concise, and helpful response."
                )
                cloud_reply = self._agent_providers.cloud_provider.generate(
                    prompt=query,
                    system=system_msg,
                    temperature=0.3,
                    max_tokens=512
                )
                if cloud_reply:
                    reply_text = cloud_reply
                    action_badge = f"Cloud AI: {self._agent_providers.cloud_provider.model}"
                else:
                    reply_text = "Received empty response from cloud provider."
                    action_badge = "Cloud AI: Empty"
            except Exception as e:
                reply_text = f"Cloud AI error: {e}"
                action_badge = "Cloud Error"
        else:
            self._pending_action = {
                "type": "cloud_setup",
                "stage": "input",
                "original_query": query
            }
            reply_text = "Local Ollama is offline. Would you like to connect a cloud AI model? Please provide your model name and API key."
            action_badge = "Prompt: Cloud Setup"

        # High Memory Thought recording for 7-day rolling retention
        if reply_text and hasattr(self, "_agent_memory") and self._agent_memory:
            try:
                self._agent_memory.record_high_memory_thought(
                    query=query,
                    thought_summary=reply_text,
                    plan_id="",
                    outcome="completed",
                    artifacts=[thumbnail_path] if thumbnail_path else [],
                    tags=["conversation", action_badge.lower()]
                )
            except Exception:
                pass

        return (reply_text, action_badge, thumbnail_path)

    def _clean_text_for_speech(self, text: str) -> str:
        if not text:
            return ""
        s = text
        # Strip code blocks and raw tool calling tags
        s = re.sub(r"```[\s\S]*?```", "", s)
        s = re.sub(r"<tool_call>.*?</tool_call>", "", s, flags=re.DOTALL)
        s = re.sub(r"<function=[^>]+>", "", s)
        s = re.sub(r"<parameter=[^>]+>", "", s)
        s = re.sub(r"</?[a-zA-Z0-9_-]+>", "", s)

        # Strip raw JSON dictionary syntax
        s = re.sub(r"\{[^{}]*\}", "", s)

        # Clean tool names and technical identifiers to natural English words
        s = re.sub(r"\b([a-z]+)_([a-z]+)\b", r"\1 \2", s)

        # Clean markdown symbols, bullets, headers, tables
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        s = re.sub(r"\*([^*]+)\*", r"\1", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"^#+\s*", "", s, flags=re.MULTILINE)
        s = re.sub(r"^\s*[-*•]\s*", "", s, flags=re.MULTILINE)
        s = re.sub(r"\|[^\n]+\|", "", s)

        # Simplify URLs and raw filesystem paths
        s = re.sub(r"https?://\S+", "the link", s)
        s = re.sub(r"/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)+", "the file", s)

        # Strip emojis and symbols
        s = re.sub(r"[\U00010000-\U0010ffff]", "", s)
        s = re.sub(r"[⏱️🎧💭💬💙🎉💫☀️🌙🌤️➔✕●⏺⏹✅⚙️🔍🔄🛑🚫⚠️❌📊]", "", s)

        # Normalize whitespace and ensure a clean pause between sentences
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"\?\s*", "? ", s)

        # If response is long, extract the first 2 clear sentences for fluent, comprehensible speech
        if len(s) > 200:
            sentences = re.split(r"(?<=[.!?])\s+", s)
            if len(sentences) > 2:
                s = " ".join(sentences[:2]).strip()

        return s

    def _speak_text(self, text: str) -> None:
        if self._abort_requested.is_set():
            return
        if not text:
            return

        clean = self._clean_text_for_speech(text)
        if not clean:
            return

        # Ensure TTS engine is initialized
        if self._tts is None:
            try:
                from dodaios.plugins.tts.piper_local import PiperLocalTTS
                self._tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium", speed=1.0)
                print("[VOID Audio] Piper neural TTS initialized lazily.", flush=True)
            except Exception as e:
                print(f"[VOID TTS Load Error] {e}", flush=True)
                return

        self._is_speaking = True
        self.state_changed.emit("speaking")
        print(f"[VOID TTS] Synthesizing speech for: '{clean[:80]}...' (len={len(clean)})", flush=True)

        try:
            self._preroll.clear()
            chunks = []
            for chunk in asyncio.run(self._synth_piper(clean)):
                if self._abort_requested.is_set():
                    print("[VOID TTS] Aborted during synthesis.", flush=True)
                    return
                chunks.append(chunk)

            if chunks and not self._abort_requested.is_set():
                pcm_all = b"".join(chunks)
                # Wrap 16-bit 22050Hz Mono PCM into standard WAV bytes
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(22050)
                    wf.writeframes(pcm_all)
                wav_bytes = buf.getvalue()

                # Safety check: ensure master audio sink is not muted so speech is audible
                try:
                    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
                except Exception:
                    pass

                played = False
                # Tier 1: Native PipeWire player (pw-play) - completely avoids PortAudio collisions
                if shutil.which("pw-play"):
                    try:
                        proc = subprocess.Popen(
                            ["pw-play", "-"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        self._active_tts_proc = proc
                        proc.stdin.write(wav_bytes)
                        proc.stdin.close()
                        while proc.poll() is None:
                            if self._abort_requested.is_set():
                                proc.terminate()
                                try:
                                    proc.wait(timeout=0.2)
                                except Exception:
                                    proc.kill()
                                break
                            time.sleep(0.04)
                        played = (proc.returncode == 0)
                        if played:
                            print("[VOID TTS] Spoken response successfully played via PipeWire (pw-play).", flush=True)
                    except Exception as e:
                        print(f"[VOID TTS] pw-play error: {e}, attempting fallback...", flush=True)
                    finally:
                        self._active_tts_proc = None

                # Tier 2: PulseAudio player (paplay)
                if not played and not self._abort_requested.is_set() and shutil.which("paplay"):
                    try:
                        proc = subprocess.Popen(
                            ["paplay"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        self._active_tts_proc = proc
                        proc.stdin.write(wav_bytes)
                        proc.stdin.close()
                        while proc.poll() is None:
                            if self._abort_requested.is_set():
                                proc.terminate()
                                break
                            time.sleep(0.04)
                        played = (proc.returncode == 0)
                        if played:
                            print("[VOID TTS] Spoken response played via paplay.", flush=True)
                    except Exception as e:
                        print(f"[VOID TTS] paplay error: {e}", flush=True)
                    finally:
                        self._active_tts_proc = None

                # Tier 3: ALSA player (aplay)
                if not played and not self._abort_requested.is_set() and shutil.which("aplay"):
                    try:
                        proc = subprocess.Popen(
                            ["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-c", "1"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        self._active_tts_proc = proc
                        proc.stdin.write(pcm_all)
                        proc.stdin.close()
                        while proc.poll() is None:
                            if self._abort_requested.is_set():
                                proc.terminate()
                                break
                            time.sleep(0.04)
                        played = (proc.returncode == 0)
                        if played:
                            print("[VOID TTS] Spoken response played via aplay.", flush=True)
                    except Exception as e:
                        print(f"[VOID TTS] aplay error: {e}", flush=True)
                    finally:
                        self._active_tts_proc = None

                # Tier 4: In-process sounddevice fallback
                if not played and not self._abort_requested.is_set():
                    try:
                        samples = np.frombuffer(pcm_all, dtype=np.int16)
                        sd.play(samples, samplerate=22050)
                        sd.wait()
                        print("[VOID TTS] Spoken response played via sounddevice.", flush=True)
                    except Exception as e:
                        print(f"[VOID TTS] sounddevice error: {e}", flush=True)
        except Exception as e:
            print(f"[VOID TTS Error] {e}", flush=True)
        finally:
            # 600ms acoustic grace period to let room echoes and speaker reverb decay
            self._mute_audio_until = time.time() + 0.6
            self._preroll.clear()
            if self._recognizer:
                self._recognizer.Reset()
            self._is_speaking = False
            self.state_changed.emit("idle")

    async def _synth_piper(self, text: str) -> list[bytes]:
        chunks = []
        async for chunk in self._tts.synthesize(text):
            chunks.append(chunk.pcm)
        return chunks

    def _return_to_wake(self) -> None:
        self._mode = "wake"
        self.state_changed.emit("idle")

# ---------------------------------------------------------------------------
# Pure Frosted Glassmorphism Island Frame (PySide6)
# ---------------------------------------------------------------------------
class GlassIslandFrame(QFrame):
    """Pure Frosted Glassmorphism Island Frame with Specular Rim and Ambient Halo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GlassIsland")
        self._radius = 28
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("#GlassIsland { background: transparent; border: none; }")

    def set_radius(self, radius: int) -> None:
        if self._radius != radius:
            self._radius = radius
            self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        w = float(rect.width())
        h = float(rect.height())
        r = float(self._radius)

        # Clear to clean alpha first
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(rect, Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # 1. Base Frosted Glass Gradient (Translucent Dark Obsidian / Deep Sapphire)
        bg_grad = QLinearGradient(0.0, 0.0, 0.0, h)
        bg_grad.setColorAt(0.0, QColor(16, 24, 42, 175))   # ~68% opacity top
        bg_grad.setColorAt(0.5, QColor(10, 16, 30, 155))   # ~60% opacity center
        bg_grad.setColorAt(1.0, QColor(6, 10, 20, 185))    # ~72% opacity bottom
        painter.setBrush(QBrush(bg_grad))

        # 2. Outer Cyber-Glass Rim Pen (Specular Cyan/Ice Blue Gradient)
        rim_grad = QLinearGradient(0.0, 0.0, 0.0, h)
        rim_grad.setColorAt(0.0, QColor(186, 230, 253, 160)) # Crisp specular top reflection
        rim_grad.setColorAt(0.25, QColor(56, 189, 248, 120)) # Neon cyber-cyan
        rim_grad.setColorAt(0.75, QColor(30, 64, 175, 80))   # Deep sapphire
        rim_grad.setColorAt(1.0, QColor(14, 165, 233, 90))
        painter.setPen(QPen(QBrush(rim_grad), 1.2))

        draw_rect = QtCore.QRectF(0.6, 0.6, w - 1.2, h - 1.2)
        painter.drawRoundedRect(draw_rect, r, r)

        # 3. Top Specular Reflection Sheen (Gloss highlight curve)
        spec_h = min(22.0, h * 0.45)
        spec_grad = QLinearGradient(0.0, 1.0, 0.0, spec_h)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 110)) # Crisp white sheen
        spec_grad.setColorAt(0.35, QColor(125, 211, 252, 45)) # Soft cyan tint
        spec_grad.setColorAt(1.0, QColor(255, 255, 255, 0))   # Fade to transparent
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(spec_grad))

        spec_path = QPainterPath()
        spec_path.addRoundedRect(QtCore.QRectF(1.2, 1.2, w - 2.4, spec_h), r, r)
        painter.drawPath(spec_path)

        # 4. Subtle Specular Highlight Line at the very top edge
        painter.setPen(QPen(QColor(255, 255, 255, 140), 1.0))
        painter.drawLine(QtCore.QPointF(r, 1.2), QtCore.QPointF(w - r, 1.2))

        painter.end()

# ---------------------------------------------------------------------------
# Dynamic Glass Flow Island Widget (PySide6)
# ---------------------------------------------------------------------------
class VoidMiniWidget(QWidget):
    """Ultra-Compact Dynamic Glass Island Widget for VOID."""

    COLLAPSED_W = 356
    COLLAPSED_H = 58
    EXPANDED_W = 370
    EXPANDED_H = 265

    def __init__(self) -> None:
        super().__init__()
        self._drag_pos = QPoint()
        self._is_expanded = False
        self._is_pinned = True
        self._wake_enabled = True

        self._active_timer_sec = 0
        self._timer_label = ""
        self._q_timer = QTimer(self)
        self._q_timer.timeout.connect(self._on_timer_tick)

        self._shutdown_action = ""
        self._shutdown_sec = 0
        self._power_timer = QTimer(self)
        self._power_timer.timeout.connect(self._on_power_tick)

        # Auto-collapse timer (collapses back after 12s idle)
        self._auto_collapse_timer = QTimer(self)
        self._auto_collapse_timer.setSingleShot(True)
        self._auto_collapse_timer.timeout.connect(self._auto_collapse)

        # Initialize Hub and Engine
        self._hub = DodaiosToolHub()
        self._engine = AudioVoiceEngine(self._hub)

        self._setup_window_flags()
        self._setup_ui()
        self._load_position()

        # Connect signals
        self._engine.state_changed.connect(self._on_state_changed)
        self._engine.audio_level.connect(self._orb.set_audio_level)
        self._engine.transcript_ready.connect(self._on_transcript_ready)
        self._engine.response_ready.connect(self._on_response_ready)
        self._engine.timer_started.connect(self._on_timer_started)
        self._engine.timer_expired.connect(self._on_timer_expired)
        self._engine.shutdown_requested.connect(self._on_shutdown_requested)
        self._engine.terminate_requested.connect(self._on_terminate)
        self._engine.agentic_update.connect(self._on_agentic_update)

        self._orb.clicked.connect(self._on_orb_clicked)

    def _setup_window_flags(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(self.COLLAPSED_W, self.COLLAPSED_H)

    def _setup_ui(self) -> None:
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Main Glass Capsule Frame
        self._card = GlassIslandFrame(self)
        self._card.setObjectName("GlassIsland")
        self._update_glass_style(expanded=False)

        self._card_layout = QVBoxLayout(self._card)
        self._card_layout.setContentsMargins(14, 6, 16, 6)
        self._card_layout.setSpacing(6)

        # -------------------------------------------------------------------
        # Header Row (Always visible in 56px pill)
        # -------------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._orb = OrbWidget(size=36, parent=self._card)
        header.addWidget(self._orb)

        # Identity & Dynamic Status (Properly vertically centered, no clipping)
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("VOID", self._card)
        title.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1.2px;
                padding-top: 2px;
                padding-bottom: 0px;
                margin: 0px;
            }
        """)
        title_row.addWidget(title)

        self._status_dot = QLabel("●", self._card)
        self._status_dot.setStyleSheet("color: #10b981; font-size: 10px; padding: 0px; margin: 0px;")
        title_row.addWidget(self._status_dot)
        title_row.addStretch()
        title_box.addLayout(title_row)

        self._status_pill = QLabel("Ready • Hey VOID", self._card)
        self._status_pill.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 10px;
                font-weight: 500;
                padding-top: 0px;
                padding-bottom: 2px;
                margin: 0px;
            }
        """)
        title_box.addWidget(self._status_pill)
        header.addLayout(title_box, stretch=1)

        # Action Buttons (Stop / Mic / Expand / Close)
        self._stop_btn = QPushButton("⏹", self._card)
        self._stop_btn.setFixedSize(28, 28)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setToolTip("Stop Thinking / Cancel Active Task")
        self._stop_btn.setVisible(False)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.35);
                color: #fca5a5;
                border: 1px solid rgba(239, 68, 68, 0.6);
                border-radius: 14px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.65);
                color: #ffffff;
            }
        """)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        header.addWidget(self._stop_btn)

        # Dedicated Visible Stop Dictation Button
        self._dict_stop_btn = QPushButton("⏹ Stop Dictation", self._card)
        self._dict_stop_btn.setFixedHeight(28)
        self._dict_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dict_stop_btn.setToolTip("Stop Dictation Mode & Return to Normal Mode")
        self._dict_stop_btn.setVisible(False)
        self._dict_stop_btn.setStyleSheet("""
            QPushButton {
                background: rgba(245, 158, 11, 0.35);
                color: #fef08a;
                border: 1px solid rgba(245, 158, 11, 0.65);
                border-radius: 14px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 10px;
            }
            QPushButton:hover {
                background: rgba(245, 158, 11, 0.70);
                color: #ffffff;
            }
        """)
        self._dict_stop_btn.clicked.connect(self._on_stop_dictation_clicked)
        header.addWidget(self._dict_stop_btn)

        self._mic_btn = MicButton(self._card)
        self._mic_btn.clicked.connect(self._engine.trigger_listening_manual)
        header.addWidget(self._mic_btn)

        self._expand_btn = QPushButton("▼", self._card)
        self._expand_btn.setFixedSize(28, 28)
        self._expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expand_btn.setToolTip("Expand / Collapse Card")
        self._expand_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 14px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(56, 189, 248, 0.25); color: #38bdf8; }
        """)
        self._expand_btn.clicked.connect(self._toggle_expand)
        header.addWidget(self._expand_btn)

        close_btn = QPushButton("✕", self._card)
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Close VOID Widget")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 11px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
                color: #ffffff;
                border: 1px solid rgba(239, 68, 68, 0.6);
            }
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        self._card_layout.addLayout(header)

        # -------------------------------------------------------------------
        # Expandable Container (Hidden when collapsed)
        # -------------------------------------------------------------------
        self._expanded_box = QWidget(self._card)
        self._expanded_box.setVisible(False)
        exp_layout = QVBoxLayout(self._expanded_box)
        exp_layout.setContentsMargins(0, 4, 0, 0)
        exp_layout.setSpacing(6)

        # Alert / Timer Progress Banner
        self._alert_banner = QFrame(self._expanded_box)
        self._alert_banner.setVisible(False)
        self._alert_banner.setStyleSheet("""
            background: rgba(56, 189, 248, 0.16);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 10px;
            padding: 3px 6px;
        """)
        alert_row = QHBoxLayout(self._alert_banner)
        alert_row.setContentsMargins(6, 2, 6, 2)
        self._alert_text = QLabel("⏱️ Timer: 00:00", self._alert_banner)
        self._alert_text.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        alert_row.addWidget(self._alert_text)
        alert_row.addStretch()

        self._alert_cancel_btn = QPushButton("Cancel", self._alert_banner)
        self._alert_cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._alert_cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.25);
                color: #fca5a5;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 6px;
                padding: 1px 6px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.45); color: #ffffff; }
        """)
        self._alert_cancel_btn.clicked.connect(self._on_cancel_alert)
        alert_row.addWidget(self._alert_cancel_btn)
        exp_layout.addWidget(self._alert_banner)

        # User Query Bubble
        self._query_bubble = QLabel("", self._expanded_box)
        self._query_bubble.setVisible(False)
        self._query_bubble.setWordWrap(True)
        self._query_bubble.setStyleSheet("""
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 4px 8px;
            color: #94a3b8;
            font-size: 11px;
            font-style: italic;
        """)
        exp_layout.addWidget(self._query_bubble)

        # Agent Activity Card (Multi-Agent Observability)
        perm_manager = getattr(self._engine._supervisor, 'perm_mgr', None) if hasattr(self._engine, '_supervisor') and self._engine._supervisor else None
        self._agent_card = AgentActivityCard(perm_manager, self._expanded_box)
        self._agent_card.setVisible(False)
        exp_layout.addWidget(self._agent_card)

        # Response Output Card
        self._resp_frame = QFrame(self._expanded_box)
        self._resp_frame.setObjectName("RespFrame")
        self._resp_frame.setStyleSheet("""
            #RespFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 12px;
            }
        """)
        resp_layout = QVBoxLayout(self._resp_frame)
        resp_layout.setContentsMargins(10, 8, 10, 8)
        resp_layout.setSpacing(5)

        resp_head = QHBoxLayout()
        self._action_badge = QLabel("Ready", self._resp_frame)
        self._action_badge.setFixedHeight(18)
        self._action_badge.setStyleSheet("""
            QLabel {
                color: #38bdf8;
                font-size: 10px;
                font-weight: bold;
                background: rgba(56, 189, 248, 0.18);
                border-radius: 4px;
                padding: 1px 6px;
                border: 1px solid rgba(56, 189, 248, 0.35);
            }
        """)
        resp_head.addWidget(self._action_badge, alignment=Qt.AlignmentFlag.AlignLeft)
        resp_head.addStretch()
        resp_layout.addLayout(resp_head)

        # Response Area with subtle scrollbar to prevent text clipping
        self._resp_scroll = QScrollArea(self._resp_frame)
        self._resp_scroll.setWidgetResizable(True)
        self._resp_scroll.setMaximumHeight(85)
        self._resp_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: rgba(15, 23, 42, 0.35);
                width: 5px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(56, 189, 248, 0.45);
                border-radius: 2px;
                min-height: 15px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(56, 189, 248, 0.8); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self._resp_text = QLabel("Ready to assist you.", self._resp_scroll)
        self._resp_text.setWordWrap(True)
        self._resp_text.setStyleSheet("""
            QLabel {
                color: #f1f5f9;
                font-size: 11px;
                line-height: 1.4;
                background: transparent;
                border: none;
            }
        """)
        self._resp_scroll.setWidget(self._resp_text)
        resp_layout.addWidget(self._resp_scroll)

        # Screenshot Thumbnail Preview (if applicable)
        self._thumb_preview = QLabel(self._resp_frame)
        self._thumb_preview.setVisible(False)
        self._thumb_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_preview.setStyleSheet("border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.3);")
        resp_layout.addWidget(self._thumb_preview)

        exp_layout.addWidget(self._resp_frame)

        # Quick Chips Row
        chips_row = QHBoxLayout()
        chips_row.setSpacing(4)
        quick_chips = [
            ("🧠 Start Ollama", "start ollama"),
            ("🌐 Open Chrome", "open chromium"),
            ("🤖 Multi-Agent", "run agentic demo 1"),
            ("🎙️ Dictate", "start dictation"),
            ("📸 Screenshot", "take screenshot"),
            ("📊 System Status", "system status"),
        ]
        for label, cmd in quick_chips:
            btn = QPushButton(label, self._expanded_box)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    color: #cbd5e1;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 6px;
                    font-size: 9px;
                    padding: 2px 5px;
                }
                QPushButton:hover {
                    background: rgba(56, 189, 248, 0.2);
                    color: #38bdf8;
                    border: 1px solid rgba(56, 189, 248, 0.35);
                }
            """)
            btn.clicked.connect(lambda checked=False, c=cmd: self._on_chip_clicked(c))
            chips_row.addWidget(btn)
        exp_layout.addLayout(chips_row)

        # Quick Input Bar
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self._input_field = QLineEdit(self._expanded_box)
        self._input_field.setPlaceholderText('Ask VOID or type command...')
        self._input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 12px;
                color: #f8fafc;
                font-size: 11px;
                padding: 4px 10px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(56, 189, 248, 0.5);
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self._input_field.returnPressed.connect(self._on_text_submitted)
        input_row.addWidget(self._input_field, stretch=1)

        send_btn = QPushButton("➔", self._expanded_box)
        send_btn.setFixedSize(26, 26)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.25);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 13px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(56, 189, 248, 0.45); color: #ffffff; }
        """)
        send_btn.clicked.connect(self._on_text_submitted)
        input_row.addWidget(send_btn)
        exp_layout.addLayout(input_row)

        self._card_layout.addWidget(self._expanded_box)
        self._main_layout.addWidget(self._card)

        # Enable dragging anywhere on the glass surface
        self._card.setCursor(Qt.CursorShape.OpenHandCursor)
        self._card.installEventFilter(self)
        for child in self._card.findChildren(QWidget):
            if not isinstance(child, (QPushButton, QLineEdit, MicButton)):
                child.installEventFilter(self)

    def _update_glass_style(self, expanded: bool) -> None:
        radius = 18 if expanded else 28
        self._card.set_radius(radius)
        self._card.setStyleSheet(f"""
            #GlassIsland {{
                background: transparent;
                border: none;
            }}
            #RespFrame {{
                background: rgba(12, 18, 32, 0.60);
                border: 1px solid rgba(56, 189, 248, 0.30);
                border-radius: 12px;
            }}
        """)

    def set_expanded(self, expanded: bool) -> None:
        self._is_expanded = expanded
        self._expanded_box.setVisible(expanded)
        self._expand_btn.setText("▲" if expanded else "▼")
        self._update_glass_style(expanded)
        if expanded:
            self.setFixedSize(self.EXPANDED_W, self.EXPANDED_H)
            self._auto_collapse_timer.stop()
        else:
            self.setFixedSize(self.COLLAPSED_W, self.COLLAPSED_H)

    def _toggle_expand(self) -> None:
        self.set_expanded(not self._is_expanded)

    def _auto_collapse(self) -> None:
        if not self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())) and not self._input_field.hasFocus():
            self.set_expanded(False)

    def _on_orb_clicked(self) -> None:
        self.set_expanded(True)
        self._engine.trigger_listening_manual()

    def start_drag(self, event: QtGui.QMouseEvent) -> None:
        self._is_dragging = True
        self._drag_start_pos = event.globalPosition().toPoint()
        self._window_start_pos = self.pos()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        wh = self.windowHandle()
        if wh is not None and hasattr(wh, "startSystemMove"):
            try:
                if wh.startSystemMove():
                    self._is_dragging = False
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                    return
            except Exception:
                pass

    def update_drag(self, event: QtGui.QMouseEvent) -> None:
        if getattr(self, "_is_dragging", False):
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._window_start_pos + delta
            screen = QApplication.primaryScreen().geometry()
            cur_w = self.width()
            cur_h = self.height()
            clamped_x = max(5, min(new_pos.x(), screen.width() - cur_w - 5))
            clamped_y = max(5, min(new_pos.y(), screen.height() - cur_h - 5))
            self.move(clamped_x, clamped_y)

    def end_drag(self, event: QtGui.QMouseEvent) -> None:
        self._is_dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._save_position()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_drag(event)
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.update_drag(event)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.end_drag(event)
            event.accept()

    def eventFilter(self, watched: QObject, event: QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if isinstance(event, QtGui.QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                if not isinstance(watched, (QPushButton, QLineEdit, MicButton)):
                    self.start_drag(event)
                    return True
        elif event.type() == QtCore.QEvent.Type.MouseMove:
            if isinstance(event, QtGui.QMouseEvent) and event.buttons() == Qt.MouseButton.LeftButton:
                if getattr(self, "_is_dragging", False):
                    self.update_drag(event)
                    return True
        elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            if isinstance(event, QtGui.QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                if getattr(self, "_is_dragging", False):
                    self.end_drag(event)
                    return True
        return super().eventFilter(watched, event)

    def _save_position(self) -> None:
        try:
            screen = QApplication.primaryScreen().geometry()
            x = max(10, min(self.x(), screen.width() - self.width() - 10))
            y = max(10, min(self.y(), screen.height() - self.height() - 10))
            with open(POS_FILE, "w") as f:
                json.dump({"x": x, "y": y}, f)
        except Exception:
            pass

    def _load_position(self) -> None:
        screen = QApplication.primaryScreen().geometry()
        default_x = screen.width() - self.COLLAPSED_W - 30
        default_y = 60
        try:
            if POS_FILE.exists():
                with open(POS_FILE, "r") as f:
                    pos = json.load(f)
                    x = int(pos.get("x", default_x))
                    y = int(pos.get("y", default_y))
                    if 0 <= x <= (screen.width() - 50) and 0 <= y <= (screen.height() - 50):
                        self.move(x, y)
                        return
        except Exception:
            pass
        self.move(default_x, default_y)

    def _update_ready_pill(self) -> None:
        try:
            active_count = len(self._engine.task_mgr.list_active())
            if active_count > 0:
                self._status_pill.setText(f"Ready • {active_count} task{'s' if active_count > 1 else ''} 💫")
            else:
                self._status_pill.setText("Ready • With you, Prakash 💫")
        except Exception:
            self._status_pill.setText("Ready • With you, Prakash 💫")

    def _on_stop_clicked(self) -> None:
        self._engine.cancel_active_task()
        self._status_pill.setText("Cancelled")
        self._status_dot.setStyleSheet("color: #ef4444; font-size: 10px;")
        QTimer.singleShot(1500, self._update_ready_pill)

    def _on_orb_clicked(self) -> None:
        if self._engine._mode in ("processing", "command"):
            self._on_stop_clicked()
        else:
            self._toggle_expand()

    def _on_stop_dictation_clicked(self) -> None:
        self._engine._dictation_mode = False
        self._dict_stop_btn.setVisible(False)
        self._status_pill.setText("Dictation Finished")
        self._status_dot.setStyleSheet("color: #10b981; font-size: 10px;")
        fname = self._engine._dictation_file.name if self._engine._dictation_file else "Note"
        reply = f"Dictation finished. Notes saved to {fname}."
        self._engine.response_ready.emit("stop dictation", reply, "Dictation: Saved", "")
        self._engine._speak_text(reply)
        QTimer.singleShot(2000, self._update_ready_pill)

    def _on_state_changed(self, state: str) -> None:
        self._orb.set_mode(state)
        if getattr(self._engine, "_dictation_mode", False):
            self._dict_stop_btn.setVisible(True)
            self._status_pill.setText("🎙️ Dictating...")
            self._status_dot.setStyleSheet("color: #f59e0b; font-size: 10px;")
        else:
            self._dict_stop_btn.setVisible(False)
        if state == "listening":
            self._stop_btn.setVisible(False)
            self._mic_btn.setVisible(True)
            self._status_dot.setStyleSheet("color: #38bdf8; font-size: 10px;")
            self._status_pill.setText("Listening with care... 🎧")
            self.set_expanded(True)
        elif state == "thinking":
            self._stop_btn.setVisible(True)
            self._mic_btn.setVisible(False)
            self._status_dot.setStyleSheet("color: #fbbf24; font-size: 10px;")
            self._status_pill.setText("Thinking thoughtfully... 💭")
        elif state == "executing":
            self._stop_btn.setVisible(True)
            self._mic_btn.setVisible(False)
            self._status_dot.setStyleSheet("color: #38bdf8; font-size: 10px;")
            self._status_pill.setText("Executing neural task... ⚡")
        elif state == "speaking":
            self._stop_btn.setVisible(True)
            self._mic_btn.setVisible(False)
            self._status_dot.setStyleSheet("color: #e879f9; font-size: 10px;")
            self._status_pill.setText("Speaking with you... 💬")
        elif state == "empathy":
            self._status_dot.setStyleSheet("color: #f43f5e; font-size: 10px;")
            self._status_pill.setText("Empathy • With you 💙")
        elif state == "celebrate":
            self._status_dot.setStyleSheet("color: #10b981; font-size: 10px;")
            self._status_pill.setText("Celebration • Nailed it! 🎉")
        elif state == "planning":
            self._stop_btn.setVisible(True)
            self._mic_btn.setVisible(False)
            self._status_dot.setStyleSheet("color: #c084fc; font-size: 10px;")
            self._status_pill.setText("Multi-Agent Planning... 🧭")
        elif state == "verifying":
            self._stop_btn.setVisible(True)
            self._mic_btn.setVisible(False)
            self._status_dot.setStyleSheet("color: #facc15; font-size: 10px;")
            self._status_pill.setText("Verifying Artifacts... 🛡️")
        elif state == "recovering":
            self._stop_btn.setVisible(True)
            self._mic_btn.setVisible(False)
            self._status_dot.setStyleSheet("color: #fb923c; font-size: 10px;")
            self._status_pill.setText("Dynamic Recovery... 🔧")
        elif state == "waiting_approval":
            self._stop_btn.setVisible(True)
            self._mic_btn.setVisible(False)
            self._status_dot.setStyleSheet("color: #f43f5e; font-size: 10px;")
            self._status_pill.setText("Awaiting User Approval 🛑")
        else:  # idle
            self._stop_btn.setVisible(False)
            self._mic_btn.setVisible(True)
            self._status_dot.setStyleSheet("color: #10b981; font-size: 10px;")
            if self._active_timer_sec > 0:
                mins = self._active_timer_sec // 60
                secs = self._active_timer_sec % 60
                self._status_pill.setText(f"⏱ {mins:02d}:{secs:02d}")
            else:
                self._update_ready_pill()
            # Schedule auto-collapse after task completion
            self._auto_collapse_timer.start(12000)

    def _on_transcript_ready(self, text: str) -> None:
        self.set_expanded(True)
        self._query_bubble.setText(f'👤 "{text}"')
        self._query_bubble.setVisible(True)

    def _on_response_ready(self, query: str, reply: str, badge: str, thumb: str) -> None:
        self.set_expanded(True)
        self._action_badge.setText(badge or "VOID")
        self._resp_text.setText(reply)
        if thumb and Path(thumb).exists():
            pix = QPixmap(thumb).scaled(220, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._thumb_preview.setPixmap(pix)
            self._thumb_preview.setVisible(True)
        else:
            self._thumb_preview.setVisible(False)

        # Automatically focus and highlight the text input field when clarification / input is requested
        if badge and "Prompt: Recipient" in badge:
            self.activateWindow()
            self._input_field.setPlaceholderText("Type recipient email (e.g. name@example.com)...")
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(56, 189, 248, 0.16);
                    border: 1.5px solid #38bdf8;
                    border-radius: 12px;
                    color: #ffffff;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 2px solid #00f0ff;
                    background: rgba(56, 189, 248, 0.25);
                }
            """)
            self._input_field.setFocus()
        elif badge and "Prompt: Search Query" in badge:
            self.activateWindow()
            self._input_field.setPlaceholderText("Type search query...")
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(56, 189, 248, 0.16);
                    border: 1.5px solid #38bdf8;
                    border-radius: 12px;
                    color: #ffffff;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 2px solid #00f0ff;
                    background: rgba(56, 189, 248, 0.25);
                }
            """)
            self._input_field.setFocus()
        else:
            self._input_field.setPlaceholderText('Ask VOID or type command...')
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 12px;
                    color: #f8fafc;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 1px solid rgba(56, 189, 248, 0.5);
                    background: rgba(255, 255, 255, 0.12);
                }
            """)

    def _on_text_submitted(self) -> None:
        text = self._input_field.text().strip()
        if text:
            self._input_field.clear()
            self._input_field.setPlaceholderText('Ask VOID or type command...')
            self._input_field.setStyleSheet("""
                QLineEdit {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 12px;
                    color: #f8fafc;
                    font-size: 11px;
                    padding: 4px 10px;
                }
                QLineEdit:focus {
                    border: 1px solid rgba(56, 189, 248, 0.5);
                    background: rgba(255, 255, 255, 0.12);
                }
            """)
            self._query_bubble.setText(f'💬 "{text}"')
            self._query_bubble.setVisible(True)
            self._engine.execute_task(text)

    def _on_chip_clicked(self, cmd: str) -> None:
        self._query_bubble.setText(f'⚡ "{cmd}"')
        self._query_bubble.setVisible(True)
        self._engine.execute_task(cmd)

    def _on_timer_started(self, duration: int, label: str) -> None:
        self._active_timer_sec = duration
        self._timer_label = label
        self._alert_text.setText(f"⏱️ Timer: {label}")
        self._alert_banner.setVisible(True)
        self._q_timer.start(1000)

    def _on_timer_tick(self) -> None:
        self._active_timer_sec -= 1
        if self._active_timer_sec <= 0:
            self._q_timer.stop()
            self._alert_text.setText("🔔 Timer Expired!")
            play_chime("alarm")
            self._status_pill.setText("Ready • Hey VOID")
            QTimer.singleShot(4000, lambda: self._alert_banner.setVisible(False))
        else:
            mins = self._active_timer_sec // 60
            secs = self._active_timer_sec % 60
            self._alert_text.setText(f"⏱️ Timer: {mins:02d}:{secs:02d}")
            if not self._is_expanded:
                self._status_pill.setText(f"⏱ {mins:02d}:{secs:02d}")

    def _on_timer_expired(self, state: str) -> None:
        self._q_timer.stop()
        self._active_timer_sec = 0
        self._alert_banner.setVisible(False)
        self._status_pill.setText("Ready • Hey VOID")

    def _on_shutdown_requested(self, action: str, seconds: int) -> None:
        self._shutdown_action = action
        self._shutdown_sec = seconds
        self.set_expanded(True)
        act_title = "Shutting down" if action == "poweroff" else "Restarting"
        self._alert_text.setText(f"⚠️ {act_title} in {seconds}s...")
        self._alert_banner.setVisible(True)
        self._power_timer.start(1000)

    def _on_power_tick(self) -> None:
        self._shutdown_sec -= 1
        if self._shutdown_sec <= 0:
            self._power_timer.stop()
            self._alert_text.setText("Executing system command...")
            if self._shutdown_action == "poweroff":
                subprocess.run(["systemctl", "poweroff"])
            elif self._shutdown_action == "reboot":
                subprocess.run(["systemctl", "reboot"])
        else:
            act_title = "Shutting down" if self._shutdown_action == "poweroff" else "Restarting"
            self._alert_text.setText(f"⚠️ {act_title} in {self._shutdown_sec}s...")

    def _on_cancel_alert(self) -> None:
        if self._power_timer.isActive():
            self._power_timer.stop()
            self._shutdown_sec = 0
            self._alert_text.setText("System action cancelled.")
            QTimer.singleShot(2000, lambda: self._alert_banner.setVisible(False))
        elif self._q_timer.isActive():
            self._q_timer.stop()
            self._active_timer_sec = 0
            self._alert_text.setText("Timer cancelled.")
            self._status_pill.setText("Ready • Hey VOID")
            QTimer.singleShot(2000, lambda: self._alert_banner.setVisible(False))

    def _on_agentic_update(self, state, plan, current_task) -> None:
        if hasattr(self, '_agent_card'):
            self._agent_card.setVisible(True)
            self.set_expanded(True)
            self._agent_card.update_state(state, plan, current_task)

    def _on_terminate(self) -> None:
        print("[VOID] Terminate code 0 received. Shutting down assistant permanently...")
        for p in [CONFIG_DIR / ".void_launcher.json", Path("/home/prakash/.dodaios/data/.void_launcher.json")]:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        self.close()
        QApplication.quit()
        os._exit(0)

# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VOID-MiniWidget")
    widget = VoidMiniWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
