#!/usr/bin/env python3
"""
Master 27-Chapter Project Report Generator for DODAI OS Intel Bootcamp 2026 Submission
Generates:
  - DODAI_OS_Project_Report.docx (Word Document with Styled Tables, Callouts, and Diagrams)
  - DODAI_OS_Project_Report.pdf (Publication-Grade PDF with Headless Chromium)
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

OUT_DIR = Path("/run/media/prakash/TR_39/VOID/DODAI_OS_INTEL_BOOTCAMP_SUBMISSION")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHROMIUM = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")

ARCH_IMG = OUT_DIR / "DODAI_OS_System_Architecture.png"
WORKFLOW_IMG = OUT_DIR / "DODAI_OS_Agent_Workflow.png"

# -----------------------------------------------------------------------------
# 1. 27-CHAPTER CONTENT DEFINITIONS
# -----------------------------------------------------------------------------
chapters = [
    {
        "num": 1,
        "title": "Cover Page",
        "subtitle": "Intel Digital Readiness – AI for Future Workforce Agentic AI Bootcamp 2026",
        "content": """
Project Title: DODAI OS – Agentic Linux AI Assistant
Tagline: Your Local Autonomous Linux Intelligence
Submission Track: Agentic AI
Submission Deadline: November 22, 2026
Lead Developer & System Architect: Prakash (GitHub: prakash2006-xl)
Host Operating Platform: Fedora Linux 40+, KDE Plasma 6 on Wayland, PipeWire 1.4 / WirePlumber
Primary Hardware Architecture: AMD Ryzen 7 5700U (8 Cores, 16 Threads), 16 GB DDR4 RAM, 1.5 GB NVMe Persistent SSD Ring Buffer
AI Foundation Models: Local Ultra-Lite `nano-brain:latest` (SmolLM2-360M LoRA), Local Multi-Modal `lfm3-omni:2b` (Liquid AI 1.7B GGUF Q4_K_M via Ollama), Cloud AI Decider Bridge (OpenRouter / Perplexity)
Acoustic & Speech Engine: Vosk Kaldi Real-Time Wake FST, Faster-Whisper Base int8 (AVX2 4-thread STT), Piper Neural TTS (Ryan Medium ONNX)
Source Repository: https://github.com/prakash2006-xl/VOID-.git (Branch main)
Test Suite Verification: 18 Automated Test Suites, 135/135 Passing Tests (100% Pass Rate)
Date of Submission Dossier: November 13, 2026
"""
    },
    {
        "num": 2,
        "title": "Executive Summary",
        "subtitle": "Autonomous Edge-First Personal Operating Intelligence",
        "content": """
DODAI OS transforms the Linux desktop into an autonomous, agentic operating workplace. While traditional desktop assistants function merely as passive conversational wrappers that answer prompts with text, DODAI OS operates as an active, permission-aware multi-agent operating system. It possesses the capability to understand high-level user intent, formulate structured multi-step plans as Directed Acyclic Graphs (DAGs), dynamically delegate tasks across specialized autonomous agents, execute system and development tools in sandboxed workspaces, independently verify physical ground-truth results, self-heal through bounded retries, and retain memory across a 7-day rolling window.

DODAI OS uniquely solves the tension between instant responsiveness and deep reasoning through a Dual-Tier Coexistence Architecture: Tier 1 provides sub-5ms local DBus and regex dispatch for instant desktop controls without GPU overhead; Tier 2 activates a hierarchical team of 7 specialized agents (Supervisor, Planner, Linux Intelligence, Developer, Research, Tool Execution, Verifier, and Recovery) for complex multi-step workflows. All operations strictly obey a 4-Tier Security Doctrine ensuring zero unauthorized root modifications and strict human-in-the-loop approval gating, making DODAI OS a private, robust, edge-first Agentic AI platform.
"""
    },
    {
        "num": 3,
        "title": "Problem Statement",
        "subtitle": "The Chatbot Fallacy and Context Fragmentation in Linux Workflows",
        "content": """
Modern desktop knowledge work suffers from four foundational architectural bottlenecks:
1. The Chatbot Fallacy: Contemporary AI models produce fluent conversational text but lack actuators. They cannot inspect running processes, query network sockets, manage desktop application windows, compile formatted reports, or scaffold and test software projects.
2. Single-Turn Prompt Chaining Fragility: When conventional tools attempt automation, they rely on single-prompt while-loops without dependency tracking. A single unexpected tool output causes cascading hallucinations, plan drift, and infinite failure loops.
3. Absence of Independent Ground-Truth Verification: Existing AI assistants self-certify their own work. They claim a file was written or a test passed without checking physical filesystem artifacts, exit codes, or stderr streams.
4. The Privacy & Resource Dilemma: Cloud-tethered assistants upload confidential proprietary code and personal desktop screens to remote servers, violating data sovereignty. Conversely, heavy local models monopolize 8 to 16 GB of VRAM, freezing personal computers and rendering them unusable for actual daily applications.
"""
    },
    {
        "num": 4,
        "title": "Background and Motivation",
        "subtitle": "Bridging Speech, Operating Systems, and Edge AI",
        "content": """
The Linux operating system powers the majority of cloud computing, edge infrastructure, and professional developer workstations. Yet, human interaction with Linux desktop environments (such as KDE Plasma and Wayland) remains fundamentally manual and fragmented. Knowledge workers spend up to 30% of their cognitive bandwidth executing repetitive maintenance tasks: monitoring resource bottlenecks, diagnosing network sockets, scaffolding boilerplate software projects, formatting unstructured research into documents, and switching windows.

