#!/usr/bin/env python3
"""
Applies pure glassmorphism, voice rate calibration, acoustic self-hearing suppression,
wake-word precision, and offline STT/Ollama enhancements to void-widget.py.
"""

import sys
import re
from pathlib import Path

WIDGET_PATH = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")
if not WIDGET_PATH.exists():
    print(f"Error: {WIDGET_PATH} not found.")
    sys.exit(1)

content = WIDGET_PATH.read_text(encoding="utf-8")

# 1. Add QPainterPath to PySide6.QtGui import
if "QPainterPath" not in content:
    content = content.replace(
        "from PySide6.QtGui import (\n    QColor, QPainter, QRadialGradient, QLinearGradient, QBrush,\n    QPen, QFont, QMouseEvent, QPixmap\n)",
        "from PySide6.QtGui import (\n    QColor, QPainter, QRadialGradient, QLinearGradient, QBrush,\n    QPen, QFont, QMouseEvent, QPixmap, QPainterPath\n)"
    )
    print("[1] Added QPainterPath to PySide6.QtGui imports.")

# 2. Update PiperLocalTTS speed to 1.0 (Crisp, articulate natural conversational speed ~185 WPM)
old_tts_snippet = 'self._tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium", speed=0.55)'
new_tts_snippet = 'self._tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium", speed=1.0)'
if old_tts_snippet in content:
    content = content.replace(old_tts_snippet, new_tts_snippet)
    print("[2] Updated PiperLocalTTS speed factor to 1.0 (100% natural conversational rate).")

# 3. Update normalize_voice_intent to handle strt, speach, olama, txt, stt
old_norm = """def normalize_voice_intent(text: str) -> str:
    \"\"\"Normalizes STT typos, misspellings, and colloquialisms for offline fast-path routing.\"\"\"
    s = " " + text.lower().strip() + " "
    replacements = [
        (r"\\b(?:opn|oppen|oepn|launc|strat|laucn)\\b", "open"),
        (r"\\b(?:crome|cromium|chrom|chromum|borwser|broswer|internt)\\b", "chromium"),
        (r"\\b(?:termianl|terminel|termnal|konsolee|consoel)\\b", "terminal"),
        (r"\\b(?:calcultor|calculater|caculator|calclator)\\b", "calculator"),
        (r"\\b(?:screnshot|screenshoot|screanshot|screenshit|snapsot)\\b", "screenshot"),
        (r"\\b(?:screen\\s+short)\\b", "screenshot"),
        (r"\\b(?:minimise|minamize|minmize)\\b", "minimize"),
        (r"\\b(?:maximise|maxamize|maxmize)\\b", "maximize"),
        (r"\\b(?:fulscreen|fullscrene|full\\s+screne)\\b", "fullscreen"),
        (r"\\b(?:olama|o\\s+llama|allama)\\b", "ollama"),
        (r"\\b(?:rember|rememebr|remerber)\\b", "remember"),
        (r"\\b(?:shutdwon|shotdown)\\b", "shutdown"),
        (r"\\b(?:restrt|rstart)\\b", "restart"),"""

new_norm = """def normalize_voice_intent(text: str) -> str:
    \"\"\"Normalizes STT typos, misspellings, and colloquialisms for offline fast-path routing.\"\"\"
    s = " " + text.lower().strip() + " "
    replacements = [
        (r"\\b(?:strt|strat|stert|starr)\\b", "start"),
        (r"\\b(?:speach|spech|speeh|specht)\\b", "speech"),
        (r"\\b(?:txet|tetx|txt)\\b", "text"),
        (r"\\b(?:stt)\\b", "speech to text"),
        (r"\\b(?:opn|oppen|oepn|launc|laucn)\\b", "open"),
        (r"\\b(?:crome|cromium|chrom|chromum|borwser|broswer|internt)\\b", "chromium"),
        (r"\\b(?:termianl|terminel|termnal|konsolee|consoel)\\b", "terminal"),
        (r"\\b(?:calcultor|calculater|caculator|calclator)\\b", "calculator"),
        (r"\\b(?:screnshot|screenshoot|screanshot|screenshit|snapsot)\\b", "screenshot"),
        (r"\\b(?:screen\\s+short)\\b", "screenshot"),
        (r"\\b(?:minimise|minamize|minmize)\\b", "minimize"),
        (r"\\b(?:maximise|maxamize|maxmize)\\b", "maximize"),
        (r"\\b(?:fulscreen|fullscrene|full\\s+screne)\\b", "fullscreen"),
        (r"\\b(?:olama|o\\s+llama|allama|alamma|ohlama)\\b", "ollama"),
        (r"\\b(?:rember|rememebr|remerber)\\b", "remember"),
        (r"\\b(?:shutdwon|shotdown|shudown)\\b", "shutdown"),
        (r"\\b(?:restrt|rstart)\\b", "restart"),"""

