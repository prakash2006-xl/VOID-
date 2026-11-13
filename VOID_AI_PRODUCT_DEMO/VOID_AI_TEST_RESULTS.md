# VOID AI — Verification & Automated Test Suite Results

## 1. Test Suite Summary
- **Evaluation Platform:** Fedora Linux 40+ (KDE Plasma 6 / Wayland)
- **Hardware Architecture:** AMD Ryzen 7 5700U (8 Cores, 16 Threads), 16 GB RAM
- **Test Framework:** pytest & custom automated acceptance suites
- **Verified Results:** 18 Test Suites, 135/135 Tests Passing (**100% Pass Rate**)

| Test Suite Script | Tests | Passed | Failed | Duration | Subsystem Tested | Result |
| :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| `test_3d_globe.py` | 1 | 1 | 0 | 0.12s | 3D Fibonacci Coordinate Projection | **PASS** |
| `test_3d_globe_states.py` | 10 | 10 | 0 | 0.25s | Visual Color State Transitions | **PASS** |
| `test_all_tools_and_emotion.py` | 10 | 10 | 0 | 2.05s | 105 VOID AI Native Tools Connectivity | **PASS** |
| `test_audio_and_wake_isolation.py` | 6 | 6 | 0 | 0.45s | PipeWire Wake Isolation & Vosk FST | **PASS** |
| `test_browser_and_email.py` | 9 | 9 | 0 | 1.82s | Chromium Tab Automation & Webmail | **PASS** |
| `test_dictation_and_documents.py` | 14 | 14 | 0 | 26.4s | Word (.docx) & Excel (.xlsx) Drafting | **PASS** |
| `test_document_tools.py` | 1 | 1 | 0 | 0.18s | Document Authoring & Path Validation | **PASS** |
| `test_email_planning.py` | 4 | 4 | 0 | 0.35s | Recipient Prompts & Email Drafting | **PASS** |
| `test_extended_acceptance_criteria.py` | 6 | 6 | 0 | 1.18s | Sub-5ms Coexistence & Secret Masking | **PASS** |
| `test_generalised_ollama_commands.py` | 4 | 4 | 0 | 0.05s | Dynamic Start/Stop/Restart Lifecycle | **PASS** |
| `test_glass_rendering.py` | 4 | 4 | 0 | 0.22s | Acrylic Glass Styling & Smooth Dragging | **PASS** |
| `test_multi_agent_system.py` | 14 | 14 | 0 | 0.88s | Multi-Agent DAG Planner, 7 Agents | **PASS** |
| `test_offline_routing_and_phonetics.py` | 12 | 12 | 0 | 0.65s | Typo Tolerance & Phonetic Normalizer | **PASS** |
| `test_speech_and_system_invariance.py` | 9 | 9 | 0 | 1.02s | Hardware Volume/Brightness Guard | **PASS** |
| `test_tts_speed.py` | 1 | 1 | 0 | 0.40s | Piper Neural TTS Rate (>160 wpm) | **PASS** |
| `test_universal_open_and_search.py` | 7 | 7 | 0 | 1.15s | Universal File, Media & App Opener | **PASS** |
| `test_weekly_memory_and_cloud.py` | 9 | 9 | 0 | 1.06s | 7-Day Memory Retention & Cloud Fallback | **PASS** |
| `test_youtube_dictation_and_memory.py` | 14 | 14 | 0 | 1.85s | YouTube Control & 1.5GB NVMe Memory | **PASS** |
| **TOTAL** | **135** | **135** | **0** | **~40s** | **Entire System (Zero Regressions)** | **100% PASS** |

---

## 2. Empirical Performance Metrics
- **Direct Command Fast-Path Latency:** **3.8 ms** (Target: <5ms)
- **Wake-Word Acoustic Latency:** **~120 ms** (Vosk Kaldi FST)
- **Speech-to-Text Transcription Latency:** **~350 ms** (Faster-Whisper int8 AVX2)
- **Neural Speech Synthesis Latency:** **~240 ms** (Piper TTS at 1.06x speed)
- **Local `nano-brain` Turnaround Time:** **210 ms - 350 ms** (<150MB RAM)
- **Standby Memory Footprint:** **185 MB** (PySide6 Acrylic Widget)
- **Memory Saved on Model Offload:** **~2.0 GB** (Freed in <20ms via `"stop ollama"`)
- **Emergency Abort Response:** **< 5 ms** (Immediate process termination)

---

## 3. Known Limitations & Technical Boundaries
1. **Wayland Screen Recording:** Automated full-screen video capture under Wayland requires PipeWire desktop portal user grant permissions.
2. **Context Window Limits:** Local quantized models (512 tokens on `nano-brain`, 4096 on `lfm3-omni`) require prompt compaction for large documents.
3. **Noisy Environments:** Acoustic wake detection sensitivity decreases in loud environments (>75 dB SPL).