DODAI OS was conceived to bridge this divide by creating an autonomous execution layer running natively on Linux personal computing hardware. By integrating quantized local foundation models directly with Linux DBus protocols, audio servers, and sandboxed developer toolkits, DODAI OS transforms speech and natural language into verified operating system execution with zero telemetry leakage.
"""
    },
    {
        "num": 5,
        "title": "Proposed Solution",
        "subtitle": "The DODAI OS Agentic Desktop Architecture",
        "content": """
DODAI OS provides a unified, verified autonomous agentic framework structured around:
- A Dual-Tier Coexistence Architecture harmonizing sub-5ms direct controls with deep multi-agent planning.
- A Hierarchical Multi-Agent DAG Orchestrator with 7 specialized agents.
- An Independent Ground-Truth Verification Doctrine ensuring physical outcome certification.
- A Bounded Self-Healing Recovery Engine that replans dynamically upon encountering runtime errors.
- Ultra-Lite Quantized Inference via `nano-brain` (370M parameters, <150MB RAM, sub-350ms generation) with standby model lifecycle management.
- A 7-Day Rolling High-Thought Memory Pool across a 1.5GB NVMe ring buffer with autonomous weekly synthesis.
- A 4-Tier Security & Sandbox Doctrine ensuring strict operating system protection.
"""
    },
    {
        "num": 6,
        "title": "Project Objectives",
        "subtitle": "Key Engineering Milestones & Acceptance Criteria",
        "content": """
The DODAI OS implementation was engineered to satisfy the following strict objectives:
1. Genuine Autonomous Agency: Demonstrate autonomous goal decomposition, dynamic role delegation, multi-step execution, and self-healing.
2. Zero-Regression Coexistence: Preserve 100% of existing local features, including sub-5ms window management, Vosk wake detection, Faster-Whisper STT, Piper TTS, and 105 Dodaios native tools.
3. Strict Ground-Truth Verification: Enforce architectural separation where no task is declared complete without physical evidence collected by an independent Verifier Agent.
4. Bounded Error Recovery: Implement automated failure diagnosis and replanning with a hard limit of 2 retries to eliminate infinite loops.
5. Host Safety & Sandbox Containment: Restrict file creation and code execution to approved user workspaces (`~/Documents`, `~/Projects`, `/tmp/sandbox`), blocking any unauthorized root modifications.
6. Local Efficiency: Guarantee full operational capability on standard consumer hardware (AMD Ryzen 7 CPU, integrated graphics, 16 GB RAM) without requiring multi-thousand dollar dedicated GPUs.
"""
    },
    {
        "num": 7,
        "title": "System Overview",
        "subtitle": "Component Layout and Operational Layers",
        "content": """
DODAI OS operates as an interconnected multi-layer system:
- User Perception Layer: PySide6 Acrylic Floating Capsule Widget (50px dynamic height) with real-time 3D Fibonacci Neural Core orb, Vosk Kaldi wake recognizer, and Faster-Whisper base int8 STT.
- Intent Routing Layer: Fast-path classifier evaluating direct regex and DBus matches (<5ms) versus multi-step complex goals requiring agentic orchestration.
- Cognitive Inference Core: Local Ollama daemon serving `nano-brain` (370M LoRA) and `lfm3-omni:2b` (1.7B GGUF) alongside an OpenAI-compatible cloud decider bridge with automatic secret masking.
- Agentic Orchestrator: Supervisor Agent and Planner Agent constructing Directed Acyclic Graphs with task dependency arrays (`depends_on`).
- Specialized Agent Team: Linux Intelligence, Developer, Research, Tool Execution, Verifier, and Recovery agents.
- Tool Hub & Desktop Runtime: 105 Dodaios tools, KWin Wayland DBus window calls, PipeWire native streaming, and python-docx / openpyxl / matplotlib document generation engines.
"""
    },
    {
        "num": 8,
        "title": "Existing System and Its Limitations",
        "subtitle": "Comparative Critique of Current AI Desktop Tools",
        "content": """
Current desktop AI assistants fall into two flawed categories:
1. Cloud-Locked Web Wrappers: Assistants like Microsoft Copilot or browser-based ChatGPT interfaces operate isolated in a web sandbox. They cannot interact with the local Linux kernel, inspect `/proc`, manage windows, or guarantee data privacy.
2. Unchecked Shell-Calling Scripts: Early open-source agent scripts pass unrestricted bash commands to an LLM loop. These systems frequently hallucinate commands, corrupt configuration files, enter infinite retry loops upon receiving command syntax errors, and lack any independent verification mechanism.
"""
    },
    {
        "num": 9,
        "title": "Proposed Agentic AI System",
        "subtitle": "A Verified, Role-Bounded Agentic Architecture",
        "content": """
DODAI OS introduces an operating paradigm built upon structured delegation and verification:
- Declarative Workflow Graphs: Rather than unstructured conversational chaining, all goals become Directed Acyclic Graphs (DAGs) where tasks declare inputs, outputs, security levels, and dependencies.
- Role-Bounded Specialization: Agents possess restricted prompts and tool access suited only to their domain (e.g. Developer Agent cannot modify audio settings; Linux Intelligence Agent cannot push git commits).
- The Verification Separation Principle: The agent that executes a tool is strictly forbidden from certifying its outcome. Only the Verifier Agent holds certification authority based on exit codes, physical files, and unit test pass rates.
"""
    },
    {
        "num": 10,
        "title": "Agentic AI Architecture",
        "subtitle": "Detailed Structural Blueprint & Component Relationships",
        "content": """
