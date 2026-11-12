import re
import py_compile

WIDGET_PATH = "/run/media/prakash/TR_39/VOID/bin/void-widget.py"
with open(WIDGET_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update PiperLocalTTS speed to 0.55 (Calm, articulate, clear 160 WPM conversational speed)
old_tts = 'self._tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium")'
new_tts = 'self._tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium", speed=0.55)'
assert old_tts in content, "old_tts not found"
content = content.replace(old_tts, new_tts, 1)

# 2. Update normalize_voice_intent with whatsapp web speech slips
old_norm = '(r"\\b(?:attendongh|attendng|attendin)\\b", "attending"),'
new_norm = '''(r"\\b(?:attendongh|attendng|attendin)\\b", "attending"),
        (r"\\b(?:whats\\s*app|whatsaap|whatsup|what's\\s+up|whats\\s+up|whatsap|whats\\s+a)\\b", "whatsapp"),
        (r"\\b(?:vib|veb|bib)\\b", "web"),'''
assert old_norm in content, "old_norm not found"
content = content.replace(old_norm, new_norm, 1)

# 3. Add Web Services direct navigation before open http
old_open_http = '        if q_lower.startswith("open http") or q_lower.startswith("go to http") or any(ext in q_lower for ext in [".com", ".org", ".io", ".net", ".edu", ".dev"]):'
new_open_http = '''        # Direct Web Services Fast-Path (WhatsApp Web, YouTube, GitHub, Reddit, Gmail)
        web_services = {
            "whatsapp web": ("https://web.whatsapp.com", "WhatsApp Web"),
            "whatsapp": ("https://web.whatsapp.com", "WhatsApp Web"),
            "youtube": ("https://www.youtube.com", "YouTube"),
            "github": ("https://github.com", "GitHub"),
            "reddit": ("https://www.reddit.com", "Reddit"),
            "gmail": ("https://mail.google.com", "Gmail"),
        }
        for svc_name, (svc_url, svc_disp) in web_services.items():
            if re.search(rf"\\b(?:open|launch|go\\s+to)\\s+(?:the\\s+)?{svc_name}\\b", q_lower) or q_lower.strip() in [svc_name, f"open {svc_name}"]:
                msg = self.tool_hub.open_browser(url=svc_url, new_tab=True)
                return (f"Opened {svc_disp} in Chromium.", f"Browser: {svc_disp}", "")

        if q_lower.startswith("open http") or q_lower.startswith("go to http") or any(ext in q_lower for ext in [".com", ".org", ".io", ".net", ".edu", ".dev"]):'''

assert old_open_http in content, "old_open_http not found"
content = content.replace(old_open_http, new_open_http, 1)

# 4. Enhance _speak_text with _clean_text_for_speech to eliminate mumbling & raw code reading
old_speak = '''    def _speak_text(self, text: str) -> None:
        if self._abort_requested.is_set():
            return
        if text and self._tts:
            self.state_changed.emit("speaking")
            try:
                clean = text.replace("*", "").replace("`", "").replace("#", "").strip()
                chunks = []
                for chunk in asyncio.run(self._synth_piper(clean)):
                    if self._abort_requested.is_set():
                        return
                    chunks.append(chunk)
                if chunks and not self._abort_requested.is_set():
                    pcm_all = b"".join(chunks)
                    samples = np.frombuffer(pcm_all, dtype=np.int16)
                    sd.play(samples, samplerate=22050)
                    while sd.get_stream().active:
                        if self._abort_requested.is_set():
                            sd.stop()
                            break
                        time.sleep(0.05)
            except Exception as e:
                print(f"[VOID TTS Error] {e}")'''

new_speak = '''    def _clean_text_for_speech(self, text: str) -> str:
        if not text:
            return ""
        s = text
        # Strip raw model tool calling tags
        s = re.sub(r"<tool_call>.*?</tool_call>", "", s, flags=re.DOTALL)
        s = re.sub(r"<function=[^>]+>", "", s)
        s = re.sub(r"<parameter=[^>]+>", "", s)
        s = re.sub(r"</?[a-zA-Z0-9_-]+>", "", s)

        # Clean tool names and technical identifiers to natural English words
        s = re.sub(r"\\b([a-z]+)_([a-z]+)\\b", r"\\1 \\2", s)

        # Clean markdown symbols
        s = re.sub(r"\\*\\*([^*]+)\\*\\*", r"\\1", s)
        s = re.sub(r"\\*([^*]+)\\*", r"\\1", s)
        s = re.sub(r"`([^`]+)`", r"\\1", s)
        s = re.sub(r"^#+\\s*", "", s, flags=re.MULTILINE)

        # Simplify URLs and raw filesystem paths
        s = re.sub(r"https?://\\S+", "the link", s)
        s = re.sub(r"/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)+", "the file", s)

        # Strip emojis and symbols
        s = re.sub(r"[\\U00010000-\\U0010ffff]", "", s)
        s = re.sub(r"[⏱️🎧💭💬💙🎉💫☀️🌙🌤️➔✕●⏺⏹]", "", s)

        # Normalize whitespace and ensure a clean pause between sentences
        s = re.sub(r"\\s+", " ", s).strip()
        s = re.sub(r"\\?\\s*", "? ", s)
        return s

    def _speak_text(self, text: str) -> None:
        if self._abort_requested.is_set():
            return
        if text and self._tts:
            clean = self._clean_text_for_speech(text)
            if not clean:
                return
            self.state_changed.emit("speaking")
            try:
                chunks = []
                for chunk in asyncio.run(self._synth_piper(clean)):
                    if self._abort_requested.is_set():
                        return
                    chunks.append(chunk)
                if chunks and not self._abort_requested.is_set():
                    pcm_all = b"".join(chunks)
                    samples = np.frombuffer(pcm_all, dtype=np.int16)
                    sd.play(samples, samplerate=22050)
                    while sd.get_stream().active:
                        if self._abort_requested.is_set():
                            sd.stop()
                            break
                        time.sleep(0.05)
            except Exception as e:
                print(f"[VOID TTS Error] {e}")'''

assert old_speak in content, "old_speak not found"
content = content.replace(old_speak, new_speak, 1)

with open(WIDGET_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("[Apply] Successfully applied speech speed regulation & text cleaner.")
py_compile.compile(WIDGET_PATH, doraise=True)
print("[Apply] py_compile PASSED!")
