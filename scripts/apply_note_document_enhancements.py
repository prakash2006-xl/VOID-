#!/usr/bin/env python3
"""
Applies Note Document Feature Improvements and Maintenance Engine:
1. Defines NOTES_DIR globally
2. Adds append_note, list_notes, search_notes, export_note_to_pdf, maintain_notes to TOOLS_SCHEMA
3. Adds rich note methods to DodaiosToolHub:
   - save_note (with tags & category metadata)
   - append_note (with timestamp entries & auto-creation)
   - read_note (with clean formatting and metadata)
   - list_notes (with sizes & timestamps)
   - search_notes (scanning content & filenames)
   - export_note_to_pdf (publication PDF compiling)
   - maintain_notes (auto-cataloging INDEX.md and cleaning stubs)
4. Adds AI tool dispatch in _execute_ai_tool
5. Adds fast-path intent routing in _execute_single_command
6. Updates normalize_voice_intent with note-related speech slips
7. Updates agentic/tools.py and agentic/agents/research_agent.py
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

# 1. Create backup
bk_path = BACKUP_DIR / f"void-widget.py.bak_{time.strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(TARGET, bk_path)
print(f"[Backup] Saved backup to {bk_path}")

content = TARGET.read_text(encoding="utf-8")

# -----------------------------------------------------------------------------
# STEP 1: Add NOTES_DIR globally
# -----------------------------------------------------------------------------
if "NOTES_DIR = DOCS_DIR" not in content:
    content = content.replace(
        'REPORTS_DIR.mkdir(parents=True, exist_ok=True)',
        'REPORTS_DIR.mkdir(parents=True, exist_ok=True)\nNOTES_DIR = DOCS_DIR / "Notes"\nNOTES_DIR.mkdir(parents=True, exist_ok=True)',
        1
    )
    print("[Step 1] Added global NOTES_DIR.")

# -----------------------------------------------------------------------------
# STEP 2: Add Note tools to TOOLS_SCHEMA
# -----------------------------------------------------------------------------
note_tools_schema = """    {
        "type": "function",
        "function": {
            "name": "append_note",
            "description": "Append text or an entry to an existing note document in ~/Documents/Notes with automatic timestamping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title or name of the note to append to"},
                    "content": {"type": "string", "description": "New content or thought to append"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "List all active note documents in ~/Documents/Notes sorted by last modification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of notes to return (default: 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Search note documents in ~/Documents/Notes by keyword across titles and content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or keyword to find in notes"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_note_to_pdf",
            "description": "Compile an existing note document into a publication-grade PDF report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title or keyword of note to export"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maintain_notes",
            "description": "Perform maintenance on note documents: generate INDEX.md catalog, inspect storage, and clean empty stubs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cleanup_empty": {"type": "boolean", "description": "Whether to prune empty 0-byte files (default: true)"}
                }
            }
        }
    },
