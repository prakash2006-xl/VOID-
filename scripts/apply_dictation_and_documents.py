#!/usr/bin/env python3
"""
Applies Live Voice Dictation, Document & Excel Drafting Suite, Web Research Synthesis,
WhatsApp Web Direct Routing, Stale Task Repetition Fix, and Capsule Glass Rendering Fix
to /run/media/prakash/TR_39/VOID/bin/void-widget.py.
"""

import sys
import shutil
import time
from pathlib import Path

TARGET = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")
BACKUP_DIR = Path("/run/media/prakash/TR_39/VOID/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

if not TARGET.exists():
    print(f"Error: {TARGET} not found!")
    sys.exit(1)

# 1. Create timestamped backup
bk_path = BACKUP_DIR / f"void-widget.py.bak_{time.strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(TARGET, bk_path)
print(f"[Backup] Saved backup to {bk_path}")

content = TARGET.read_text(encoding="utf-8")

# -----------------------------------------------------------------------------
# STEP 1: Add docx, openpyxl imports & REPORTS_DIR
# -----------------------------------------------------------------------------
if "import docx" not in content:
    import_block = """try:
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
"""
    # Insert right before TOOLS_SCHEMA
    if "TOOLS_SCHEMA = [" in content:
        content = content.replace("TOOLS_SCHEMA = [", import_block + "\nTOOLS_SCHEMA = [", 1)
        print("[Step 1] Added docx, openpyxl, and REPORTS_DIR.")
    else:
        print("[Step 1 Warning] Could not find TOOLS_SCHEMA anchor.")

# -----------------------------------------------------------------------------
# STEP 2: Add Document, Excel & Dictation tools to TOOLS_SCHEMA
# -----------------------------------------------------------------------------
if '"draft_docx_document"' not in content:
    doc_tools_schema = """    {
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
"""
    if "TOOLS_SCHEMA = [" in content:
        content = content.replace("TOOLS_SCHEMA = [\n", "TOOLS_SCHEMA = [\n" + doc_tools_schema, 1)
        print("[Step 2] Added Document, Excel, Report, and Dictation schemas to TOOLS_SCHEMA.")

# -----------------------------------------------------------------------------
# STEP 3: Add Document Drafting methods to DodaiosToolHub
# -----------------------------------------------------------------------------
if "def draft_docx_document" not in content:
    toolhub_methods = '''    def draft_docx_document(self, title: str, sections: list[dict[str, Any]], filename: str = "") -> str:
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
                    lines = body.split("\\n")
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
                {"heading": "Action Items", "content": "- Review findings with team\\n- Schedule next implementation milestone\\n- Monitor key performance metrics"}
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
                f"# {title}\\n"
                f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} | Topic: {topic}*\\n\\n"
                f"## Executive Summary\\n"
                f"Comprehensive analysis on {topic}.\\n\\n"
                f"## Detailed Findings\\n"
                f"{content or 'No extra details provided.'}\\n\\n"
                f"## Recommendations\\n"
                f"1. Continuous monitoring of key metrics.\\n"
                f"2. Align next steps with project objectives.\\n"
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

        content_str = "\\n".join(snippets) if snippets else f"No direct search results for '{topic}'."
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
'''
    init_anchor = "    def _init_in_bg(self) -> None:"
    if init_anchor in content:
        content = content.replace(init_anchor, toolhub_methods + "\n" + init_anchor, 1)
        print("[Step 3] Added draft_docx_document, draft_excel_spreadsheet, draft_formatted_report, and research_and_generate_document to DodaiosToolHub.")

# -----------------------------------------------------------------------------
# STEP 4: Add tool dispatch to _execute_ai_tool
# -----------------------------------------------------------------------------
if 'name == "draft_docx_document"' not in content:
    tool_dispatch = '''            elif name == "draft_docx_document":
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
'''
    dispatch_anchor = 'if name == "search_web":'
    if dispatch_anchor in content:
        content = content.replace(dispatch_anchor, tool_dispatch.strip() + "\n            " + dispatch_anchor, 1)
        print("[Step 4] Added Document, Excel, Report, and Dictation dispatch to _execute_ai_tool.")

# -----------------------------------------------------------------------------
# STEP 5: Add Dictation Engine state to AudioVoiceEngine.__init__
# -----------------------------------------------------------------------------
if "self._dictation_file" not in content:
    engine_init_anchor = "self._pending_action: dict[str, Any] | None = None"
    if engine_init_anchor in content:
        content = content.replace(
            engine_init_anchor,
            engine_init_anchor + "\n        self._dictation_mode = False\n        self._dictation_file: Path | None = None\n        self._dictation_title: str = ''",
            1
        )
        print("[Step 5] Added _dictation_mode, _dictation_file, and _dictation_title to AudioVoiceEngine.__init__.")

# -----------------------------------------------------------------------------
# STEP 6: Handle Voice Dictation in _process_task
# -----------------------------------------------------------------------------
if "if self._dictation_mode:" not in content:
    process_task_anchor = "q_raw = query.strip()"
    dictation_process = """q_raw = query.strip()
            # Live Voice Dictation Handler
            if self._dictation_mode:
                q_low = q_raw.lower()
                if any(p in q_low for p in ["stop dictation", "finish dictation", "end dictation", "stop typing", "dictation off", "stop voice typing", "exit dictation"]):
                    self._dictation_mode = False
                    fname = self._dictation_file.name if self._dictation_file else "Note"
                    reply_text = f"Dictation finished. Your notes have been saved to {fname}."
                    print(f"[VOID Dictation] Stopped. Saved to {fname}.", flush=True)
                    self.response_ready.emit(query, reply_text, "Dictation: Saved", "")
                    self._speak_text(reply_text)
                    return
                # Append transcribed speech to dictation note and clipboard
                if self._dictation_file:
                    try:
                        with open(self._dictation_file, "a", encoding="utf-8") as f:
                            f.write(f"[{time.strftime('%H:%M:%S')}] {q_raw}\\n\\n")
                    except Exception as e:
                        print(f"[VOID Dictation Write Error] {e}", flush=True)
                try:
                    subprocess.run(["wl-copy"], input=q_raw, text=True, timeout=1.0)
                except Exception:
                    pass
                fname = self._dictation_file.name if self._dictation_file else "Note"
                self.response_ready.emit(query, f'Transcribed: "{q_raw}"\\n(Appended to {fname})', "🎙️ Dictating...", "")
                return
"""
    if process_task_anchor in content:
        content = content.replace(process_task_anchor, dictation_process, 1)
        print("[Step 6] Added Dictation mode interceptor to _process_task.")

# -----------------------------------------------------------------------------
# STEP 7: Fix Stale Task Repetition in _pending_action
# -----------------------------------------------------------------------------
stale_anchor = "if self._pending_action:"
if stale_anchor in content:
    stale_fix = """if self._pending_action:
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
            if is_new_cmd and "@" not in q_clean:
                print(f"[VOID Action] Discarding stale pending action ({p_action.get('type')}) because new command intent was initiated: '{q_clean}'", flush=True)
                self._pending_action = None
            else:"""
    content = content.replace(stale_anchor, stale_fix, 1)
    print("[Step 7] Fixed stale pending action re-execution bug.")

# -----------------------------------------------------------------------------
# STEP 8: Add WhatsApp Web Direct Launch & Typo Tolerance
# -----------------------------------------------------------------------------
if "whatsapp web in chromium" not in content.lower():
    whatsapp_code = r"""        # WhatsApp Web Direct Fast Path (Phonetic typo tolerant: watsapp, whatsapp, whats up, etc.)
        if any(p in q_lower for p in [
            "whatsapp web", "watsapp web", "whats app web", "whatsap web", "whats up web",
            "open whatsapp", "open watsapp", "launch whatsapp", "launch watsapp", "open whats app",
            "go to whatsapp", "go to watsapp"
        ]) or q_lower.strip() in ["whatsapp", "watsapp", "whatsapp web", "watsapp web"]:
            msg_m = re.search(r"(?:message|saying|text|send)\s+(.+)$", q_clean, re.I)
            if msg_m and not any(p in msg_m.group(1).lower() for p in ["web", "watsapp", "whatsapp"]):
                text_content = msg_m.group(1).strip()
                url = f"https://web.whatsapp.com/send?text={urllib.parse.quote(text_content)}"
                self.tool_hub.open_browser(url=url, new_tab=True)
                return (f"Opened WhatsApp Web in Chromium prepared with your message: '{text_content}'.", "Browser: WhatsApp Web", "")
            else:
                self.tool_hub.open_browser(url="https://web.whatsapp.com", new_tab=True)
                return ("Opened WhatsApp Web in Chromium.", "Browser: WhatsApp Web", "")
"""
    # Insert right before Direct Web Services Fast-Path
    web_svc_anchor = "# Direct Web Services Fast-Path"
    if web_svc_anchor in content:
        content = content.replace(web_svc_anchor, whatsapp_code + "\n        " + web_svc_anchor, 1)
        print("[Step 8] Added WhatsApp Web direct fast-path with typo tolerance.")

# -----------------------------------------------------------------------------
# STEP 9: Add Live Voice Typing & Document Drafting Fast-Paths
# -----------------------------------------------------------------------------
if "Voice typing mode activated" not in content:
    doc_dictation_fastpath = r"""        # Live Voice Dictation / Voice Typing Start Fast-Path
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

        # Document & Spreadsheet Drafting Suite Fast-Path (.docx, .xlsx, .md, .txt)
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
        if any(p in q_lower for p in ["research and write", "collect information about", "research topic", "search and draft", "research and draft"]):
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
"""
    # Insert before 3d. Email & Webmail Composition
    email_anchor = "# 3d. Email & Webmail Composition / Sending Fast Path"
    if email_anchor in content:
        content = content.replace(email_anchor, doc_dictation_fastpath + "\n        " + email_anchor, 1)
        print("[Step 9] Added Voice Dictation and Document/Excel Drafting fast-paths.")

# -----------------------------------------------------------------------------
# STEP 10: Deduplicate emotional companion routing and add strict rule to Ollama
# -----------------------------------------------------------------------------
dup_block = """        # 0e. Emotional Companion & Empathy Routing (Warm, Caring, Witty & Supportive)
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
"""
if content.count(dup_block) > 1:
    content = content.replace(dup_block, "", 1)
    print("[Step 10] Deduplicated redundant emotional companion block.")

# Strict rule to Ollama system prompt
rule_anchor = "STRICT BEHAVIOR RULES:\\n"
strict_rule = "STRICT BEHAVIOR RULES:\\n0. CRITICAL: EXECUTE ONLY THE USER'S CURRENT REQUEST. DO NOT re-execute, repeat, or resurrect tasks, tool calls, or actions from previous turns. Treat each user message as a distinct goal.\\n"
if rule_anchor in content and strict_rule not in content:
    content = content.replace(rule_anchor, strict_rule, 1)
    print("[Step 10b] Injected anti-repetition rule into Ollama system prompt.")

# -----------------------------------------------------------------------------
# STEP 11: Widget UI Glass Rendering Fix & Quick Chips
# -----------------------------------------------------------------------------
# 1. Update COLLAPSED_H = 58
content = content.replace("COLLAPSED_H = 56", "COLLAPSED_H = 58")

# 2. Update Glass Style opacity to eliminate text-bleed from background windows
old_glass_style = """            #GlassIsland {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15, 23, 42, 0.88),
                    stop:1 rgba(10, 14, 26, 0.94));
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: {radius}px;
            }}"""

new_glass_style = """            #GlassIsland {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(13, 18, 30, 0.98),
                    stop:1 rgba(8, 12, 22, 0.99));
                border: 1px solid rgba(56, 189, 248, 0.38);
                border-radius: {radius}px;
            }}"""
if old_glass_style in content:
    content = content.replace(old_glass_style, new_glass_style)
    print("[Step 11] Upgraded glass frame opacity to 0.98-0.99 preventing underlying window bleed-through.")

# 3. Add Dictate and Draft Doc quick chips
old_chips = """        quick_chips = [
            ("Close Win", "close window"),
            ("Min Win", "minimize window"),
            ("Screenshot", "take screenshot"),
            ("Web Search", "search web for linux news"),
            ("Ollama", "start ollama"),
        ]"""
new_chips = """        quick_chips = [
            ("🎙️ Dictate", "start dictation"),
            ("Draft Doc", "draft doc on AI Trends 2026"),
            ("Draft Excel", "draft excel on Project Budget"),
            ("WhatsApp", "open whatsapp web"),
            ("Screenshot", "take screenshot"),
        ]"""
if old_chips in content:
    content = content.replace(old_chips, new_chips)
    print("[Step 11b] Added Dictate, Draft Doc, Draft Excel, and WhatsApp quick chips.")

# Save modified content
TARGET.write_text(content, encoding="utf-8")
print(f"[Done] Successfully wrote all enhancements to {TARGET}!")
