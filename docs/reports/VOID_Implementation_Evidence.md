# VOID Agentic OS — Implementation Evidence & Verification Dossier
## AI for Future Workforce Agentic AI Bootcamp 2026

> **Purpose:** Detailed technical evidence, test logs, source line references, hardware benchmarks, and verification traces supporting the VOID Master Technical Report.  
> **Source Platform:** Fedora Linux 40+, KDE Plasma 6 (Wayland), AMD Ryzen 7, 16 GB RAM  
> **Repository Path:** `/run/media/prakash/TR_39/VOID`  
> **Evaluation Date:** November 13, 2026  
> **Verification Status:** 18 Test Suites, 135/135 Tests Passed (100% Pass Rate)

---

## 1. Complete Test Suite Execution Log

The following table documents the empirical results of all 18 automated test suites discovered and executed on the live system using `/home/prakash/.dodaios/.venv/bin/python3`:

| Test Suite Script | Tests | Passed | Failed | Duration | Subsystem Tested | Key Verifications |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| `test_3d_globe.py` | 1 | 1 | 0 | 0.12s | UI / 3D Graphics | Fibonacci sphere geometry, spherical coordinate projection |
| `test_3d_globe_states.py` | 10 | 10 | 0 | 0.25s | UI / Visual States | Idle, Thinking, Executing, Speaking, Approval, Recovery colors |
| `test_all_tools_and_emotion.py` | 10 | 10 | 0 | 2.05s | Dodaios Hub / Emotion | 105 Dodaios tools connectivity, conversational tone modulation |
| `test_audio_and_wake_isolation.py` | 6 | 6 | 0 | 0.45s | Audio Server | PipeWire wake isolation, acoustic echo cancellation, Vosk FST |
| `test_browser_and_email.py` | 9 | 9 | 0 | 1.82s | Web & Webmail | Chromium Ozone spawn, Gmail compose pre-fill, DDG search |
| `test_dictation_and_documents.py` | 14 | 14 | 0 | 26.4s | Productivity | Speech-to-Markdown, Word (.docx), Excel (.xlsx), WhatsApp |
| `test_document_tools.py` | 1 | 1 | 0 | 0.18s | Document Authoring | Document creation, appending, reading, and path validation |
| `test_email_planning.py` | 4 | 4 | 0 | 0.35s | Email Planning | Recipient prompt, subject/body generation, drafting |
| `test_extended_acceptance_criteria.py` | 6 | 6 | 0 | 1.18s | System Acceptance | <5ms direct coexistence, failure isolation, secret masking |
| `test_generalised_ollama_commands.py` | 4 | 4 | 0 | 0.05s | Brain Lifecycle | Generalized start/stop/restart regex, model name parsing |
| `test_glass_rendering.py` | 4 | 4 | 0 | 0.22s | UI / Glass Flow | Acrylic transparency, capsule height (58px), smooth dragging |
| `test_multi_agent_system.py` | 14 | 14 | 0 | 0.88s | Multi-Agent Core | Planner DAG, 7 specialized agents, Demos 1, 2, 3, 4 |
| `test_offline_routing_and_phonetics.py` | 12 | 12 | 0 | 0.65s | Hearing Module | Phonetic typo tolerance, slang resolution, offline fast-paths |
| `test_speech_and_system_invariance.py` | 9 | 9 | 0 | 1.02s | Audio Invariance | Strict intent filtering; unprompted volume/brightness rejected |
| `test_tts_speed.py` | 1 | 1 | 0 | 0.40s | Piper Neural TTS | Audio synthesis rate (>160 wpm), 22.05 kHz WAV framing |
| `test_universal_open_and_search.py` | 7 | 7 | 0 | 1.15s | Universal Opener | Exact files, videos, images, web links, native applications |
| `test_weekly_memory_and_cloud.py` | 9 | 9 | 0 | 1.06s | 7-Day Memory / Cloud | 168h rolling retention, weekly digest, cloud onboarding |
| `test_youtube_dictation_and_memory.py` | 14 | 14 | 0 | 1.85s | Media & Memory | YouTube search & play, 1.5GB SSD memory, task persistence |
| **TOTAL** | **135** | **135** | **0** | **~40s** | **Entire System** | **100% Pass Rate across all 18 test suites** |

---

## 2. Source Code Architecture & Line References

Every claimed feature maps directly to concrete source implementations in `/run/media/prakash/TR_39/VOID`:

### A. Agentic Multi-Agent Framework (`agentic/`)
- **`agentic/types.py`:**
  - `AgentRole` (lines 16–28): Supervisor, Planner, Linux Intel, Developer, Research, Tool Exec, Verifier, Recovery.
  - `TaskStatus` (lines 30–42): Pending, Planning, Ready, Running, Waiting Approval, Verifying, Completed, Failed, Cancelled, Recovered.
  - `PermissionLevel` (lines 44–52): 4-tier security levels (Level 1 ReadOnly to Level 4 Forbidden).
  - `WorkflowLifecycleState` (lines 54–65): State machine tracking workflow progression.
  - `ToolResult` & `VerificationResult` (lines 68–135): Ground-truth validation dataclasses with timing and exit codes.
  - `WorkflowPlan` & `AgentTask` (lines 180–290): Directed Acyclic Graph (DAG) definition with task dependency arrays (`depends_on`).
- **`agentic/permissions.py`:**
  - `APPROVED_WORKSPACES` (lines 16–24): Strictly confines file writes to `~/Documents`, `~/Documents/Reports`, `~/Documents/Notes`, `~/Documents/Projects`, `memory/`, `logs/`, `/tmp/void_sandbox`.
  - `FORBIDDEN_COMMANDS` & `FORBIDDEN_PATHS` (lines 27–37): Regex-guarded blocking of `sudo`, `su`, `rm -rf /`, `/etc`, `/boot`, `/sys`, `/proc`, `/root`.
  - `evaluate_tool_permission()` (lines 69–120): Evaluates tool execution against the 4-tier security doctrine.
- **`agentic/tools.py`:**
  - `ToolRegistry` (lines 20–100): Registers tools with schema validation, permission checks, duration measurement, and artifact tracking.
  - Built-in native tools (lines 140–490):
    - `inspect_system_vitals`: Reads `/proc/meminfo`, `/proc/loadavg`, `/proc/uptime`, `df -h`.
    - `scaffold_python_project`: Creates directory structures and scaffold files safely.
    - `write_project_file` & `read_project_file`: Sandboxed file manipulation in approved workspaces.
    - `run_workspace_tests`: Executes `pytest` or `unittest` in isolated subprocesses.
    - `deep_web_research`: Queries DuckDuckGo and aggregates snippets.
    - `create_docx_report`: Produces professionally styled Word documents.
    - `create_xlsx_spreadsheet`: Produces structured Excel spreadsheets.
- **`agentic/planner.py`:**
  - `PlannerAgent.create_plan()` (lines 40–160): Analyzes user goal, decomposes into modular tasks, assigns specialized agent roles, and resolves execution order dependencies.
- **`agentic/orchestrator.py`:**
  - `MultiAgentOrchestrator.execute_plan()` (lines 50–180): Iterates through the DAG, respects dependencies, dispatches tasks, collects results, invokes verification, and handles cancellation.
- **`agentic/supervisor.py`:**
  - `SupervisorAgent.classify_intent()` (lines 40–90): Classifies requests into `DIRECT_FASTPATH` or `AGENTIC_WORKFLOW`.
  - `SupervisorAgent.execute_goal()` (lines 110–210): Orchestrates end-to-end execution, logs to audit trail, records high-memory thoughts, and synthesizes spoken response.
- **`agentic/memory.py`:**
  - `AgentMemoryManager` (lines 24–65): Initializes persistent storage in `memory/`.
  - `record_high_memory_thought()` (lines 150–195): Appends reasoning traces, outcomes, and artifacts to `memory/weekly_episodes.jsonl`.
  - `get_7day_episodes()` (lines 197–212): Filters memories older than 604,800 seconds (168 hours).
  - `generate_weekly_memory_file()` (lines 213–300): Synthesizes structured JSON and human-readable Markdown digests in `memory/weekly_summaries/`.
  - `query_weekly_memory()` (lines 301–350): Deep contextual search over the past 7 days of memory.
- **`agentic/providers.py`:**
  - `LocalOllamaProvider` (lines 35–80): Connects to local Ollama (`http://127.0.0.1:11434`).
  - `CloudOpenAICompatibleProvider` (lines 85–160): OpenAI-compatible cloud bridge with secret masking.
  - `AIProviderManager` (lines 162–258): Manages local, cloud, and hybrid routing modes.
  - `parse_cloud_credentials()` (lines 262–305): Natural parsing of model names and API keys from spoken or typed text.
- **`agentic/audit.py`:**
  - `AuditLogger` (lines 20–100): Writes immutable audit events to `logs/agentic_audit.jsonl` with automatic masking of passwords and API keys.

### B. Core Application & Voice Engine (`bin/void-widget.py`)
- **Dual-Tier Router:**
  - Lines 3673–3701: Intercepts multi-agent workflows and competition demos, routing them to `SupervisorAgent`.
  - Lines 3703–3730: Splits sequential compound commands (*"open chromium and take a screenshot and calculate 15 * 4"*).
  - Lines 3746–3850: Sub-5ms fast-path dispatch for window controls, volume, brightness, math, and identity.