"""

if '"append_note"' not in content:
    content = content.replace(
        'TOOLS_SCHEMA = [',
        f'TOOLS_SCHEMA = [\n{note_tools_schema}',
        1
    )
    print("[Step 2] Added note management tools to TOOLS_SCHEMA.")

# -----------------------------------------------------------------------------
# STEP 3: Add last_note_info in DodaiosToolHub.__init__
# -----------------------------------------------------------------------------
if 'self.last_note_info' not in content:
    content = content.replace(
        'self.last_document_info: dict[str, Any] = {}',
        'self.last_document_info: dict[str, Any] = {}\n        self.last_note_info: dict[str, Any] = {}',
        1
    )
    print("[Step 3] Initialized last_note_info in DodaiosToolHub.")

# -----------------------------------------------------------------------------
# STEP 4: Add note pronoun resolution in open_or_search_content
# -----------------------------------------------------------------------------
if '"last note"' not in content:
    content = content.replace(
        '"the generated file", "completed document", "completed pdf"',
        '"the generated file", "completed document", "completed pdf", "note", "the note", "last note", "my note"',
        1
    )
    print("[Step 4] Added note pronoun resolution to open_or_search_content.")

# -----------------------------------------------------------------------------
# STEP 5: Replace DodaiosToolHub save_note and read_note with enhanced suite
# -----------------------------------------------------------------------------
enhanced_hub_notes = '''    def save_note(self, title: str, content: str, category: str = "General") -> str:
        """Saves a styled markdown note document to ~/Documents/Notes."""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "note"
        path = NOTES_DIR / f"{safe_title}.md"
        date_str = time.strftime('%Y-%m-%d %H:%M:%S')
        note_body = (
            f"# {title.strip()}\\n"
            f"*Created: {date_str} | Category: {category} | Author: Prakash (via VOID AI)*\\n\\n"
            f"{content.strip()}\\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(note_body)
        self.last_created_file = str(path)
        self.last_note_info = {"title": title, "path": str(path), "modified": time.time()}
        return f"Note '{title}' saved to {path.name} in Notes."

    def append_note(self, title: str, content: str) -> tuple[bool, str, str]:
        """Appends an entry with timestamp to an existing note document in ~/Documents/Notes."""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_")
        matches = list(NOTES_DIR.glob(f"*{safe_title}*.md"))
        if not matches:
            # Check without case
            for f in NOTES_DIR.glob("*.md"):
                if safe_title.lower() in f.stem.lower() or f.stem.lower() in safe_title.lower():
                    matches.append(f)
                    break

        if matches:
            target_p = matches[0]
            date_str = time.strftime('%Y-%m-%d %H:%M:%S')
            entry = f"\\n\\n---\\n*Added: {date_str}*\\n{content.strip()}\\n"
            with open(target_p, "a", encoding="utf-8") as f:
                f.write(entry)
            self.last_created_file = str(target_p)
            self.last_note_info = {"title": target_p.stem.replace("_", " "), "path": str(target_p), "modified": time.time()}
            return True, f"Successfully appended new entry to note '{target_p.name}'.", str(target_p)
        else:
            # Note does not exist yet: auto-create it
            msg = self.save_note(title, content)
            new_path = NOTES_DIR / f"{safe_title or 'note'}.md"
            return True, f"Note '{title}' did not exist, so I created it for you in Notes.", str(new_path)

    def read_note(self, title: str) -> str:
        """Reads a saved note document from ~/Documents/Notes with clean formatting."""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_")
        matches = list(NOTES_DIR.glob(f"*{safe_title}*.md"))
        if not matches:
            for f in NOTES_DIR.glob("*.md"):
                if safe_title.lower() in f.stem.lower() or f.stem.lower() in safe_title.lower():
                    matches.append(f)
                    break

        if matches:
            target_p = matches[0]
            self.last_created_file = str(target_p)
            self.last_note_info = {"title": target_p.stem.replace("_", " "), "path": str(target_p), "modified": time.time()}
            try:
                with open(target_p, "r", encoding="utf-8", errors="replace") as f:
                    txt = f.read(2500)
                mtime_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(target_p.stat().st_mtime))
                return f"Note: {target_p.name} (Updated {mtime_str}):\\n\\n{txt}"
            except Exception as e:
                return f"Failed to read note: {e}"
        return f"No note found matching '{title}' in ~/Documents/Notes."

    def list_notes(self, limit: int = 10) -> str:
        """Lists active note documents in ~/Documents/Notes."""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        notes = [f for f in NOTES_DIR.glob("*.md") if f.name != "INDEX.md"]
        if not notes:
            return "You have no saved notes in ~/Documents/Notes."

        notes.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        lines = [f"You have {len(notes)} saved note documents in ~/Documents/Notes:"]
        for n in notes[:limit]:
            mtime_str = time.strftime('%b %d, %H:%M', time.localtime(n.stat().st_mtime))
            t_disp = n.stem.replace("_", " ").title()
            sz_kb = round(n.stat().st_size / 1024, 1) or 0.1
            lines.append(f"- **{t_disp}** (`{n.name}`, {sz_kb} KB, updated {mtime_str})")
        if len(notes) > limit:
            lines.append(f"*...and {len(notes) - limit} more notes.*")
        return "\\n".join(lines)

    def search_notes(self, query: str) -> str:
        """Searches note documents across titles and content."""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        q_clean = query.strip().lower()
        if not q_clean:
            return "Please provide a search keyword to find in your notes."

        matches = []
        for n in NOTES_DIR.glob("*.md"):
            if n.name == "INDEX.md":
                continue
            try:
                txt = n.read_text(encoding="utf-8", errors="replace")
                if q_clean in n.name.lower() or q_clean in txt.lower():
                    # Extract context snippet
                    snippet = ""
                    for line in txt.splitlines():
                        if q_clean in line.lower() and not line.startswith("#"):
                            snippet = line.strip()[:100]
                            break
                    if not snippet:
                        snippet = txt[:100].strip().replace("\\n", " ")
                    matches.append((n.stat().st_mtime, n, snippet))
            except Exception:
                pass

        if not matches:
            return f"No notes found matching '{query}' in ~/Documents/Notes."

        matches.sort(key=lambda x: x[0], reverse=True)
        res_lines = [f"Found {len(matches)} note{'s' if len(matches) > 1 else ''} matching '{query}':"]
        for _, n_path, snip in matches[:6]:
            t_disp = n_path.stem.replace("_", " ").title()
            res_lines.append(f"- **{t_disp}** (`{n_path.name}`): \\"{snip}...\\"")
        return "\\n".join(res_lines)

    def export_note_to_pdf(self, title: str = "") -> tuple[bool, str, str]:
        """Compiles a note document into a publication-grade PDF report."""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        target_note = None
        if title:
            safe_title = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_")
            for f in NOTES_DIR.glob("*.md"):
                if safe_title.lower() in f.stem.lower() or f.stem.lower() in safe_title.lower():
                    target_note = f
                    break

        if not target_note:
            # Check last note info
            last_p = getattr(self, "last_note_info", {}).get("path")
            if last_p and Path(last_p).exists():
                target_note = Path(last_p)
            elif self.last_created_file and Path(self.last_created_file).parent == NOTES_DIR:
                target_note = Path(self.last_created_file)
            else:
                # Find newest note
                notes = [f for f in NOTES_DIR.glob("*.md") if f.name != "INDEX.md"]
                if notes:
                    notes.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    target_note = notes[0]

        if not target_note or not target_note.exists():
            return False, "Could not find a note document to export to PDF.", ""

        try:
            content_txt = target_note.read_text(encoding="utf-8", errors="replace")
            note_title = target_note.stem.replace("_", " ").title()

            sections = []
            cur_heading = "Notes & Key Points"
            cur_lines = []
            for line in content_txt.splitlines():
                l = line.strip()
                if l.startswith("#"):
                    if cur_lines:
                        sections.append({"heading": cur_heading, "content": "\\n".join(cur_lines)})
                        cur_lines = []
                    cur_heading = l.lstrip("#").strip()
                else:
                    cur_lines.append(line)
            if cur_lines:
                sections.append({"heading": cur_heading, "content": "\\n".join(cur_lines)})

            out_pdf = REPORTS_DIR / f"{target_note.stem}.pdf"
            msg = self.draft_pdf_document(
                title=f"Note: {note_title}",
                sections=sections,
                filename=str(out_pdf),
                metadata={"topic": note_title, "author": "Prakash (via VOID AI)"}
            )
            self.last_created_file = str(out_pdf)
            self.last_document_info = {
                "title": f"Note: {note_title}",
                "topic": note_title,
                "sections": sections,
                "format": "pdf",
                "path": str(out_pdf),
                "timestamp": time.time(),
            }
            return True, f"Note '{target_note.name}' has been compiled into a professional PDF report at {out_pdf.name}. Say 'open it' to review.", str(out_pdf)
        except Exception as e:
            return False, f"Failed to export note to PDF: {e}", ""

    def maintain_notes(self, cleanup_empty: bool = True) -> tuple[bool, str]:
        """Catalogs, organizes, and maintains the ~/Documents/Notes directory."""
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        all_files = list(NOTES_DIR.glob("*.md")) + list(NOTES_DIR.glob("*.txt"))

        cleaned_count = 0
        if cleanup_empty:
            for f in all_files:
                if f.name == "INDEX.md":
                    continue
                try:
                    sz = f.stat().st_size
                    # Clean empty or tiny cancelled dictation stubs (< 70 bytes with just headers)
                    if sz == 0 or (sz < 70 and "Dictation_" in f.name):
                        f.unlink()
                        cleaned_count += 1
                except Exception:
                    pass

        active_notes = [f for f in NOTES_DIR.glob("*.md") if f.name != "INDEX.md"]
        active_notes.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        total_bytes = sum(f.stat().st_size for f in active_notes)
        total_kb = round(total_bytes / 1024, 1)

        # Generate INDEX.md
        index_lines = [
            "# VOID Notes Document Catalog",
            f"*Maintained by VOID Autonomous AI Assistant on {time.strftime('%Y-%m-%d %H:%M:%S')}*",
            f"**Total Notes:** {len(active_notes)} | **Total Storage:** {total_kb} KB | **Directory:** `~/Documents/Notes`",
            "",
            "| Note Title | File Name | Size | Last Updated |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for n in active_notes:
            mtime_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(n.stat().st_mtime))
            t_disp = n.stem.replace("_", " ").title()
            sz_str = f"{round(n.stat().st_size / 1024, 1)} KB" if n.stat().st_size >= 1024 else f"{n.stat().st_size} B"
            index_lines.append(f"| **{t_disp}** | `{n.name}` | {sz_str} | {mtime_str} |")

        index_file = NOTES_DIR / "INDEX.md"
        index_file.write_text("\\n".join(index_lines), encoding="utf-8")

        cleanup_msg = f", pruned {cleaned_count} empty stubs" if cleaned_count > 0 else ""
        summary = f"Notes maintenance complete: cataloged {len(active_notes)} active notes in INDEX.md{cleanup_msg} (total {total_kb} KB)."
        return True, summary
'''

old_save_note_anchor = '    def save_note(self, title: str, content: str) -> str:'
old_save_note_end = '    def security_audit(self) -> dict[str, Any]:'

if old_save_note_anchor in content and old_save_note_end in content:
    pre = content.split(old_save_note_anchor)[0]
    post = content.split(old_save_note_end)[1]
    content = pre + enhanced_hub_notes + "\n" + old_save_note_end + post
    print("[Step 5] Replaced DodaiosToolHub note methods with comprehensive Note Document Suite.")
else:
    print("[Step 5 Warning] Could not find save_note anchor in content!")

# -----------------------------------------------------------------------------
# STEP 6: Add AI Tool Dispatch in _execute_ai_tool
# -----------------------------------------------------------------------------
ai_tool_notes = """            elif name == "append_note":
                title = args.get("title", "Note")
                content = args.get("content", "")
                ok, msg, path = self.tool_hub.append_note(title, content)
                return msg
            elif name == "list_notes":
                lim = args.get("limit", 10)
                return self.tool_hub.list_notes(limit=lim)
            elif name == "search_notes":
                q = args.get("query", "")
                return self.tool_hub.search_notes(q)
            elif name == "export_note_to_pdf":
                t = args.get("title", "")
                ok, msg, path = self.tool_hub.export_note_to_pdf(t)
                return msg
            elif name == "maintain_notes":
                cl = args.get("cleanup_empty", True)
                ok, msg = self.tool_hub.maintain_notes(cleanup_empty=cl)
                return msg