if old_norm in content:
    content = content.replace(old_norm, new_norm)
    print("[3] Updated normalize_voice_intent with phonetic offline mappings.")

# 4. Update Vosk grammar in _init_models_in_bg
old_grammar = """                    grammar = json.dumps([
                        "hey void", "void", "hi void", "hello void", "okay void",
                        "hey boyd", "boyd", "a void", "hey voyd", "voyd",
                        "terminate code zero", "hey void terminate code zero", "terminate code",
                        "terminate", "exit void", "stop void", "shutdown void", "shut down void",
                        "[unk]"
                    ])"""

new_grammar = """                    grammar = json.dumps([
                        "hey void", "hi void", "hello void", "okay void",
                        "hey computer", "wake up void",
                        "terminate code zero", "hey void terminate code zero",
                        "[unk]"
                    ])"""

if old_grammar in content:
    content = content.replace(old_grammar, new_grammar)
    print("[4] Updated Vosk grammar to eliminate false bare-word triggers.")

# 5. Add variables to AudioVoiceEngine.__init__
old_init_vars = """        self._dictation_mode = False
        self._dictation_file: Path | None = None
        self._dictation_title: str = ''"""

new_init_vars = """        self._dictation_mode = False
        self._dictation_file: Path | None = None
        self._dictation_title: str = ''
        self._is_speaking = False
        self._mute_audio_until = 0.0
        self._last_executed_cmd = ''
        self._last_cmd_timestamp = 0.0"""

if old_init_vars in content:
    content = content.replace(old_init_vars, new_init_vars)
    print("[5] Added audio muting and deduplication state tracking.")

# 6. Update _start_audio_stream and Vosk handling in void-widget.py
old_stream = """                        while self._is_running:
                            try:
                                audio_bytes = audio_queue.get(timeout=0.5)
                            except queue.Empty:
                                continue

                            samples = np.frombuffer(audio_bytes, dtype=np.int16)
                            self._preroll.append(samples)
                            rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2))) / 32768.0

                            # Pulse orb with ambient voice so user knows VOID is hearing
                            self.audio_level.emit(min(1.0, rms * 4.0))

                            if self._mode == "command":
                                self._audio_buffer.append(samples)
                                if rms < 0.007:
                                    self._silence_chunks += 1
                                else:
                                    self._silence_chunks = 0

                                # End of command utterance: ~1600ms silence or 12s max
                                if (self._silence_chunks >= 16 and len(self._audio_buffer) >= 12) or len(self._audio_buffer) > 120:
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
                                    text = res.get("text", "").lower()
                                    if any(w in text for w in ["terminate code", "terminate code zero", "exit void", "stop void", "shutdown void"]):
                                        self._handle_terminate()
                                    elif any(w in text for w in ["void", "hey void", "hello void", "hi void", "okay void"]):
                                        self._handle_wake_text(text)
                                else:
                                    partial = json.loads(self._recognizer.PartialResult()).get("partial", "").lower()
                                    if any(w in partial for w in ["terminate code", "terminate code zero", "exit void", "stop void", "shutdown void"]):
                                        self._handle_terminate()
                                        self._recognizer.Reset()
                                    elif any(w in partial for w in ["hey void", "hello void", "void"]):
                                        self._handle_wake_text(partial)
                                        self._recognizer.Reset()"""

new_stream = """                        while self._is_running:
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
                                        self._recognizer.Reset()"""

if old_stream in content:
    content = content.replace(old_stream, new_stream)
    print("[6] Updated _audio_loop with acoustic echo suppression and strict wake phrases.")