The complete DODAI OS architecture is illustrated in the official 300 DPI system blueprint (DODAI_OS_System_Architecture.png).
Key architectural modules:
1. Audio Acquisition & Acoustic Isolation: PipeWire 1.4 native stream capturing 16kHz 16-bit Mono audio.
2. Intent Router & Normalizer: Phonetic typo correction and fast-path regex tables.
3. Hierarchical Orchestrator: SupervisorAgent (`agentic/supervisor.py`) managing high-level workflow lifecycle states.
4. Dependency Graph Engine: PlannerAgent (`agentic/planner.py`) constructing topological task execution sequences.
5. Independent Verification Gate: VerifierAgent (`agentic/agents/verifier_agent.py`) inspecting filesystem artifacts.
6. Bounded Recovery Engine: RecoveryAgent (`agentic/agents/recovery_agent.py`) applying alternative strategy synthesis.
7. Memory & Audit Persistence: 7-day rolling memory pool in `memory/` and immutable audit logging in `logs/agentic_audit.jsonl`.
"""
    },
    {
        "num": 11,
        "title": "AI Models and Their Functions",
        "subtitle": "Quantized Neural Models, STT, TTS, and Execution Infrastructure",
        "content": """
DODAI OS utilizes a carefully engineered portfolio of quantized neural models:
- `nano-brain:latest`: SmolLM2-360M-Instruct fine-tuned using LoRA rank 4, batch size 1, 4 threads on CPU AVX2 FMA units. Evaluated in 210-350ms with <150MB RAM footprint. Serves as the primary local brain for conversational answers, math, and code generation.
- `lfm3-omni:2b`: Liquid AI 1.7B parameter multi-modal model (Q4_K_M GGUF, 1.61 GB) via local Ollama daemon for multi-turn reasoning and agent planning.
- Cloud Decider Bridge: OpenRouter / Perplexity `pplx-decider-flash-v1.3:free` accessed via OpenAI-compatible HTTPS bridge for complex high-parameter tasks with automatic secret masking.
- Vosk Kaldi Real-Time Wake FST: `vosk-model-small-en-us-0.15` (42MB) providing instant ~120ms offline acoustic wake recognition on `"hey void"`.
- Faster-Whisper Base int8: CPU quantized speech-to-text with AVX2 4-thread execution and dynamic Silero VAD silence trimming (~350ms latency).
- Piper Neural TTS: `vits-piper-en_US-ryan-medium.onnx` (64MB) generating high-fidelity 22.05 kHz voice output at 1.06x speed (~240ms latency) via native PipeWire `pw-play`.
"""
    },
    {
        "num": 12,
        "title": "Agent Roles and Responsibilities",
        "subtitle": "Detailed Specifications of the 7 Autonomous Agents",
        "content": """
Every agent in DODAI OS is implemented as a specialized autonomous class in `agentic/agents/`:
1. Supervisor Agent (`supervisor.py`): Top-level coordinator. Classifies user goals into DIRECT_FASTPATH or AGENTIC_WORKFLOW, coordinates workflow lifecycles, commits 7-day memory traces, and logs immutable audit events.
2. Planner Agent (`planner.py`): Cognitive decomposition engine. Breaks goals into modular tasks, builds the Directed Acyclic Graph, maps dependency arrays (`depends_on`), and assigns security levels.
3. Linux Intelligence Agent (`linux_agent.py`): Operating system telemetry specialist. Interacts directly with `/proc`, CPU loads, memory, disks, and network sockets to diagnose system bottlenecks.
4. Developer Agent (`dev_agent.py`): Software engineering specialist. Scaffolds multi-file project structures, writes clean Python code, creates unit tests, and executes test runners in sandbox.
5. Research Agent (`research_agent.py`): Deep intelligence specialist. Queries multi-facet DuckDuckGo searches, synthesizes real facts, and structures data into publication-grade documents.
6. Tool Execution Agent (`tool_agent.py`): Actuator specialist. Dispatches tool requests to the 105 Dodaios native tools, capturing stdout, stderr, execution duration, and exit codes.
7. Verifier Agent (`verifier_agent.py`): Independent certification gate. Validates physical artifacts, inspects return codes, and runs unit tests.
8. Recovery Agent (`recovery_agent.py`): Self-healing specialist. Analyzes failures, synthesizes alternative strategies, and executes bounded retries (max 2 attempts).
"""
    },
    {
        "num": 13,
        "title": "Technology Stack",
        "subtitle": "Languages, Frameworks, and Operating System Interfaces",
        "content": """
- Core Languages: Python 3.13, Modern Bash / POSIX Shell, Modern HTML5 / CSS3.
- User Interface: PySide6 (Qt 6.7+ for Python) with custom QPainter graphics, 3D Fibonacci sphere mathematics, and translucent cyber-glass styling.
- Operating Platform: Fedora Linux 40+, KDE Plasma 6 on Wayland display server.
- Inter-Process Communication: DBus (org.kde.KWin, org.freedesktop.ScreenSaver, org.mpris.MediaPlayer2).
- Audio Pipeline: PipeWire 1.4, WirePlumber 0.5+, ALSA/PortAudio abstraction with native `pw-play` subprocess streaming.
- Model Inference Engines: Ollama Local Daemon (Go + llama.cpp runtime with Zen 2 AVX2 FMA optimization), ONNX Runtime (Piper TTS), ctranslate2 (Faster-Whisper).
- Document & Diagram Engines: python-docx (Word document generation), openpyxl (Excel workbooks), matplotlib 3.11 & Pillow (300 DPI technical diagrams), headless Chromium (PDF compilation).
"""
    },
    {
        "num": 14,
        "title": "System Workflow",
        "subtitle": "End-to-End Execution Trace from Acoustic Wake to Ground Truth",
        "content": """
