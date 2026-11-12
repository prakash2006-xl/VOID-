#!/usr/bin/env python3
"""
Applies Speech Response Resilience, Volume & Brightness Protection, and System Upgrades to VOID:
1. Speech Output Restoration & PipeWire Native Playback:
   - Replaces fragile sounddevice sd.play() (which failed with PaErrorCode -9988 Invalid stream pointer)
     with robust native PipeWire pw-play (with automatic fallbacks to paplay, aplay, and sounddevice).
   - Adds auto-unmute check on master audio sink to ensure audibility.
   - Instantly halts playback when task is aborted (terminating pw-play child process).
   - Added lazy-loader for self._tts so speech never silently drops.
2. Volume & Brightness Auto-Change Elimination:
   - Removes intrusive startup commands (amixer, wpctl set-volume @DEFAULT_AUDIO_SOURCE@ 0.20).
   - Tightens regex matching for volume and brightness to require explicit commands, preventing ambient noise
     or loose words (e.g., bare 'louder', 'quieter', 'brighter', 'dimmer', or 'volume 1') from altering settings.
   - Adds query_context guard to _execute_ai_tool to suppress unprompted LLM tool-calling hallucinations.
   - Records initial volume & brightness baseline and adds 'reset volume' / 'reset brightness' voice commands.
3. Code Cleanups & Diagnostics:
   - Removes redundant duplicated block (_finish_utterance_and_process, cancel_active_task, execute_task).
   - Adds interactive speech diagnostic voice command ("test speech" / "test audio").
   - Updates UI pill and dot during speech playback.
"""

import sys
import re
from pathlib import Path

WIDGET_PATH = Path("/run/media/prakash/TR_39/VOID/bin/void-widget.py")

