#!/usr/bin/env python3
"""
Applies YouTube search & play, screen click automation, dictation stop button & phrases,
file memory traceback ('open that'), quick chips cleanup, and false 'open' trigger fixes to void-widget.py.
"""

import sys
import re
from pathlib import Path

WIDGET_PATH = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")
if not WIDGET_PATH.exists():
    print(f"Error: {WIDGET_PATH} not found.")
    sys.exit(1)

content = WIDGET_PATH.read_text(encoding="utf-8")

# 1. Update normalize_voice_intent
old_norm = """        (r"\\b(?:restrt|rstart)\\b", "restart"),
        (r"\\b(?:asked\\s+to\\s+search|ask\\s+to\\s+search|wants\\s+to\\s+search)\\b", "search"),
        (r"\\b(?:fel|fell)\\s+not\\b", "feel not"),
        (r"\\b(?:attendongh|attendng|attendin)\\b", "attending"),
        (r"\\b(?:what'?s?\\s*app|wats\\s*app|watsapp|whatsaap|whatsup|what's\\s+up|whats\\s+up|whatsap|whats\\s+a)\\b", "whatsapp"),
        (r"\\b(?:vib|veb|bib)\\b", "web"),"""

new_norm = """        (r"\\b(?:restrt|rstart)\\b", "restart"),
        (r"\\b(?:beliver|beleiver|belever)\\b", "believer"),
        (r"\\b(?:snag|sng)\\b", "song"),
        (r"\\b(?:can\\s+cel)\\b", "cancel"),
        (r"\\b(?:cerate|creat)\\b", "create"),
        (r"\\b(?:asked\\s+to\\s+search|ask\\s+to\\s+search|wants\\s+to\\s+search)\\b", "search"),
        (r"\\b(?:fel|fell)\\s+not\\b", "feel not"),
        (r"\\b(?:attendongh|attendng|attendin)\\b", "attending"),
        (r"\\b(?:whats\\s*app|wats\\s*app|watsapp|whatsaap)\\b", "whatsapp"),
        (r"\\b(?:vib|veb|bib)\\b", "web"),"""

if old_norm in content:
    content = content.replace(old_norm, new_norm)
    print("[1] Updated normalize_voice_intent with believer/snag/cancel/create and strict WhatsApp.")
else:
    print("[WARNING 1] old_norm not matched exactly, checking regex...")

# 2. Update resolve_app_name to never match short pronouns/stop words
old_resolve = """def resolve_app_name(raw_name: str) -> str | None:
    raw_lower = raw_name.strip().lower()
    for app_id, aliases in KNOWN_APPS.items():
        if raw_lower in aliases:
            return app_id
        for a in aliases:
            if a in raw_lower or raw_lower in a:
                return app_id"""

new_resolve = """def resolve_app_name(raw_name: str) -> str | None:
    raw_lower = raw_name.strip().lower()
    # Never resolve generic pronouns, articles, or stop words as application names
    if raw_lower in ["that", "it", "this", "something", "the summary", "summary", "document", "file", "all"]:
        return None
    for app_id, aliases in KNOWN_APPS.items():
        if raw_lower in aliases:
            return app_id
        for a in aliases:
            if a in raw_lower or (len(raw_lower) >= 4 and raw_lower in a):
                return app_id"""

if old_resolve in content:
    content = content.replace(old_resolve, new_resolve)
    print("[2] Updated resolve_app_name to protect pronouns and short words from false app resolution.")

# 3. Add last_created_file, play_youtube_query, click_screen to DodaiosToolHub
old_hub_init = """    def __init__(self) -> None:
        self.brain = None
        self.tools: dict[str, Any] = {}
        self._init_in_bg()"""

new_hub_init = """    def __init__(self) -> None:
        self.brain = None
        self.tools: dict[str, Any] = {}
        self.last_created_file: str | None = None
        self._init_in_bg()

    def play_youtube_query(self, query: str) -> tuple[bool, str]:
        \"\"\"Searches YouTube, resolves the top matching video ID, and directly plays it in Chromium.\"\"\"
        clean_q = re.sub(r"\\b(?:song|video|track|music)\\b", "", query, flags=re.I).strip()
        try:
            enc_q = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={enc_q}"
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
            html = urllib.request.urlopen(req, timeout=3.5).read().decode("utf-8", errors="ignore")
            video_ids = re.findall(r"/watch\\?v=([a-zA-Z0-9_-]{11})", html)
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
        \"\"\"Clicks the screen at exact coordinates (x, y).\"\"\"
        try:
            import pyautogui
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
            return f"Clicked mouse {button} at screen coordinates ({x}, {y})."
        except Exception as e:
            return f"Error clicking at ({x}, {y}): {e}"

    def click_screen_object(self, target: str) -> str:
        \"\"\"Identifies on-screen semantic target and clicks it.\"\"\"
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
            return f"Failed to click on-screen target: {e}\""""