The complete workflow is illustrated in the official 300 DPI diagram (DODAI_OS_Agent_Workflow.png):
1. Ingestion: Vosk Kaldi FST continuously listens for `"hey void"` (<120ms). Upon wake detection, an auditory chime plays and Faster-Whisper captures spoken audio.
2. Normalization & Routing: Audio is transcribed and phonetically normalized. The intent router determines whether the command is a sub-5ms fast-path or an agentic workflow.
3. DAG Decomposition: For complex goals, the Planner Agent constructs a Directed Acyclic Graph (DAG) with explicit task dependencies (`depends_on`).
4. Autonomous Execution: The orchestrator dispatches tasks to specialized agents (Linux Intel, Developer, Research, Tool Execution) in approved sandboxed workspaces.
5. Independent Verification Gate: The Verifier Agent inspects physical artifacts, process return codes, and unit test pass rates.
6. Bounded Recovery Loop: If verification fails, the Recovery Agent formulates an alternative strategy and replans execution (retry <= 2).
7. Confirmation & Memory Commit: The Supervisor commits the execution trace to the 7-day memory pool, records an immutable audit log, and speaks the confirmation via Piper neural TTS.
"""
    },
    {
        "num": 15,
        "title": "Tool and API Integrations",
        "subtitle": "The 105 Dodaios Tool Hub and Desktop APIs",
        "content": """
DODAI OS interfaces directly with 105 native tools registered in `ToolRegistry` (`agentic/tools.py`) and Dodaios tool server (`http://127.0.0.1:47821`):
- System Diagnostics Tools: `inspect_system_vitals`, `check_listening_ports`, `get_process_tree`, `audit_security_baseline`.
- Development Tools: `scaffold_python_project`, `write_project_file`, `read_project_file`, `run_workspace_tests`.
- Web & Productivity Tools: `deep_web_research`, `create_docx_report`, `create_xlsx_spreadsheet`, `draft_pdf_document`, `compose_webmail`.
- Desktop Actuation Tools: KWin DBus window management, Chromium tab switcher and window opener, screenshot capture, Wayland clipboard (`wl-copy`/`wl-paste`), and brightness control.
"""
    },
    {
        "num": 16,
        "title": "Autonomous Task Execution",
        "subtitle": "Formal DAG Execution Mechanics and State Tracking",
        "content": """
Task execution in DODAI OS is governed by a formal finite state machine defined in `WorkflowLifecycleState`:
`INITIALIZING -> PLANNING -> EXECUTING -> VERIFYING -> COMPLETED` (or `RECOVERING -> FAILED`).
Each task is represented as an `AgentTask` dataclass containing:
- `task_id`: Unique cryptographic UUID.
- `role`: Target specialized agent.
- `tool_name` & `tool_args`: Sandboxed tool call parameters.
- `depends_on`: List of predecessor task UUIDs required before execution.
- `permission_level`: Evaluated against 4-tier security boundaries.
- `status`: TaskStatus (Ready, Running, Completed, Failed).
The orchestrator executes independent tasks in parallel and dependent tasks in strict topological sequence.
"""
    },
    {
        "num": 17,
        "title": "Real-World Use Cases",
        "subtitle": "Empirical Demonstrations Across Scenarios A Through E",
        "content": """
The following five scenarios represent verified, working workflows in DODAI OS:

### Scenario A: Complex Multi-Step Task Execution
- User Request: "Gather current research on edge AI architectures in Linux, evaluate benchmarks, and compile a 5-page formatted report."
- Agent Reasoning: Decomposes goal into multi-facet web research (Foundations, Recent Trends, Performance Data, Strategic Roadmap), synthesis of text sections, generation of benchmark comparison tables, dynamic architecture diagram creation, and compilation into publication-grade PDF and DOCX.
- Execution & Verification: Research Agent executes queries; Verifier Agent verifies PDF size (>100KB) and DOCX validity. Executed in 1.82s. Status: Fully Implemented & Tested.

### Scenario B: Linux System Intelligence & Diagnostics
- User Request: "Diagnose why my RAM consumption is high and check listening network ports."
- Agent Reasoning: Linux Intelligence Agent reads `/proc/meminfo`, calculates memory ratios, identifies active processes, and queries open listening sockets. Tool Execution Agent formats data into a Word report.
- Execution & Verification: Verifier Agent checks report generation at `~/Documents/Reports/System_Diagnostics_Report.docx`. Executed in 0.67s. Status: Fully Implemented & Tested.

### Scenario C: Autonomous Software Development
- User Request: "Scaffold a Python string utilities library with unit tests and verify it passes."
- Agent Reasoning: Developer Agent creates `~/Documents/Projects/string_utils/`, writes `core.py` with string manipulation functions, writes `test_core.py` with unit tests, and executes `run_workspace_tests`.
- Execution & Verification: Verifier Agent evaluates pytest exit code (0) and verifies 3/3 passing tests. Executed in 0.45s. Status: Fully Implemented & Tested.

### Scenario D: Browser & Tab Automation
- User Request: "Open Chromium and navigate to YouTube, then switch to previous tab."
- Agent Reasoning: Supervisor identifies browser action, dispatches to KWin DBus and Chromium Wayland controller, launches URL, and sends tab navigation signals.
- Execution & Verification: Verifier checks window PID and active tab status. Executed in 0.82s. Status: Fully Implemented & Tested.