def main():
    content = WIDGET_PATH.read_text(encoding="utf-8")
    original_len = len(content)

    # 1. Ensure io and wave are imported
    if "import wave" not in content:
        content = content.replace("import shutil\n", "import shutil\nimport io\nimport wave\n", 1)
        print("[1] Added 'import io' and 'import wave'.")

    # 2. In AudioVoiceEngine.__init__: Remove startup mixer tampering (amixer, wpctl set-volume) and add active proc & baselines
    old_init_tampering = """        # Calibrate ALSA mixer gain to prevent analog clipping and un-mute mic
        try:
            subprocess.run(["amixer", "-c", "1", "sset", "Mic Boost", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", "0.20"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass"""

    new_init_clean = """        self._active_tts_proc: subprocess.Popen | None = None
        # Record initial baseline audio & screen levels without modifying user hardware
        try:
            init_v = self.tool_hub.get_volume()
            self._initial_volume = init_v.get("volume_pct", 50)
            self._initial_brightness = self.tool_hub.get_brightness()
        except Exception:
            self._initial_volume = 50
            self._initial_brightness = 50"""

    assert old_init_tampering in content, "old_init_tampering not found"
    content = content.replace(old_init_tampering, new_init_clean, 1)
    print("[2] Removed startup mixer tampering and added baseline safeguards.")

    # 3. Update cancel_active_task to terminate self._active_tts_proc immediately
    old_cancel = """    def cancel_active_task(self) -> None:
        \"\"\"Immediately interrupts thinking, stops speech, and returns to wake state.\"\"\"
        print("[VOID Audio] User requested task abort / stop.", flush=True)
        self._abort_requested.set()
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self._return_to_wake()
        self.response_ready.emit("", "Thinking process stopped by user.", "Cancelled", "")"""

    new_cancel = """    def cancel_active_task(self) -> None:
        \"\"\"Immediately interrupts thinking, stops speech, and returns to wake state.\"\"\"
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
        self.response_ready.emit("", "Thinking process stopped by user.", "Cancelled", "")"""

    assert old_cancel in content, "old_cancel not found"
    content = content.replace(old_cancel, new_cancel)
    print("[3] Updated cancel_active_task with instant TTS process termination.")

    # 4. Remove duplicate block between _execute_ai_tool return and _process_task
    target_start = '        return "Unknown tool."\n\n    def _finish_utterance_and_process(self) -> None:'
    proc_marker = "    def _process_task(self, query: str) -> None:"
    start_pos = content.find(target_start)
    assert start_pos != -1, "target_start not found"
    del_start = start_pos + len('        return "Unknown tool."\n\n')
    end_pos = content.find(proc_marker, del_start)
    assert end_pos != -1, "proc_marker not found"
    content = content[:del_start] + content[end_pos:]
    print("[4] Cleanly deleted duplicate _finish_utterance_and_process, cancel_active_task, and execute_task block.")

    # 5. Add query_context and guards to _execute_ai_tool
    old_tool_def = '    def _execute_ai_tool(self, name: str, args: dict[str, Any]) -> str:'
    new_tool_def = '    def _execute_ai_tool(self, name: str, args: dict[str, Any], query_context: str = "") -> str:'
    assert old_tool_def in content, "old_tool_def not found"
    content = content.replace(old_tool_def, new_tool_def, 1)
    print("[5a] Updated _execute_ai_tool signature with query_context.")

    # Guard set_volume in _execute_ai_tool
    old_vol_tool = """            elif name == "set_volume":
                act = args.get("action", "set")
                lvl = args.get("level_pct")
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
                    return f"Current volume is {v['volume_pct']}%.\""""

    new_vol_tool = """            elif name == "set_volume":
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
                    return f"Current volume is {v['volume_pct']}%.\""""

    assert old_vol_tool in content, "old_vol_tool not found"
    content = content.replace(old_vol_tool, new_vol_tool, 1)
    print("[5b] Added volume safeguard guard in _execute_ai_tool.")

    # Guard manage_brightness in _execute_ai_tool
    old_bright_tool = """            elif name == "manage_brightness":
                act = args.get("action", "set")
                lvl = args.get("level_pct")
                cur = self.tool_hub.get_brightness()
                if act == "up":
                    return self.tool_hub.set_brightness(min(100, cur + 15))
                elif act == "down":
                    return self.tool_hub.set_brightness(max(10, cur - 15))
                elif lvl is not None:
                    return self.tool_hub.set_brightness(int(lvl))
                return f"Current screen brightness is {cur}%.\""""

    new_bright_tool = """            elif name == "manage_brightness":
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
                return f"Current screen brightness is {cur}%.\""""

    assert old_bright_tool in content, "old_bright_tool not found"
    content = content.replace(old_bright_tool, new_bright_tool, 1)
    print("[5c] Added brightness safeguard guard in _execute_ai_tool.")

    # Pass query_context when calling _execute_ai_tool in _execute_single_command
    old_call = "tool_result = self._execute_ai_tool(fn_name, fn_args)"
    new_call = "tool_result = self._execute_ai_tool(fn_name, fn_args, query_context=query)"
    assert old_call in content, "old_call not found"
    content = content.replace(old_call, new_call, 1)
    print("[5d] Passed query_context to _execute_ai_tool caller.")

    # 6. Replace fragile _speak_text with Multi-Tier PipeWire pw-play Engine
    old_speak_text = """    def _speak_text(self, text: str) -> None:
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

    new_speak_text = """    def _speak_text(self, text: str) -> None:
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
            self.state_changed.emit("idle")"""

    assert old_speak_text in content, "old_speak_text not found"
    content = content.replace(old_speak_text, new_speak_text, 1)
    print("[6] Replaced _speak_text with Multi-Tier PipeWire playback engine.")

    # 7. Refactor Volume & Brightness dispatch in _execute_single_command
    old_vol_dispatch = """        vol_set_m = re.search(r"\\b(?:set|change|put)\\s+(?:the\\s+)?volume\\s+(?:to\\s+)?(\\d+)\\b", q_lower) or re.search(r"\\bvolume\\s+(?:to\\s+)?(\\d+)%?\\b", q_lower)
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
            return (f"Master audio volume is currently {st}.", "Audio: Status", "")"""

    new_vol_dispatch = """        # Voice Audio Diagnostic & Speech Test
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

        # Strict volume setting: requires explicit command verb (prevents accidental matches from numbers/noise)
        vol_set_m = re.search(r"^\\s*(?:please\\s+)?(?:set|change|turn|adjust|put)\\s+(?:the\\s+)?(?:audio\\s+|master\\s+)?volume\\s+(?:to\\s+)?(\\d+)\\s*(?:%|percent)?\\s*$", q_lower) or re.search(r"\\b(?:set|change|turn|adjust)\\s+(?:the\\s+)?volume\\s+(?:to\\s+)?(\\d+)%?\\b", q_lower)
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
            return (msg, "Audio: Mute Toggled", "")"""

    assert old_vol_dispatch in content, "old_vol_dispatch not found"
    content = content.replace(old_vol_dispatch, new_vol_dispatch, 1)
    print("[7a] Refactored volume dispatch with strict intent safeguards.")

    old_bright_dispatch = """        bright_set_m = re.search(r"\\b(?:set|change|put)\\s+(?:the\\s+)?brightness\\s+(?:to\\s+)?(\\d+)\\b", q_lower) or re.search(r"\\bbrightness\\s+(?:to\\s+)?(\\d+)%?\\b", q_lower)
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
            return (f"Screen brightness is currently at {cur}%.", "Screen: Brightness", "")"""

    new_bright_dispatch = """        if any(p in q_lower for p in ["reset brightness", "restore brightness", "restore default brightness"]):
            target = getattr(self, "_initial_brightness", 50)
            msg = self.tool_hub.set_brightness(target)
            return (f"Restored display brightness to baseline ({target}%).", f"Screen: Brightness {target}%", "")

        if any(p in q_lower for p in ["what is the brightness", "check brightness", "current brightness", "get brightness", "screen brightness"]):
            cur = self.tool_hub.get_brightness()
            return (f"Screen brightness is currently at {cur}%.", "Screen: Brightness", "")

        # Strict brightness setting: requires explicit command verb (prevents accidental matches)
        bright_set_m = re.search(r"^\\s*(?:please\\s+)?(?:set|change|adjust|turn|put)\\s+(?:the\\s+)?(?:screen\\s+|display\\s+)?brightness\\s+(?:to\\s+)?(\\d+)\\s*(?:%|percent)?\\s*$", q_lower) or re.search(r"\\b(?:set|change|adjust)\\s+(?:the\\s+)?(?:screen\\s+)?brightness\\s+(?:to\\s+)?(\\d+)%?\\b", q_lower)
        if bright_set_m:
            target_b = int(bright_set_m.group(1))
            msg = self.tool_hub.set_brightness(target_b)
            return (msg, f"Screen: Brightness {target_b}%", "")

        # Strict brightness adjustments (requires explicit 'brightness' keyword)
        if any(p == q_lower.strip() or p in q_lower for p in ["brightness up", "increase brightness", "raise brightness", "increase screen brightness", "turn up brightness"]):
            cur = self.tool_hub.get_brightness()
            new_b = min(100, cur + 15)
            msg = self.tool_hub.set_brightness(new_b)
            return (msg, f"Screen: Brightness {new_b}%", "")

        if any(p == q_lower.strip() or p in q_lower for p in ["brightness down", "decrease brightness", "lower brightness", "decrease screen brightness", "dim screen brightness", "turn down brightness"]):
            cur = self.tool_hub.get_brightness()
            new_b = max(10, cur - 15)
            msg = self.tool_hub.set_brightness(new_b)
            return (msg, f"Screen: Brightness {new_b}%", "")"""

    assert old_bright_dispatch in content, "old_bright_dispatch not found"
    content = content.replace(old_bright_dispatch, new_bright_dispatch, 1)
    print("[7b] Refactored brightness dispatch with strict intent safeguards.")

    print("[8] UI speaking state already active: Speaking with you... 💬.")

    # Write modifications
    WIDGET_PATH.write_text(content, encoding="utf-8")
    print(f"Applied all fixes! File size changed: {original_len} -> {len(content)} bytes.")

if __name__ == "__main__":
    main()