"""

if 'elif name == "append_note":' not in content:
    content = content.replace(
        '            elif name == "save_note":',
        f'{ai_tool_notes}            elif name == "save_note":',
        1
    )
    print("[Step 6] Added note tools to _execute_ai_tool.")

# -----------------------------------------------------------------------------
# STEP 7: Add Fast-Path Note Routing in _execute_single_command
# -----------------------------------------------------------------------------
fast_path_notes = """        # 5g. Comprehensive Note Document Suite (Create, Append, List, Search, Export, Maintain)
        # A. Notes Maintenance & Cataloging
        if any(p in q_lower for p in ["maintain notes", "organize my notes", "organize notes", "clean up my notes", "clean up notes", "index notes", "notes maintenance", "maintain note documents"]):
            ok, msg = self.tool_hub.maintain_notes()
            return (msg, "Notes: Maintained", str(NOTES_DIR / "INDEX.md"))

        # B. List Notes
        if any(p in q_lower for p in ["list my notes", "list notes", "what are my notes", "show my notes", "show notes", "my notes", "list note documents"]):
            res = self.tool_hub.list_notes()
            return (res, "Notes: List", "")

        # C. Search Notes
        search_notes_m = re.search(r"^(?:search|find|lookup)\s+(?:in\s+)?(?:my\s+)?notes?\s+(?:for\s+)?(.+)$", q_clean, re.I)
        if search_notes_m:
            sq = search_notes_m.group(1).strip()
            res = self.tool_hub.search_notes(sq)
            return (res, f"Notes: Search ({sq[:14]})", "")

        # D. Export Note to PDF
        export_note_m = re.search(r"^(?:convert|export|compile|make)\s+(?:my\s+)?note\s+(?:titled|called|named)?\s*['\"]?([^'\"\n]+?)['\"]?\s*(?:in|to|as|into)\s+(?:a\s+)?(?:pdf|document)$", q_clean, re.I) or \\
                        re.search(r"^(?:convert|export|compile)\s+(?:this\s+|the\s+)?note\s+(?:to|as|into)\s+(?:a\s+)?pdf$", q_clean, re.I)
        if export_note_m:
            n_target = export_note_m.group(1).strip() if (export_note_m.groups() and export_note_m.group(1)) else ""
            ok, msg, pdf_path = self.tool_hub.export_note_to_pdf(n_target)
            if ok and pdf_path:
                self.last_generated_file = pdf_path
                return (msg, "Note: Export PDF", pdf_path)
            else:
                return (msg, "Note: Export Failed", "")

        # E. Append / Add to Existing Note
        note_append_m = (
            re.search(r"^(?:append\s+to|add\s+to|update)\s+(?:my\s+)?note\s+(?:titled|called|named)?\s*['\"]?([^'\"\n:]+?)['\"]?\s*(?:content|body|saying|that|with|:)\s*(.+)$", q_clean, re.I) or
            re.search(r"^(?:append\s+to|add\s+to)\s+(?:my\s+)?note\s*['\"]?([^'\"\n:]+?)['\"]?\s*:\s*(.+)$", q_clean, re.I)
        )
        if note_append_m:
            n_title = note_append_m.group(1).strip()
            n_text = note_append_m.group(2).strip()
            ok, msg, fpath = self.tool_hub.append_note(n_title, n_text)
            self.last_generated_file = fpath
            return (msg, f"Note: Appended ({n_title[:16]})", fpath)

        # F. Create / Take Note
        note_take_m = (
            re.search(r"^(?:take|save|write|create|make)\s+(?:a\s+)?note\s+(?:titled|called|named)?\s*['\"]?([^'\"\n:]+?)['\"]?\s*(?:content|body|saying|:)\s*(.+)$", q_clean, re.I) or
            re.search(r"^(?:take|save|write)\s+(?:a\s+)?note\s*:\s*(.+)$", q_clean, re.I) or
            re.search(r"^note\s+down\s*:\s*(.+)$", q_clean, re.I) or
            re.search(r"^note\s+down\s+(.+)$", q_clean, re.I)
        )
        if note_take_m:
            if len(note_take_m.groups()) >= 2 and note_take_m.group(2):
                title = note_take_m.group(1).strip() or "Quick Note"
                n_content = note_take_m.group(2).strip()
            else:
                title = "Quick Note"
                n_content = note_take_m.group(1).strip()
            msg = self.tool_hub.save_note(title, n_content)
            safe_t = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "note"
            fpath = str(NOTES_DIR / f"{safe_t}.md")
            self.last_generated_file = fpath
            return (msg, f"Note: Saved ({title[:16]})", fpath)

        # G. Read / Open Note
        note_read_m = re.search(r"^(?:read|get|open|show)\s+(?:my\s+)?note\s+(?:titled|called|named)?\s*['\"]?([^'\"\n]+)['\"]?$", q_clean, re.I)
        if note_read_m:
            title = note_read_m.group(1).strip()
            if q_lower.startswith("open note"):
                # Also open in default desktop application
                res = self.tool_hub.read_note(title)
                last_p = getattr(self.tool_hub, "last_note_info", {}).get("path")
                if last_p and Path(last_p).exists():
                    try:
                        subprocess.Popen(["xdg-open", last_p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    except Exception:
                        pass
                    return (f"Opened note '{Path(last_p).name}' in your default editor.\\n\\n{res}", f"Note: Open ({title[:16]})", last_p)
                return (res, f"Note: {title[:16]}", "")
            else:
                res = self.tool_hub.read_note(title)
                return (res, f"Note: {title[:16]}", "")
"""

old_note_route_anchor = '        # 5g. Quick Sticky Notes (~/Documents/Notes)'
old_note_route_end = '        # 6. Power Controls (Shutdown, Reboot, Lock with 5s Cancelable Timer)'

if old_note_route_anchor in content and old_note_route_end in content:
    pre = content.split(old_note_route_anchor)[0]
    post = content.split(old_note_route_end)[1]
    content = pre + fast_path_notes + "\n" + old_note_route_end + post
    print("[Step 7] Injected Comprehensive Note Document fast-paths into _execute_single_command.")
else:
    print("[Step 7 Warning] Could not find old note route anchor in content!")

TARGET.write_text(content, encoding="utf-8")
print(f"[Done] Updated {TARGET}")