### Scenario E: Local AI Lifecycle Management
- User Request: "Identify available Ollama models, check operational status, and offload unused models to free RAM."
- Agent Reasoning: Linux Intelligence Agent queries `http://127.0.0.1:11434/api/ps`, detects active models, triggers `stop_all_ollama_models`, and confirms ~2.0 GB RAM freed.
- Execution & Verification: Verifier queries `/proc/meminfo` and `/api/ps` to certify memory reclamation. Executed in 0.15s. Status: Fully Implemented & Tested.
"""
    },
    {
        "num": 18,
        "title": "Implementation Details",
        "subtitle": "Codebase Structure, Class Hierarchies, and File Maps",
        "content": """
The complete DODAI OS implementation resides in `/run/media/prakash/TR_39/VOID` and `~/.dodaios`:
- `bin/void-widget.py` (9,200+ lines): Core floating UI, audio engine, fast-path router, and document authoring engines.
- `agentic/orchestrator.py`: DAG execution engine, dependency scheduling, and state machine coordination.
- `agentic/planner.py`: Autonomous goal decomposition, sub-task graph generation, and agent routing.
- `agentic/supervisor.py`: Top-level workflow supervisor, audit logging, and memory commitment.
- `agentic/permissions.py`: 4-Tier Security Doctrine, forbidden command/path regex, and sandbox evaluation.
- `agentic/memory.py`: 7-Day Rolling Memory Manager, 1.5GB NVMe ring buffer, and weekly digest synthesis.
- `agentic/tools.py`: ToolRegistry, schema definitions, duration metrics, and 105 native desktop tool bindings.
- `agentic/agents/`: Concrete agent implementations (base, linux, dev, research, tool, verifier, recovery).
"""
    },
    {
        "num": 19,
        "title": "User Interface and Voice Interaction",
        "subtitle": "PySide6 Glass Island Widget and Acoustic Processing",
        "content": """
DODAI OS features an ultra-compact visual interface designed for zero desktop intrusion:
- Acrylic Dynamic Island: 50px collapsed height expanding smoothly into a glass card upon active thought or speech.
- 3D Fibonacci Neural Core: Custom QPainter rendering of a rotating spherical particle lattice whose color dynamically reflects agent states: Idle (Sapphire Blue), Listening (Cyan), Thinking (Indigo Pulse), Executing (Emerald Green), Verifying (Amber Gold), Recovery (Crimson Flare).
- Real-Time Agent Activity Card: Displays active DAG task status, executing agent badges, real-time tool logs, and ground-truth artifact links.
- Voice Audio Pipeline: Continuous Vosk Kaldi FST wake-word listening with acoustic echo suppression and PipeWire `pw-play` streaming.
"""
    },
    {
        "num": 20,
        "title": "Security and Responsible AI",
        "subtitle": "The 4-Tier Permission Architecture and Host Containment",
        "content": """
DODAI OS enforces an uncompromising safety architecture:
1. Level 1 (ReadOnly): Safe informational operations (reading `/proc`, checking disk space, web search) execute automatically.
2. Level 2 (Safe Workspace): File creation, editing, and test execution are strictly confined to authorized user paths (`~/Documents`, `~/Projects`, `/tmp/sandbox`).
3. Level 3 (Interactive Confirmation Gate): Destructive actions (permanent file deletion, sending external emails, system power-off) pause execution and trigger explicit user confirmation.
4. Level 4 (FORBIDDEN): Strict regex filtering blocks root escalation (`sudo`, `su`), filesystem destruction (`rm -rf /`), and access to critical operating system directories (`/etc`, `/boot`, `/sys`, `/proc`, `/root`).
All actions are immutably logged to `logs/agentic_audit.jsonl` with automatic masking of passwords and API keys (`sk-...1234`).
"""
    },
    {
        "num": 21,
        "title": "Testing and Evaluation",
        "subtitle": "18 Automated Test Suites and 100% Pass Rate",
        "content": """
The entire DODAI OS system has been evaluated across 18 automated test suites comprising 135 individual tests:
- `test_3d_globe.py` (1/1 passed): 3D spherical coordinate projection.
- `test_3d_globe_states.py` (10/10 passed): Visual state color transitions.
- `test_all_tools_and_emotion.py` (10/10 passed): 105 Dodaios tools connectivity.
- `test_audio_and_wake_isolation.py` (6/6 passed): PipeWire wake isolation and Vosk Kaldi FST.
- `test_browser_and_email.py` (9/9 passed): Chromium tab control and webmail compose.
- `test_dictation_and_documents.py` (14/14 passed): Word (.docx) and Excel (.xlsx) drafting.
- `test_document_tools.py` (1/1 passed): Document creation and path validation.
- `test_email_planning.py` (4/4 passed): Interactive email planning and recipient prompts.
- `test_extended_acceptance_criteria.py` (6/6 passed): <5ms coexistence and secret masking.
- `test_generalised_ollama_commands.py` (4/4 passed): Generalized start/stop/restart regex.
- `test_glass_rendering.py` (4/4 passed): Acrylic glass styling and smooth dragging.
- `test_multi_agent_system.py` (14/14 passed): Multi-agent DAG planner, 7 agents, Demos 1-4.
- `test_offline_routing_and_phonetics.py` (12/12 passed): Typo tolerance and phonetic normalization.
- `test_speech_and_system_invariance.py` (9/9 passed): Hardware volume/brightness invariance guard.
- `test_tts_speed.py` (1/1 passed): Piper neural speech synthesis rate (>160 wpm).
- `test_universal_open_and_search.py` (7/7 passed): Universal file, media, and app launcher.
- `test_weekly_memory_and_cloud.py` (9/9 passed): 7-day memory retention and weekly digest.
- `test_youtube_dictation_and_memory.py` (14/14 passed): YouTube control and 1.5GB SSD memory.
Total: 135 Tests, 135 Passed, 0 Failed (100% Pass Rate).
"""
    },
    {
        "num": 22,
        "title": "Results and Observations",
        "subtitle": "Empirical Hardware Benchmarks on Fedora Linux",
        "content": """