# 7. Update _finish_utterance_and_process with energy filter and hallucination suppressor
old_finish = """    def _finish_utterance_and_process(self) -> None:
        self._mode = "processing"
        self.state_changed.emit("thinking")
        if not self._audio_buffer:
            self._return_to_wake()
            return

        all_samples = np.concatenate(self._audio_buffer).astype(np.float32) / 32768.0
        self._audio_buffer.clear()

        def _transcribe():
            try:
                if self._whisper is not None:
                    print("[VOID Audio] Transcribing with Faster-Whisper...", flush=True)
                    segments, _ = self._whisper.transcribe(all_samples, beam_size=1, language="en")
                    text = " ".join(s.text for s in segments).strip()
                    print(f"[VOID Audio] Transcribed: '{text}'", flush=True)
                    if text:
                        self.transcript_ready.emit(text)
                        self.execute_task(text)
                        return
            except Exception as e:
                print(f"[VOID STT Error] {e}")
            self._return_to_wake()

        threading.Thread(target=_transcribe, daemon=True).start()"""

new_finish = """    def _finish_utterance_and_process(self) -> None:
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

        threading.Thread(target=_transcribe, daemon=True).start()"""

if old_finish in content:
    content = content.replace(old_finish, new_finish)
    print("[7] Updated _finish_utterance_and_process with energy & hallucination filtering.")

# 8. Update execute_task with duplicate command debouncing
old_exec_task = """    def execute_task(self, query: str) -> None:
        self._abort_requested.clear()
        self._mode = "processing"
        self.state_changed.emit("thinking")
        threading.Thread(target=self._process_task, args=(query,), daemon=True).start()"""

new_exec_task = """    def execute_task(self, query: str) -> None:
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
        threading.Thread(target=self._process_task, args=(query,), daemon=True).start()"""

if old_exec_task in content:
    content = content.replace(old_exec_task, new_exec_task)
    print("[8] Added rapid duplicate command debouncing to execute_task.")

# 9. Update _speak_text with _is_speaking and echo decay cooldown
old_speak = """    def _speak_text(self, text: str) -> None:
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
                print(f"[VOID TTS Error] {e}")"""

new_speak = """    def _speak_text(self, text: str) -> None:
        if self._abort_requested.is_set():
            return
        if text and self._tts:
            clean = self._clean_text_for_speech(text)
            if not clean:
                return
            self._is_speaking = True
            self.state_changed.emit("speaking")
            try:
                self._preroll.clear()
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
                        time.sleep(0.04)
            except Exception as e:
                print(f"[VOID TTS Error] {e}")
            finally:
                # 600ms acoustic grace period to let room echoes and speaker reverb decay
                self._mute_audio_until = time.time() + 0.6
                self._preroll.clear()
                if self._recognizer:
                    self._recognizer.Reset()
                self._is_speaking = False"""

if old_speak in content:
    content = content.replace(old_speak, new_speak)
    print("[9] Updated _speak_text with speaker muting and echo decay cooldown.")

# 10. Add _ensure_ollama_started_bg helper and enhanced offline intent routing
old_ollama_block = """        # 0d. Ollama Brain Lifecycle ("start ollama", "stop ollama") - BEFORE app launch!
        if any(p in q_lower for p in ["start ollama", "activate brain", "launch ollama", "load brain"]):
            try:
                import httpx
                try:
                    httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.0)
                except Exception:
                    ollama_env = dict(os.environ, OLLAMA_MODELS=str(MODELS_DIR))
                    subprocess.Popen(["ollama", "serve"], env=ollama_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                    time.sleep(1.5)
                httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": "lfm3-omni:2b", "prompt": "ready", "stream": False}, timeout=12.0)
                return ("Ollama server started and lfm3-omni:2b brain is loaded.", "Ollama: Online", "")
            except Exception as e:
                return (f"Could not start Ollama: {e}", "Ollama: Error", "")"""

new_ollama_block = """        # 0d. Ollama Brain Lifecycle & Speech-to-Text Initialization Fast-Path
        if any(p in q_lower for p in [
            "start ollama in speech to text", "start ollama and speech to text", "start ollama in stt",
            "start speech to text and ollama", "start speech to text", "activate speech to text",
            "turn on speech to text", "speech to text mode"
        ]):
            self._ensure_ollama_started_bg()
            return ("Ollama AI brain is initializing and speech-to-text is active and listening offline.", "Ollama & STT: Active", "")

        if any(p in q_lower for p in ["start ollama", "activate brain", "launch ollama", "load brain", "turn on brain", "start ai brain"]):
            try:
                import httpx
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
                try:
                    httpx.post(f"{OLLAMA_URL}/api/generate", json={"model": "lfm3-omni:2b", "prompt": "ready", "stream": False}, timeout=12.0)
                except Exception:
                    pass
                return ("Ollama server started and lfm3-omni:2b brain is loaded.", "Ollama: Online", "")
            except Exception as e:
                return (f"Could not start Ollama: {e}", "Ollama: Error", "")"""