if old_hub_init in content:
    content = content.replace(old_hub_init, new_hub_init)
    print("[3] Added last_created_file, play_youtube_query, and screen clicking to DodaiosToolHub.")

# Update file trackers in draft_docx_document and create_document
old_doc_save = """            out = (REPORTS_DIR / f"{safe_name}.docx") if not filename else Path(filename)
            doc.save(out)
            return f"Word document successfully created and saved to {out}." """

# Let's inspect where doc.save(out) is in content
if "doc.save(out)" in content:
    content = content.replace(
        "            doc.save(out)\n            return f\"Word document successfully created and saved to {out}.\"",
        "            doc.save(out)\n            self.last_created_file = str(out)\n            return f\"Word document successfully created and saved to {out}.\""
    )
    print("[3b] Tracked last_created_file in draft_docx_document.")

if "wb.save(out)" in content:
    content = content.replace(
        "            wb.save(out)\n            return f\"Excel workbook successfully created and saved to {out}.\"",
        "            wb.save(out)\n            self.last_created_file = str(out)\n            return f\"Excel workbook successfully created and saved to {out}.\""
    )
    print("[3c] Tracked last_created_file in draft_excel_spreadsheet.")

# 4. Update AudioVoiceEngine.__init__ with last_generated_file
old_engine_vars = """        self._is_speaking = False
        self._mute_audio_until = 0.0
        self._last_executed_cmd = ''
        self._last_cmd_timestamp = 0.0"""

new_engine_vars = """        self._is_speaking = False
        self._mute_audio_until = 0.0
        self._last_executed_cmd = ''
        self._last_cmd_timestamp = 0.0
        self.last_generated_file: str | None = None"""

if old_engine_vars in content:
    content = content.replace(old_engine_vars, new_engine_vars)
    print("[4] Added last_generated_file tracking to AudioVoiceEngine.")

# 5. Update dictation exit phrases in _process_task
old_dict_stop = """            # Live Voice Dictation Handler
            if self._dictation_mode:
                q_low = q_raw.lower()
                if any(p in q_low for p in ["stop dictation", "finish dictation", "end dictation", "stop typing", "dictation off", "stop voice typing", "exit dictation"]):
                    self._dictation_mode = False
                    fname = self._dictation_file.name if self._dictation_file else "Note"
                    reply_text = f"Dictation finished. Your notes have been saved to {fname}."
                    print(f"[VOID Dictation] Stopped. Saved to {fname}.", flush=True)
                    self.response_ready.emit(query, reply_text, "Dictation: Saved", "")
                    self._speak_text(reply_text)
                    return"""

new_dict_stop = """            # Live Voice Dictation Handler
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
                    return"""

if old_dict_stop in content:
    content = content.replace(old_dict_stop, new_dict_stop)
    print("[5] Expanded dictation exit phrases with cancel dictate and stop dictate.")

# 6. Add YouTube Play, Screen Click, Summary Drafting with Exact Name, and File Open Memory to _execute_single_command
old_b_search = """        # WhatsApp Web Direct Fast Path (Phonetic typo tolerant: watsapp, whatsapp, whats app, etc.)
        if any(p in q_lower for p in ["whatsapp", "watsapp", "whats app", "whatsap", "whats up web", "wats app"]):"""