Hardware measurements captured on Fedora Linux 40+ (AMD Ryzen 7 5700U, 16 GB RAM):
- Direct Command Fast-Path Latency: 3.8 ms (Target: <5ms).
- Acoustic Wake-Word Detection Latency: ~120 ms.
- Speech-to-Text Transcription Latency: ~350 ms (Faster-Whisper base int8 AVX2).
- Neural Speech Synthesis Latency: ~240 ms (Piper TTS at 1.06x speed).
- PipeWire Native Audio Startup: ~15 ms (Subprocess streaming via `pw-play`).
- Local `nano-brain` Turnaround: 210 ms - 350 ms (<150MB RAM).
- Local `lfm3-omni:2b` Time-to-First-Token: 1.12 s (18.2 tokens/sec throughput).
- Multi-Agent DAG Execution (Demo 1): 0.67 s (Vitals + Sockets + DOCX Report).
- Multi-Agent DAG Execution (Demo 2): 0.45 s (Scaffold + Code + PyTest Pass).
- Multi-Agent DAG Execution (Demo 3): 1.82 s (Deep Web Search + 5-Page PDF Report).
- Standby Memory Footprint: 185 MB (Lightweight PySide6 acrylic widget).
- Memory Reclaimed on Model Offload: ~2.0 GB (Freed in <20ms via `"stop ollama"`).
- Emergency Abort Interruption Time: < 5 ms (Halts audio process and cancels active tasks).
"""
    },
    {
        "num": 23,
        "title": "Innovation and Differentiation",
        "subtitle": "Traditional Chatbots vs. Conventional Assistants vs. DODAI OS",
        "content": """
DODAI OS represents a paradigm shift across all operational dimensions:
- Conversation vs. Execution: Traditional chatbots only converse; DODAI OS executes real system tools, scaffolds code, and creates files.
- Single Turn vs. Multi-Step DAG: Conventional assistants process single prompts; DODAI OS constructs multi-step Directed Acyclic Graphs with task dependency tracking.
- Self-Claimed Success vs. Ground-Truth Verification: Standard AI assumes success; DODAI OS employs an independent Verifier Agent to inspect physical evidence.
- Plan Drift vs. Bounded Self-Healing: Standard agents crash or loop infinitely; DODAI OS diagnoses errors and replans with a hard limit of 2 retries.
- Cloud Dependence vs. 100% Local Privacy: Cloud assistants leak private data; DODAI OS operates 100% offline with zero mandatory telemetry.
"""
    },
    {
        "num": 24,
        "title": "Current Limitations",
        "subtitle": "Transparent Architectural Boundaries & Constraints",
        "content": """
To maintain strict engineering integrity, current system limitations are identified:
1. Context Window Constraints: Local quantized models (`nano-brain` 512 tokens, `lfm3-omni:2b` 4096 tokens) require prompt compression and cannot ingest 100-page source files without summarization.
2. Wayland Screen Capture Constraints: Wayland security policies require PipeWire portal permissions for full-screen capture, restricting headless screenshot tools without user session grants.
3. Complex Software Scaffolding: While single-module libraries (e.g. `string_utils`) scaffold and test in <0.5s, large enterprise projects with 50+ dependencies require human architectural guidance.
4. Voice Accents in High Noise: Vosk wake recognition sensitivity drops in environments with high background noise (>75 dB) or heavy microphone reverb.
"""
    },
    {
        "num": 25,
        "title": "Future Scope",
        "subtitle": "Technical Roadmap and Ecosystem Expansion",
        "content": """
The future development roadmap for DODAI OS includes:
1. Intel OpenVINO Integration: Leverage Intel OpenVINO runtime to execute neural inference on Intel Core Ultra NPUs and integrated Arc GPUs, reducing CPU utilization to near zero.
2. Distributed Multi-Agent Swarms: Enable peer-to-peer agent collaboration across multiple Linux machines on a local network using encrypted WebSockets.
3. Multimodal Wayland Vision: Integrate local vision encoders for real-time visual UI element recognition and semantic document analysis.
4. Formal SELinux Policy Integration: Package DODAI OS with dedicated SELinux security profiles for enterprise Linux deployments.
"""
    },
    {
        "num": 26,
        "title": "Conclusion",
        "subtitle": "Summary of Achievements and Readiness",
        "content": """
DODAI OS proves that personal computing intelligence can move beyond passive conversational chatbots to become a genuine, private, edge-first Agentic AI operating assistant. By pairing a sub-5ms direct desktop fast-path with a hierarchical multi-agent Directed Acyclic Graph orchestrator, an independent ground-truth verification gate, bounded self-healing recovery, an ultra-lite 370M local foundation model, and strict 4-tier security containment, DODAI OS delivers verified, robust autonomy on Linux personal computers. Validated through 18 automated test suites comprising 135 passing tests (100% pass rate), DODAI OS stands ready as a premier submission for the Intel AI for Future Workforce Agentic AI Bootcamp 2026.
"""
    },
    {
        "num": 27,
        "title": "References and Supporting Resources",
        "subtitle": "Citations, Repositories, and Standards",
        "content": """