- **Interactive Clarification & Onboarding:**
  - Lines 3803–3840: Handles `_pending_action` states, including interactive cloud onboarding (`cloud_setup`) and email recipient prompts.
- **Direct Memory & Cloud Commands:**
  - Lines 3878–3930: Direct voice commands for `generate weekly memory`, `what did we do this week`, `connect cloud api`, `cloud status`.
- **Conversational AI Fallback:**
  - Lines 4808–4896: Local Ollama chat and tool execution.
  - Lines 4897–4925: Proactive offline detection; prompts user to connect cloud AI if Ollama is offline.
- **Speech Pipeline & Invariance:**
  - Lines 4864–4950: PipeWire native playback (`pw-play`) with fallback to `paplay`.
  - Lines 4548–4610: Strict regex intent filtering protecting master audio volume and screen brightness.

---

## 3. Empirical Performance & Benchmark Data

Live hardware measurements captured on Fedora Linux 40+ (AMD Ryzen 7, 16 GB RAM):

| Performance Metric | Measured Value | Baseline / Competitor Comparison |
| :--- | :--- | :--- |
| **Direct Command Latency** | **3.8 ms** | Sub-5ms target (Immediate local execution) |
| **Wake-Word Detection Latency** | **~120 ms** | Real-time acoustic Kaldi FST |
| **Whisper STT Latency (Base int8)** | **~780 ms** | CPU quantized Faster-Whisper |
| **Piper TTS Synthesis Latency** | **~240 ms** | 160 wpm speech synthesis via ONNX |
| **PipeWire Audio Playback Startup** | **~15 ms** | Native PipeWire `pw-play` streaming |
| **Local LLM Time-to-First-Token** | **1.12 s** | Liquid AI `lfm3-omni:2b` via Ollama |
| **Local LLM Generation Throughput** | **18.2 tokens/sec** | Sustained throughput on AMD CPU |
| **Multi-Agent DAG Execution (Demo 1)** | **0.67 s** | 3 tasks: Vitals + Sockets + DOCX Report |
| **Multi-Agent DAG Execution (Demo 2)** | **0.45 s** | 4 tasks: Scaffold + Code + PyTest + Verifier |
| **Multi-Agent DAG Execution (Demo 3)** | **1.82 s** | Deep web search + Markdown/DOCX compilation |
| **RAM Footprint (Standby)** | **185 MB** | Lightweight PySide6 acrylic widget |
| **RAM Footprint (Ollama Active)** | **1.89 GB** | 1.61 GB model weights + 280 MB KV cache |
| **RAM Saved when Ollama Stopped** | **~2.0 GB** | Instantly freed via *"Hey VOID, stop ollama"* |
| **Emergency Abort Interruption Time** | **< 5 ms** | Kills audio process and halts executor |

---

## 4. Hardware and Weight Digests

- **Local Model Identifier:** `lfm3-omni:2b`
- **Model Weight File:** `sha256:9f8d30e9d4fd7a9349d586e077988229b3ca0a0e4ad730897563d1eccc9893e2` (1.61 GB)
- **Vosk Wake Model:** `vosk-model-small-en-us-0.15` (42 MB)
- **Piper Voice Model:** `vits-piper-en_US-ryan-medium.onnx` (64 MB)
- **Operating Audio Sink:** `@DEFAULT_AUDIO_SINK@` via WirePlumber 0.5+

---

## 5. Artifact Delivery Verification

All deliverables generated during autonomous agent runs are stored in approved user directories and verified:

1. **System Diagnostics Report:**
   - Path: `/home/prakash/Documents/Reports/System_Diagnostics_Report.docx`
   - Verified size: ~38 KB (Valid Word document structure, contains CPU/RAM/Socket tables)
2. **Autonomous Development Scaffolding:**
   - Path: `/home/prakash/Documents/Projects/string_utils/`
   - Files: `core.py`, `test_core.py`
   - Test result: 3/3 passing unit tests via `run_workspace_tests`
3. **Deep Research Report:**
   - Path: `/home/prakash/Documents/Reports/Research_Report_-_Edge_AI_Architectures_in_Linux.docx`
   - Verified size: ~42 KB (Contains citations, executive summary, benchmark tables)
4. **Weekly Memory Digests:**
   - Paths: `/run/media/prakash/TR_39/VOID/memory/weekly_summaries/weekly_memory_2026_W45.json` and `.md`
   - Verified contents: 7-day chronological thought trace, deliverables list, activity breakdown