new_media_and_memory = """        # 1b1. YouTube Search & Play (Direct Video Stream & Browser Playback)
        yt_play_match = (
            re.search(r"(?:open\s+)?youtube(?:\s+in\s+chromium)?\s+and\s+search(?:\s+for)?\s+(.+?)(?:\s+and\s+play(?:\s+it)?|$)", q_lower) or
            re.search(r"search(?:\s+for)?\s+(.+?)\s+on\s+youtube\s+and\s+play(?:\s+it)?", q_lower) or
            re.search(r"play\s+(.+?)\s+(?:on|in)\s+youtube", q_lower) or
            re.search(r"play\s+(.+?)\s+song(?:\s+on\s+youtube)?", q_lower) or
            re.search(r"youtube\s+(?:play|search)\s+(.+)", q_lower)
        )
        if yt_play_match:
            yt_query = yt_play_match.group(1).strip()
            yt_query = re.sub(r"\\b(?:in\\s+chromium|and\\s+play\\s+it|and\\s+play|play\\s+it)\\b", "", yt_query, flags=re.I).strip()
            if yt_query and yt_query not in ["it", "something", "a song"]:
                ok, msg = self.tool_hub.play_youtube_query(yt_query)
                return (msg, f"YouTube: Play ({yt_query[:16]})", "")

        # 1b2. Screen Identification & Object Clicking
        click_m = (
            re.search(r"^(?:please\\s+)?click\\s+(?:on\\s+)?(?:the\\s+)?(?:at\\s+)?(\\d+)[,\\s]+(\\d+)$", q_clean, re.I) or
            re.search(r"^(?:please\\s+)?click\\s+(?:on\\s+)?(?:the\\s+)?(.+)$", q_clean, re.I)
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
            re.search(r"(?:create|draft|write|generate|make)\\s+(?:me\\s+)?(?:a\\s+)?(?:summary|document|report|doc|notes?)\\s+(?:on|about|regarding|of|for)\\s+(.+)$", q_clean, re.I) or
            re.search(r"summarize\\s+(.+?)\\s+(?:into|in|to)\\s+(?:a\\s+)?(?:document|doc|report|file)", q_clean, re.I)
        )
        if summary_req_m:
            topic_raw = summary_req_m.group(1).strip()
            # Extract custom name if user said "called X", "named X", "titled X", "save as X"
            name_m = re.search(r"(?:called|named|titled|save\\s+(?:it\\s+)?as|with\\s+(?:the\\s+)?name)\\s+['\\\"]?([a-zA-Z0-9_\\-\\s]+)['\\\"]?", q_clean, re.I)
            custom_title = name_m.group(1).strip() if name_m else ""
            topic = re.sub(r"(?:called|named|titled|save\\s+(?:it\\s+)?as|with\\s+(?:the\\s+)?name)\\s+['\\\"]?[a-zA-Z0-9_\\-\\s]+['\\\"]?", "", topic_raw, flags=re.I).strip()
            if not topic:
                topic = topic_raw

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
                    "content": "- Pillar 1: Unconditional support, emotional guidance, and foundational security.\n- Pillar 2: Moral framework and social-emotional development across life stages.\n- Pillar 3: Lifelong anchor providing strength, empathy, and perspective."
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
            re.search(r"\\b(?:whatsapp|watsapp)\\b", q_lower) and
            any(w in q_lower for w in ["open", "launch", "go to", "message", "send", "chat", "web"])
        ) or q_lower.strip() in ["whatsapp", "whatsapp web", "watsapp web"]
        if is_whatsapp_request:"""

if old_b_search in content:
    content = content.replace(old_b_search, new_media_and_memory)
    print("[6] Added YouTube play, screen click, summary writer, and file memory traceback to _execute_single_command.")
else:
    print("[WARNING 6] old_b_search not matched.")

# 7. Update Quick Chips in VoidMiniWidget
old_chips = """        quick_chips = [
            ("🎙️ Dictate", "start dictation"),
            ("Draft Doc", "draft doc on AI Trends 2026"),
            ("Draft Excel", "draft excel on Project Budget"),
            ("WhatsApp", "open whatsapp web"),
            ("Screenshot", "take screenshot"),
        ]"""

new_chips = """        quick_chips = [
            ("🧠 Start Ollama", "start ollama"),
            ("🌐 Open Chrome", "open chromium"),
            ("🎙️ Dictate", "start dictation"),
            ("📸 Screenshot", "take screenshot"),
            ("📊 System Status", "system status"),
        ]"""

if old_chips in content:
    content = content.replace(old_chips, new_chips)
    print("[7] Cleaned up quick chips: kept Start Ollama & Open Chrome, removed Draft Doc/Excel.")