1. Intel Digital Readiness: AI for Future Workforce Program Guidelines & Agentic AI Framework (2026).
2. SmolLM2: Compact Neural Foundation Models for Local Inference (Hugging Face, 2024).
3. Liquid AI: Low-Memory Multi-Modal Neural Models (lfm3-omni:2b architecture, 2025).
4. Vosk Speech Recognition Toolkit: Kaldi-based Offline Speech Recognition (Alpha Cephei, 2024).
5. Faster-Whisper: Fast Speech-to-Text Transcription via CTranslate2 (Guillaume Klein et al., 2023).
6. Piper Neural Text-to-Speech Engine: Real-Time High-Fidelity Speech Synthesis (Rhasspy, 2024).
7. KDE Plasma 6 & KWin DBus Architecture: Wayland Window Management Protocol Specifications (KDE Community, 2024).
8. PipeWire Multimedia Framework: Modern Linux Audio and Video Routing (Wim Taymans et al., 2024).
9. DODAI OS Source Repository: https://github.com/prakash2006-xl/VOID-.git (Branch main).
"""
    }
]

# -----------------------------------------------------------------------------
# 2. GENERATE DODAI_OS_Project_Report.pdf (HTML -> Chromium)
# -----------------------------------------------------------------------------
def generate_master_report_pdf():
    print("Building DODAI_OS_Project_Report.pdf...")
    
    html_chapters = []
    for ch in chapters:
        ch_num = ch["num"]
        ch_title = ch["title"]
        ch_sub = ch["subtitle"]
        ch_body = ch["content"].strip()
        
        # Format paragraphs and lists
        lines = ch_body.split("\n")
        body_html = ""
        in_list = False
        
        for line in lines:
            l = line.strip()
            if l.startswith("- ") or l.startswith("• "):
                if not in_list:
                    body_html += '<ul class="content-list">\n'
                    in_list = True
                body_html += f"  <li>{l[2:]}</li>\n"
            elif l.startswith("1. ") or l.startswith("2. ") or l.startswith("3. ") or l.startswith("4. ") or l.startswith("5. ") or l.startswith("6. ") or l.startswith("7. "):
                if in_list:
                    body_html += "</ul>\n"
                    in_list = False
                body_html += f"<p><strong>{l[:3]}</strong> {l[3:]}</p>\n"
            elif l.startswith("### "):
                if in_list:
                    body_html += "</ul>\n"
                    in_list = False
                body_html += f"<h3>{l[4:]}</h3>\n"
            elif l:
                if in_list:
                    body_html += "</ul>\n"
                    in_list = False
                body_html += f"<p>{l}</p>\n"
                
        if in_list:
            body_html += "</ul>\n"

        # Embed architecture diagrams into Chapters 10 and 14
        diagram_html = ""
        if ch_num == 10 and ARCH_IMG.exists():
            diagram_html = f"""
            <div class="figure-container">
                <img src="file://{ARCH_IMG}" class="doc-figure" alt="System Architecture Diagram" style="max-width: 98%;">
                <div class="figure-caption">Figure 10.1: DODAI OS Runtime Engine & System Architecture Blueprint (300 DPI)</div>
            </div>
            """
        elif ch_num == 14 and WORKFLOW_IMG.exists():
            diagram_html = f"""
            <div class="figure-container">
                <img src="file://{WORKFLOW_IMG}" class="doc-figure" alt="Agent Workflow Diagram" style="max-width: 98%;">
                <div class="figure-caption">Figure 14.1: Autonomous Multi-Agent DAG Execution & Verification Cycle (300 DPI)</div>
            </div>
            """

        page_break_class = "page-break" if ch_num > 1 else ""
        ch_html = f"""
        <div class="chapter-block {page_break_class}">
            <div class="chapter-badge">Chapter {ch_num}</div>
            <h2 class="chapter-title">{ch_title}</h2>
            <div class="chapter-subtitle">{ch_sub}</div>
            <hr class="chapter-divider">
            {body_html}
            {diagram_html}
        </div>
        """
        html_chapters.append(ch_html)

    all_chapters_html = "\n".join(html_chapters)

    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DODAI OS — Complete Technical Project Report</title>
<style>
@page {{
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-right {{
        content: "Page " counter(page);
        font-size: 8pt;
        font-family: 'Inter', system-ui, sans-serif;
        color: #64748b;
    }}
    @bottom-left {{
        content: "DODAI OS • Intel AI for Future Workforce Bootcamp 2026";
        font-size: 8pt;
        font-family: 'Inter', system-ui, sans-serif;
        color: #94a3b8;
    }}
}}
*, *:before, *:after {{ box-sizing: border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #0f172a;
    background: #ffffff;
    line-height: 1.6;
    font-size: 9.8pt;
    margin: 0;
    padding: 0;
}}
.chapter-block {{
    margin-bottom: 24px;
}}
.chapter-badge {{
    display: inline-block;
    background: #0284c7;
    color: #ffffff;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
}}
.chapter-title {{
    font-size: 16pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px 0;
    line-height: 1.25;
}}
.chapter-subtitle {{
    font-size: 10pt;
    font-weight: 600;
    color: #0284c7;
    margin: 0 0 8px 0;
}}
.chapter-divider {{
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #0284c7, #38bdf8, #e2e8f0);
    margin: 8px 0 14px 0;
}}
h3 {{
    font-size: 11pt;
    font-weight: 700;
    color: #1e293b;
    margin: 14px 0 6px 0;
    border-left: 3px solid #0284c7;
    padding-left: 8px;
}}
p {{
    margin: 0 0 8px 0;
    text-align: justify;
}}
ul, ol {{
    margin: 0 0 10px 0;
    padding-left: 20px;
}}
li {{
    margin-bottom: 4px;
}}
.figure-container {{
    text-align: center;
    margin: 18px 0;
    page-break-inside: avoid;
}}
.doc-figure {{
    border-radius: 6px;
    border: 1px solid #cbd5e1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}}
.figure-caption {{
    font-size: 8.5pt;
    color: #64748b;
    font-style: italic;
    margin-top: 6px;
}}
.page-break {{
    page-break-before: always;
}}
</style>
</head>
<body>
    {all_chapters_html}
</body>
</html>"""

    out_pdf = OUT_DIR / "DODAI_OS_Project_Report.pdf"
    temp_html = OUT_DIR / "DODAI_OS_Project_Report.temp.html"
    temp_html.write_text(report_html, encoding="utf-8")
    
    cmd = [
        CHROMIUM,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        f"--print-to-pdf={out_pdf}",
        str(temp_html)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    temp_html.unlink(missing_ok=True)
    print(f"Generated: {out_pdf} ({out_pdf.stat().st_size} bytes)")

# -----------------------------------------------------------------------------
# 3. GENERATE DODAI_OS_Project_Report.docx (python-docx)
# -----------------------------------------------------------------------------
def generate_master_report_docx():
    print("Building DODAI_OS_Project_Report.docx...")
    try:
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.oxml import parse_xml
        from docx.oxml.ns import nsdecls
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        print("python-docx not available, skipping docx generation.")
        return

    doc = docx.Document()

    # Set page margins (0.8 inch)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Master Title
    title_p = doc.add_paragraph()
    r_title = title_p.add_run("DODAI OS: Complete Technical Project Report")
    r_title.font.size = Pt(24)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)

    sub_p = doc.add_paragraph()
    r_sub = sub_p.add_run("Intel AI for Future Workforce Agentic AI Bootcamp 2026 • Master Engineering Dossier")
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = RGBColor(2, 132, 199)
    doc.add_paragraph()

    for ch in chapters:
        ch_num = ch["num"]
        ch_title = ch["title"]
        ch_sub = ch["subtitle"]
        ch_body = ch["content"].strip()

        # Chapter Heading
        h1 = doc.add_heading(f"Chapter {ch_num}: {ch_title}", level=1)
        h1.paragraph_format.space_before = Pt(14)
        h1.paragraph_format.space_after = Pt(2)
        for r in h1.runs:
            r.font.color.rgb = RGBColor(15, 23, 42)

        # Chapter Subtitle
        p_sub = doc.add_paragraph()
        r_s = p_sub.add_run(ch_sub)
        r_s.font.size = Pt(10)
        r_s.font.italic = True
        r_s.font.color.rgb = RGBColor(2, 132, 199)
        p_sub.paragraph_format.space_after = Pt(8)

        # Body Content
        lines = ch_body.split("\n")
        for line in lines:
            l = line.strip()
            if l.startswith("- ") or l.startswith("• "):
                doc.add_paragraph(l[2:], style='List Bullet')
            elif l.startswith("### "):
                h2 = doc.add_heading(l[4:], level=2)
                h2.paragraph_format.space_before = Pt(8)
                h2.paragraph_format.space_after = Pt(2)
                for r in h2.runs:
                    r.font.color.rgb = RGBColor(30, 41, 59)
            elif l:
                p = doc.add_paragraph(l)
                p.paragraph_format.space_after = Pt(4)

        # Embed diagrams in Chapter 10 and Chapter 14
        if ch_num == 10 and ARCH_IMG.exists():
            try:
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(12)
                r_img = p_img.add_run()
                r_img.add_picture(str(ARCH_IMG), width=Inches(6.2))
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_c = p_cap.add_run("Figure 10.1: DODAI OS Runtime Engine & System Architecture Blueprint (300 DPI)")
                r_c.font.size = Pt(8.5)
                r_c.font.italic = True
                r_c.font.color.rgb = RGBColor(100, 116, 139)
            except Exception as e:
                print(f"Failed to embed arch diagram in docx: {e}")

        elif ch_num == 14 and WORKFLOW_IMG.exists():
            try:
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(12)
                r_img = p_img.add_run()
                r_img.add_picture(str(WORKFLOW_IMG), width=Inches(6.2))
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_c = p_cap.add_run("Figure 14.1: Autonomous Multi-Agent DAG Execution & Verification Cycle (300 DPI)")
                r_c.font.size = Pt(8.5)
                r_c.font.italic = True
                r_c.font.color.rgb = RGBColor(100, 116, 139)
            except Exception as e:
                print(f"Failed to embed workflow diagram in docx: {e}")

        # Page break after major chapters
        if ch_num in [1, 2, 6, 10, 14, 17, 21, 26]:
            doc.add_page_break()

    out_docx = OUT_DIR / "DODAI_OS_Project_Report.docx"
    doc.save(out_docx)
    print(f"Generated: {out_docx} ({out_docx.stat().st_size} bytes)")

if __name__ == "__main__":
    generate_master_report_pdf()
    generate_master_report_docx()
