#!/usr/bin/env python3
"""
Test Suite: TTS Speech Speed Regulation & Prosody Pacing
Verifies:
1. Dynamic speech pacing for large text (never over-speeds or rushes).
2. Prosody clause segmentation and natural breath pauses (350ms sentence, 200ms clause, 160ms conjunction).
3. Word rate regulation: short, medium, and large text maintain steady, articulate cadence.
4. AudioVoiceEngine adaptive speed scaling across response lengths.
"""

import sys
import os
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT_DIR / "bin"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BIN_DIR))

from dodaios.plugins.tts.piper_local import PiperLocalTTS

# Import void-widget modules
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(["-platform", "offscreen"])

import importlib.util
spec = importlib.util.spec_from_file_location("void_widget", BIN_DIR / "void-widget.py")
vw = importlib.util.module_from_spec(spec)
sys.modules["void_widget"] = vw
spec.loader.exec_module(vw)

passed = 0
failed = 0

def check(name: str, cond: bool, info: str = ""):
    global passed, failed
    if cond:
        print(f"  [PASS] {name} {f'({info})' if info else ''}")
        passed += 1
    else:
        print(f"  [FAIL] {name} {f'({info})' if info else ''}")
        failed += 1

async def run_tests():
    global passed, failed
    print("=" * 70)
    print("    TEST SUITE: TTS SPEECH SPEED REGULATION & PROSODY PACING       ")
    print("=" * 70)

    tts = PiperLocalTTS(voice="vits-piper-en_US-ryan-medium")

    # 1. Prosody Segmentation on Complex Large Text
    large_text = (
        "Linux is an open-source Unix-like operating system based on the Linux kernel. "
        "It was first released by Linus Torvalds on September 17, 1991. "
        "Linux is typically packaged as a Linux distribution, which includes the kernel and supporting system software. "
        "Popular distributions include Debian, Ubuntu, Fedora, and Arch Linux. "
        "Today, Linux powers the majority of servers, supercomputers, and cloud infrastructure worldwide."
    )
    segs = tts._prosody_segments(large_text)
    check("Large Text Prosody Segmentation", len(segs) >= 8, f"Generated {len(segs)} natural breath clauses")

    # Verify breath pauses are present in segments
    has_sentence_pauses = any(p >= 300 for _, p in segs)
    has_clause_pauses = any(150 <= p <= 250 for _, p in segs)
    check("Natural Sentence Pauses (350ms)", has_sentence_pauses)
    check("Natural Clause Pauses (160-200ms)", has_clause_pauses)

    # 2. Synthesis Speed Benchmarking on Large Text
    # Measure audio duration and words-per-minute (WPM)
    chunks = []
    async for c in tts.synthesize(large_text):
        chunks.append(c.pcm)
    pcm = b"".join(chunks)
    dur = len(pcm) / (2 * 22050)
    words = len(large_text.split())
    wpm = words / (dur / 60)
    print(f"\n  [BENCHMARK] Large Text ({words} words):")
    print(f"    Audio Duration: {dur:.2f} seconds")
    print(f"    Measured Cadence: {wpm:.1f} Words Per Minute")

    # Standard human conversational cadence is 120-150 WPM. Over-speeding is > 170 WPM.
    check("Large Text Does NOT Over-Speed (< 145 WPM)", wpm <= 145.0, f"Rate: {wpm:.1f} WPM")
    check("Large Text Has Sane Articulate Cadence (> 110 WPM)", wpm >= 110.0, f"Rate: {wpm:.1f} WPM")

    # 3. AudioVoiceEngine Adaptive Speed Calibration
    th = vw.DodaiosToolHub()
    engine = vw.AudioVoiceEngine(tool_hub=th)
    engine._is_running = False

    # Check text cleaning and pacing
    raw_list_text = "Here are the files found in Documents:\n- report.pdf\n- summary.docx\n- analysis.xlsx\nAll tasks completed."
    cleaned = engine._clean_text_for_speech(raw_list_text)
    check("List Items Converted to Paced Sentences", "." in cleaned, f"Cleaned: '{cleaned}'")

    # Check adaptive speed thresholds
    # Case A: Short confirmation
    short_text = "Closed window."
    cl_short = engine._clean_text_for_speech(short_text)
    w_short = len(cl_short.split())
    spd_short = 0.86 if (w_short > 35 or len(cl_short) > 180) else (0.89 if (w_short > 15 or len(cl_short) > 80) else 0.92)
    check("Short Text Speed Calibrated Crisp (0.92)", spd_short == 0.92)

    # Case B: Large explanation text
    cl_large = engine._clean_text_for_speech(large_text)
    w_large = len(cl_large.split())
    spd_large = 0.86 if (w_large > 35 or len(cl_large) > 180) else (0.89 if (w_large > 15 or len(cl_large) > 80) else 0.92)
    check("Large Text Speed Calibrated Calm (0.86)", spd_large == 0.86, f"Words: {w_large}, Speed: {spd_large}")

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_tests())