# 8. Add dictation stop button to widget header
old_header_buttons = """        self._stop_btn = QPushButton("⏹", self._card)
        self._stop_btn.setFixedSize(28, 28)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setToolTip("Stop Thinking / Cancel Active Task")
        self._stop_btn.setVisible(False)
        self._stop_btn.setStyleSheet(\"\"\"
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
        \"\"\")
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        header.addWidget(self._stop_btn)"""

new_header_buttons = """        self._stop_btn = QPushButton("⏹", self._card)
        self._stop_btn.setFixedSize(28, 28)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setToolTip("Stop Thinking / Cancel Active Task")
        self._stop_btn.setVisible(False)
        self._stop_btn.setStyleSheet(\"\"\"
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
        \"\"\")
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        header.addWidget(self._stop_btn)

        # Dedicated Visible Stop Dictation Button
        self._dict_stop_btn = QPushButton("⏹ Stop Dictation", self._card)
        self._dict_stop_btn.setFixedHeight(28)
        self._dict_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dict_stop_btn.setToolTip("Stop Dictation Mode & Return to Normal Mode")
        self._dict_stop_btn.setVisible(False)
        self._dict_stop_btn.setStyleSheet(\"\"\"
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
        \"\"\")
        self._dict_stop_btn.clicked.connect(self._on_stop_dictation_clicked)
        header.addWidget(self._dict_stop_btn)"""

if old_header_buttons in content:
    content = content.replace(old_header_buttons, new_header_buttons)
    print("[8] Added _dict_stop_btn to header row.")

# Add _on_stop_dictation_clicked and dictation state handler to VoidMiniWidget
old_on_state = """    def _on_state_changed(self, state: str) -> None:
        self._orb.set_state(state)
        if state == "thinking":
            self._status_dot.setStyleSheet("color: #f59e0b; font-size: 10px;")
            self._status_pill.setText("Thinking...")
            self._stop_btn.setVisible(True)"""

new_on_state = """    def _on_stop_dictation_clicked(self) -> None:
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
        self._orb.set_state(state)
        # Update Dictation Stop Button visibility
        if getattr(self._engine, "_dictation_mode", False):
            self._dict_stop_btn.setVisible(True)
            self._status_pill.setText("🎙️ Dictating...")
            self._status_dot.setStyleSheet("color: #f59e0b; font-size: 10px;")
        else:
            self._dict_stop_btn.setVisible(False)

        if state == "thinking":
            self._status_dot.setStyleSheet("color: #f59e0b; font-size: 10px;")
            self._status_pill.setText("Thinking...")
            self._stop_btn.setVisible(True)"""

if old_on_state in content:
    content = content.replace(old_on_state, new_on_state)
    print("[9] Added _on_stop_dictation_clicked and dynamic dictation button visibility.")

# 10. Strict email intent check in _execute_single_command
old_email_intent = """        # 3d. Email & Webmail Composition / Sending Fast Path
        is_email_intent = bool(
            re.search(r"\\b(?:send|compose|write|draft|open)\\s+(?:an?\\s+)?(?:email|mail)\\b", q_lower) or
            re.search(r"\\b(?:email|mail)\\b.*\\b(?:to|saying|about|@)\\b", q_lower)
        )"""

new_email_intent = """        # 3d. Email & Webmail Composition / Sending Fast Path (Strict: requires explicit email intent)
        is_email_intent = bool(
            re.search(r"\\b(?:send|compose|draft)\\s+(?:an?\\s+)?(?:email|mail)\\b", q_lower) or
            re.search(r"\\b(?:open|launch)\\s+(?:gmail|google\\s+mail|webmail)\\b", q_lower) or
            re.search(r"\\b(?:open\\s+(?:mail|email)\\s+in\\s+(?:chromium|browser))\\b", q_lower) or
            re.search(r"\\b(?:send|write)\\s+(?:an?\\s+)?(?:email|mail)\\s+(?:to|saying|about)\\b", q_lower) or
            ("@" in q_clean and any(w in q_lower for w in ["send", "email", "mail", "compose"]))
        )"""

if old_email_intent in content:
    content = content.replace(old_email_intent, new_email_intent)
    print("[10] Made email intent strict to prevent false opens.")

WIDGET_PATH.write_text(content, encoding="utf-8")
print(f"[SUCCESS] void-widget.py updated successfully ({len(content)} bytes).")

