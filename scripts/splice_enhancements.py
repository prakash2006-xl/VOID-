import py_compile

WIDGET_PATH = "/run/media/prakash/TR_39/VOID/bin/void-widget.py"
with open(WIDGET_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

idx_ollama_end = None
idx_sec5_start = None
idx_sec6_start = None

for i, l in enumerate(lines):
    if 'return (f"Error stopping Ollama: {e}", "Ollama: Error", "")' in l:
        idx_ollama_end = i + 1
    if '# 5. Audio Hardware Inspection & Volume' in l:
        idx_sec5_start = i
    if '# 6. Power Controls (Shutdown, Reboot, Lock with 5s Cancelable Timer)' in l:
        idx_sec6_start = i

print(f"Indices: ollama_end={idx_ollama_end}, sec5={idx_sec5_start}, sec6={idx_sec6_start}")
assert idx_ollama_end is not None, "idx_ollama_end not found"
assert idx_sec5_start is not None, "idx_sec5_start not found"
assert idx_sec6_start is not None, "idx_sec6_start not found"

sec_0e_code = r'''
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
'''

sec_5_code = r'''        # 5. Audio Hardware Inspection & Volume Control
        if any(p in q_lower for p in ["audio devices", "list audio", "show microphones", "show speakers"]):
            devs = self.tool_hub.get_audio_devices()
            if devs:
                inputs = [d["name"] for d in devs.get("inputs", []) if not d["name"].startswith("PipeWire ALSA")]
                outputs = [d["name"] for d in devs.get("outputs", []) if not d["name"].startswith("PipeWire ALSA")]
                reply = f"Inputs:\n- " + "\n- ".join(inputs[:3]) + "\n\nOutputs:\n- " + "\n- ".join(outputs[:3])
                return (reply, "Audio Hardware", "")
            else:
                return ("PipeWire and WirePlumber audio devices are active.", "Audio: Active", "")

        vol_set_m = re.search(r"\b(?:set|change|put)\s+(?:the\s+)?volume\s+(?:to\s+)?(\d+)\b", q_lower) or re.search(r"\bvolume\s+(?:to\s+)?(\d+)%?\b", q_lower)
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
        bright_set_m = re.search(r"\b(?:set|change|put)\s+(?:the\s+)?brightness\s+(?:to\s+)?(\d+)\b", q_lower) or re.search(r"\bbrightness\s+(?:to\s+)?(\d+)%?\b", q_lower)
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
'''

sec_5_lines = [l + "\n" for l in sec_5_code.splitlines()]
sec_0e_lines = [l + "\n" for l in sec_0e_code.splitlines()]

# Slicing: replace sec5 first, then insert sec_0e
lines[idx_sec5_start:idx_sec6_start] = sec_5_lines
lines[idx_ollama_end:idx_ollama_end] = sec_0e_lines

with open(WIDGET_PATH, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Successfully written to void-widget.py.")
py_compile.compile(WIDGET_PATH, doraise=True)
print("py_compile PASSED!")