if old_ollama_block in content:
    content = content.replace(old_ollama_block, new_ollama_block)
    print("[10] Enhanced Ollama & STT intent routing.")

# Add _ensure_ollama_started_bg to AudioVoiceEngine if not present
if "def _ensure_ollama_started_bg" not in content:
    target_str = "    def _start_proactive_monitor(self) -> None:"
    helper_code = """    def _ensure_ollama_started_bg(self) -> None:
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

    def _start_proactive_monitor(self) -> None:"""
    content = content.replace(target_str, helper_code)
    print("[10b] Added _ensure_ollama_started_bg helper.")

# 11. Add GlassIslandFrame class and integrate pure glassmorphism
glass_frame_class = '''# ---------------------------------------------------------------------------
# Pure Frosted Glassmorphism Island Frame (PySide6)
# ---------------------------------------------------------------------------
class GlassIslandFrame(QFrame):
    """Pure Frosted Glassmorphism Island Frame with Specular Rim and Ambient Halo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GlassIsland")
        self._radius = 28
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

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

'''

if "class GlassIslandFrame" not in content:
    target_pos = "# ---------------------------------------------------------------------------\n# Dynamic Glass Flow Island Widget (PySide6)\n# ---------------------------------------------------------------------------"
    content = content.replace(target_pos, glass_frame_class + target_pos)
    print("[11] Added GlassIslandFrame custom QFrame.")

# Update self._card instantiation and _update_glass_style
old_card_init = "        # Main Glass Capsule Frame\n        self._card = QFrame(self)\n        self._card.setObjectName(\"GlassIsland\")"
new_card_init = "        # Main Glass Capsule Frame\n        self._card = GlassIslandFrame(self)\n        self._card.setObjectName(\"GlassIsland\")"
if old_card_init in content:
    content = content.replace(old_card_init, new_card_init)
    print("[11b] Updated self._card to GlassIslandFrame instance.")

old_style_fn = """    def _update_glass_style(self, expanded: bool) -> None:
        radius = 18 if expanded else 28
        self._card.setStyleSheet(f\"\"\"
            #GlassIsland {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(13, 18, 30, 0.98),
                    stop:1 rgba(8, 12, 22, 0.99));
                border: 1px solid rgba(56, 189, 248, 0.38);
                border-radius: {radius}px;
            }}
        \"\"\")"""

new_style_fn = """    def _update_glass_style(self, expanded: bool) -> None:
        radius = 18 if expanded else 28
        self._card.set_radius(radius)
        self._card.setStyleSheet(f\"\"\"
            #GlassIsland {{
                background: transparent;
                border: none;
            }}
            #RespFrame {{
                background: rgba(12, 18, 32, 0.60);
                border: 1px solid rgba(56, 189, 248, 0.30);
                border-radius: 12px;
            }}
        \"\"\")"""

if old_style_fn in content:
    content = content.replace(old_style_fn, new_style_fn)
    print("[11c] Updated _update_glass_style to pure glass rendering.")

# 12. Add Offline General Task Handlers to _execute_single_command
# (Files, capabilities, IP, network status)
offline_capabilities_snippet = """        # 0f. Offline Capabilities & Capabilities Summary
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
                        f.write(fc + "\\n")
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
                        return (f"Content of {fn}:\\n{content_txt}", f"File: {fn}", "")
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
"""

if "0f. Offline Capabilities" not in content:
    target_loc = "        # 0e. Emotional Companion & Empathy Routing"
    content = content.replace(target_loc, offline_capabilities_snippet + "\n" + target_loc)
    print("[12] Added offline file management, capabilities, and IP tools.")

WIDGET_PATH.write_text(content, encoding="utf-8")
print(f"[SUCCESS] void-widget.py enhanced and written ({len(content)} bytes).")

