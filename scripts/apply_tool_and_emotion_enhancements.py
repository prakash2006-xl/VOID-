import sys
import re
import py_compile

WIDGET_PATH = "/run/media/prakash/TR_39/VOID/bin/void-widget.py"

with open(WIDGET_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# ---------------------------------------------------------------------------
# 1. Update normalize_voice_intent with extra typos
# ---------------------------------------------------------------------------
old_typo = '(r"\\b(?:attendongh|attendng|attendin)\\b", "attending"),'
new_typo = '''(r"\\b(?:attendongh|attendng|attendin)\\b", "attending"),
        (r"\\b(?:volum|volme|vlume)\\b", "volume"),
        (r"\\b(?:brightnes|brigthness)\\b", "brightness"),
        (r"\\b(?:clippboard|clipbord|clipbaord)\\b", "clipboard"),
        (r"\\b(?:wether|weaher)\\b", "weather"),
        (r"\\b(?:batry|batery|battry)\\b", "battery"),
        (r"\\b(?:temprature|tempratures|temperatue)\\b", "temperature"),'''

assert old_typo in content, "old_typo not found in content"
content = content.replace(old_typo, new_typo, 1)

# ---------------------------------------------------------------------------
# 2. Remove duplicate methods in AudioVoiceEngine (lines 2293-2337)
# ---------------------------------------------------------------------------
dup_marker = 'return "Unknown tool."'
dup_pattern = r'(\s+return "Unknown tool\."\s+)(def _finish_utterance_and_process\(self\) -> None:.*?)(def _process_task\(self, query: str\) -> None:)'

match_dup = re.search(dup_pattern, content, re.DOTALL)
if match_dup:
    content = content[:match_dup.start(2)] + content[match_dup.start(3):]
    print("[Apply] Successfully removed duplicated methods in AudioVoiceEngine.")
else:
    print("[Apply Note] No duplicate methods detected in AudioVoiceEngine.")

# ---------------------------------------------------------------------------
# 3. Add Section 0e: Emotional Companion & Empathy Routing (after Section 0d)
# ---------------------------------------------------------------------------
sec_0d_end = 'return ("Ollama stopped. Model unloaded and memory freed.", "Ollama: Standby", "")\n            except Exception as e:\n                return (f"Error stopping Ollama: {e}", "Ollama: Error", "")'

sec_0e_code = '''return ("Ollama stopped. Model unloaded and memory freed.", "Ollama: Standby", "")
            except Exception as e:
                return (f"Error stopping Ollama: {e}", "Ollama: Error", "")

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
            return ("Good afternoon, Prakash! Powering through the day smoothly. Let me know what you need next.", "Companion • Afternoon 🌤️", "")'''

assert sec_0d_end in content, "sec_0d_end not found"
content = content.replace(sec_0d_end, sec_0e_code, 1)

# ---------------------------------------------------------------------------
# 4. Replace Section 5 with full Offline Tools (Volume, Media, Brightness, Clipboard, Weather, Vitals, Notes)
# ---------------------------------------------------------------------------
sec_5_old = '''        # 5. Audio Hardware Inspection & Volume
        if any(p in q_lower for p in ["audio devices", "list audio", "show microphones", "show speakers"]):
            devs = self.tool_hub.get_audio_devices()
            if devs:
                inputs = [d["name"] for d in devs.get("inputs", []) if not d["name"].startswith("PipeWire ALSA")]
                outputs = [d["name"] for d in devs.get("outputs", []) if not d["name"].startswith("PipeWire ALSA")]
                reply = f"Inputs:\\n- " + "\\n- ".join(inputs[:3]) + "\\n\\nOutputs:\\n- " + "\\n- ".join(outputs[:3])
                return (reply, "Audio Hardware", "")
            else:
                return ("PipeWire and WirePlumber audio devices are active.", "Audio: Active", "")

        if any(p in q_lower for p in ["volume up", "increase volume", "louder"]):
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "10%+"], stdout=subprocess.DEVNULL)
            return ("Volume increased.", "Audio: Volume Up", "")

        if any(p in q_lower for p in ["volume down", "decrease volume", "quieter"]):
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "10%-"], stdout=subprocess.DEVNULL)
            return ("Volume decreased.", "Audio: Volume Down", "")

        if any(p in q_lower for p in ["mute", "unmute", "toggle mute"]):
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], stdout=subprocess.DEVNULL)
            return ("Audio mute toggled.", "Audio: Mute Toggled", "")'''

sec_5_new = '''        # 5. Audio Hardware Inspection & Volume Control
        if any(p in q_lower for p in ["audio devices", "list audio", "show microphones", "show speakers"]):
            devs = self.tool_hub.get_audio_devices()
            if devs:
                inputs = [d["name"] for d in devs.get("inputs", []) if not d["name"].startswith("PipeWire ALSA")]
                outputs = [d["name"] for d in devs.get("outputs", []) if not d["name"].startswith("PipeWire ALSA")]
                reply = f"Inputs:\\n- " + "\\n- ".join(inputs[:3]) + "\\n\\nOutputs:\\n- " + "\\n- ".join(outputs[:3])
                return (reply, "Audio Hardware", "")
            else:
                return ("PipeWire and WirePlumber audio devices are active.", "Audio: Active", "")

        vol_set_m = re.search(r"\\b(?:set|change|put)\\s+(?:the\\s+)?volume\\s+(?:to\\s+)?(\\d+)\\b", q_lower) or re.search(r"\\bvolume\\s+(?:to\\s+)?(\\d+)%?\\b", q_lower)
        if vol_set_m:
            target_vol = int(vol_set_m.group(1))
            msg = self.tool_hub.set_volume(target_vol)
            return (msg, f"Audio: Volume {target_vol}%", "")

        if any(p in q_lower for p in ["volume up", "increase volume", "raise volume", "louder", "turn it up"]):
            msg = self.tool_hub.adjust_volume(10)
            return (msg, "Audio: Volume Up", "")

        if any(p in q_lower for p in ["volume down", "decrease volume", "lower volume", "quieter", "turn it down"]):
            msg = self.tool_hub.adjust_volume(-10)
            return (msg, "Audio: Volume Down", "")

        if any(p in q_lower for p in ["mute audio", "unmute audio", "toggle mute", "mute sound", "unmute sound", "mute", "unmute"]):
            msg = self.tool_hub.toggle_mute()
            return (msg, "Audio: Mute Toggled", "")

        if any(p in q_lower for p in ["what is the volume", "check volume", "current volume", "get volume", "show volume"]):
            v = self.tool_hub.get_volume()
            st = "muted" if v.get("muted") else f"{v.get('volume_pct')}%"
            return (f"Master audio volume is currently {st}.", "Audio: Status", "")

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
        bright_set_m = re.search(r"\\b(?:set|change|put)\\s+(?:the\\s+)?brightness\\s+(?:to\\s+)?(\\d+)\\b", q_lower) or re.search(r"\\bbrightness\\s+(?:to\\s+)?(\\d+)%?\\b", q_lower)
        if bright_set_m:
            target_b = int(bright_set_m.group(1))
            msg = self.tool_hub.set_brightness(target_b)
            return (msg, f"Screen: Brightness {target_b}%", "")

        if any(p in q_lower for p in ["brightness up", "increase brightness", "brighter", "screen brighter", "raise brightness"]):
            cur = self.tool_hub.get_brightness()
            new_b = min(100, cur + 15)
            msg = self.tool_hub.set_brightness(new_b)
            return (msg, f"Screen: Brightness {new_b}%", "")

        if any(p in q_lower for p in ["brightness down", "decrease brightness", "dimmer", "screen dimmer", "lower brightness", "dim screen"]):
            cur = self.tool_hub.get_brightness()
            new_b = max(10, cur - 15)
            msg = self.tool_hub.set_brightness(new_b)
            return (msg, f"Screen: Brightness {new_b}%", "")

        if any(p in q_lower for p in ["what is the brightness", "check brightness", "current brightness", "get brightness", "screen brightness"]):
            cur = self.tool_hub.get_brightness()
            return (f"Screen brightness is currently at {cur}%.", "Screen: Brightness", "")

        # 5d. Wayland Clipboard Management (wl-copy / wl-paste)
        copy_m = re.search(r"^(?:please\\s+)?copy\\s+(.+?)\\s+to\\s+(?:the\\s+)?clipboard$", q_clean, re.I)
        if copy_m:
            txt_to_copy = copy_m.group(1).strip().strip("'\\\"")
            msg = self.tool_hub.set_clipboard(txt_to_copy)
            return (msg, "Clipboard: Copied", "")

        if any(p in q_lower for p in ["read clipboard", "what is on my clipboard", "what is on clipboard", "check clipboard", "show clipboard", "paste clipboard", "clipboard content"]):
            clip = self.tool_hub.get_clipboard()
            return (f"Clipboard content:\\n{clip}", "Clipboard: Content", "")

        # 5e. Live Weather Lookup (wttr.in)
        weather_m = (
            re.search(r"\\bweather\\s+(?:in|for|at)\\s+([a-zA-Z\\s]+)", q_lower) or
            re.search(r"\\bhow\\s+is\\s+the\\s+weather\\s+(?:in|for|at)\\s+([a-zA-Z\\s]+)", q_lower)
        )
        if weather_m:
            loc = weather_m.group(1).strip()
            w_res = self.tool_hub.get_weather(loc)
            return (f"Live weather for {loc.title()}: {w_res}", f"Weather: {loc.title()}", "")

        if any(p in q_lower for p in ["what is the weather", "current weather", "how is the weather", "check weather", "weather today"]):
            w_res = self.tool_hub.get_weather()
            return (f"Current weather: {w_res}", "Weather: Local", "")

        # 5f. Hardware & Battery Vitals (upower + sensors)
        if any(p in q_lower for p in ["hardware vitals", "battery status", "check battery", "how much battery", "cpu temp", "cpu temperature", "temperatures", "hardware health", "battery level"]):
            v = self.tool_hub.get_hardware_vitals()
            msg = f"Battery: {v.get('battery_pct')}% ({v.get('battery_state')}). Temperatures: CPU {v.get('cpu_temp_c')}°C"
            if v.get('gpu_temp_c') is not None:
                msg += f", GPU {v.get('gpu_temp_c')}°C"
            if v.get('nvme_temp_c') is not None:
                msg += f", NVMe {v.get('nvme_temp_c')}°C"
            msg += "."
            return (msg, "Hardware Vitals", "")

        # 5g. Quick Sticky Notes (~/Documents/Notes)
        note_take_m = (
            re.search(r"^(?:take|save|write|create|make)\\s+(?:a\\s+)?note\\s+(?:titled|called|named)?\\s*['\\\"]?([^'\\\"\\n:]+?)['\\\"]?\\s*(?:content|body|saying|:)\\s*(.+)$", q_clean, re.I) or
            re.search(r"^(?:take|save|write)\\s+(?:a\\s+)?note\\s*:\\s*(.+)$", q_clean, re.I)
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

        note_read_m = re.search(r"^(?:read|get|open|show)\\s+(?:my\\s+)?note\\s+(?:titled|called|named)?\\s*['\\\"]?([^'\\\"\\n]+)['\\\"]?$", q_clean, re.I)
        if note_read_m:
            title = note_read_m.group(1).strip()
            res = self.tool_hub.read_note(title)
            return (res, f"Note: {title}", "")'''

assert sec_5_old in content, "sec_5_old not found in content"
content = content.replace(sec_5_old, sec_5_new, 1)

# ---------------------------------------------------------------------------
# 5. Update Ollama System Message (Rule 1 & Rule 6: Empathetic & Companionable SOUL)
# ---------------------------------------------------------------------------
old_rules = '''                        "1. NEVER introduce yourself unless the user explicitly asks 'who are you'. NEVER begin responses with 'I am VOID' or 'As an AI assistant'.\\n"
                        "2. AUTONOMOUS TASK PLANNING & EXECUTION: You possess full capability to plan and execute multi-step complex tasks. When the user gives a complex goal, formulate a clear sequential plan, decompose it into sub-goals, and invoke necessary tools (e.g. web search, file management, email drafting, safe commands, task reminders) step by step until the goal is fully achieved.\\n"
                        "3. BROWSER & EMAIL EXECUTION: When asked to open mail, compose an email, or send an email in the browser, invoke 'browser_compose_email' with the recipient, subject, and body so that Chromium opens with Gmail compose loaded on screen. If the recipient email is missing from the request, invoke 'ask_user_clarification' or ask the user directly for the recipient's email address. When asked to open a new tab, search, or visit a website on screen, call 'browser_open' or 'browser_search'. Maintain local project files using 'create_document', 'append_document', 'read_document', and 'list_files'. NEVER simply save an email draft to disk when the user asked to send or compose it in the browser!\\n"
                        "4. TRUTHFUL BOUNDARIES: If a user asks for something outside system boundaries or impossible with available tools (e.g. modifying root system files, accessing unauthorized remote accounts), state clearly: 'I am unable to complete this task because [exact reason]'. NEVER claim an action was done if no tool was executed.\\n"
                        "5. Provide a direct, concise final response (1-2 sentences maximum) summarizing the completed plan and actions."'''

new_rules = '''                        "1. NEVER introduce yourself unless the user explicitly asks 'who are you'. NEVER begin responses with 'I am VOID' or 'As an AI assistant'. Address Prakash with natural warmth, respect, and camaraderie.\\n"
                        "2. AUTONOMOUS TASK PLANNING & EXECUTION: You possess full capability to plan and execute multi-step complex tasks. When the user gives a complex goal, formulate a clear sequential plan, decompose it into sub-goals, and invoke necessary tools step by step until the goal is fully achieved.\\n"
                        "3. BROWSER & EMAIL EXECUTION: When asked to open mail, compose an email, or send an email in the browser, invoke 'browser_compose_email' with the recipient, subject, and body so that Chromium opens with Gmail compose loaded on screen. If the recipient email is missing from the request, invoke 'ask_user_clarification' or ask the user directly for the recipient's email address. When asked to open a new tab, search, or visit a website on screen, call 'browser_open' or 'browser_search'. Maintain local project files using 'create_document', 'append_document', 'read_document', and 'list_files'. NEVER simply save an email draft to disk when the user asked to send or compose it in the browser!\\n"
                        "4. TRUTHFUL BOUNDARIES: If a user asks for something outside system boundaries or impossible with available tools (e.g. modifying root system files, accessing unauthorized remote accounts), state clearly: 'I am unable to complete this task because [exact reason]'. NEVER claim an action was done if no tool was executed.\\n"
                        "5. Provide a direct, concise final response (1-2 sentences maximum) summarizing the completed plan and actions.\\n"
                        "6. EMPATHETIC & COMPANIONABLE SOUL: You are an empathetic, witty, and caring companion. If Prakash expresses fatigue, distress, or stress, respond with genuine warmth and comfort. If Prakash celebrates a win or good news, celebrate enthusiastically with him! Never speak like a dry, robotic utility."'''

assert old_rules in content, "old_rules not found in content"
content = content.replace(old_rules, new_rules, 1)

# ---------------------------------------------------------------------------
# 6. UI Layout & Anti-Clipping Enhancements in VoidMiniWidget
# ---------------------------------------------------------------------------
old_dim = '''    COLLAPSED_W = 356
    COLLAPSED_H = 56
    EXPANDED_W = 370
    EXPANDED_H = 265'''

new_dim = '''    COLLAPSED_W = 385
    COLLAPSED_H = 56
    EXPANDED_W = 385
    EXPANDED_H = 265'''

assert old_dim in content, "old_dim not found in content"
content = content.replace(old_dim, new_dim, 1)

old_ui_title = '''        title_box = QVBoxLayout()
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
        """)'''

new_ui_title = '''        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setContentsMargins(0, 0, 0, 0)
        title = QLabel("VOID", self._card)
        title.setFixedHeight(18)
        title.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1.2px;
                padding: 0px;
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
        self._status_pill.setFixedHeight(16)
        self._status_pill.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 10px;
                font-weight: 500;
                padding: 0px;
                margin: 0px;
            }
        """)'''

assert old_ui_title in content, "old_ui_title not found in content"
content = content.replace(old_ui_title, new_ui_title, 1)

# Write modified file
with open(WIDGET_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("[Apply] Successfully wrote all enhancements to void-widget.py.")

# Verify syntax with py_compile
py_compile.compile(WIDGET_PATH, doraise=True)
print("[Apply] Python syntax verification PASSED cleanly.")
