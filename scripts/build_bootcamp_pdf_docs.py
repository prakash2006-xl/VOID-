#!/usr/bin/env python3
"""
Generate DODAI_OS_Executive_Summary.pdf and DODAI_OS_Model_and_Function_Documentation.pdf
using modern HTML5/CSS print layouts and Chromium headless PDF engine.
"""

import os
import time
import shutil
import subprocess
from pathlib import Path

OUT_DIR = Path("/run/media/prakash/TR_39/VOID/DODAI_OS_INTEL_BOOTCAMP_SUBMISSION")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHROMIUM = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")

CSS_BASE = """
@page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-right {
        content: "Page " counter(page);
        font-size: 8pt;
        font-family: 'Inter', system-ui, sans-serif;
        color: #64748b;
    }
    @bottom-left {
        content: "DODAI OS • Intel AI for Future Workforce Bootcamp 2026";
        font-size: 8pt;
        font-family: 'Inter', system-ui, sans-serif;
        color: #94a3b8;
    }
}
*, *:before, *:after { box-sizing: border-box; }
body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #0f172a;
    background: #ffffff;
    line-height: 1.6;
    font-size: 9.8pt;
    margin: 0;
    padding: 0;
}
.header-bar {
    height: 4px;
    background: linear-gradient(90deg, #0284c7, #38bdf8, #818cf8, #10b981);
    margin-bottom: 16px;
    border-radius: 2px;
}
.header-banner {
    border-bottom: 2px solid #0284c7;
    padding-bottom: 12px;
    margin-bottom: 16px;
}
.doc-meta {
    display: flex;
    justify-content: space-between;
    font-size: 8.5pt;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 4px;
}
.doc-title {
    font-size: 20pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 6px 0;
    line-height: 1.2;
}
.doc-subtitle {
    font-size: 10.5pt;
    font-weight: 600;
    color: #0284c7;
    margin: 0 0 4px 0;
}
.doc-author {
    font-size: 9pt;
    color: #475569;
    margin: 0;
}
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 14px 0 16px 0;
}
.metric-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: center;
}
.metric-val { font-size: 14pt; font-weight: 800; color: #0284c7; margin-bottom: 2px; }
.metric-lbl { font-size: 7.5pt; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
.callout-box {
    background: #f0f9ff;
    border-left: 4px solid #0284c7;
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin: 14px 0;
}
.callout-title { font-weight: 700; color: #0369a1; font-size: 10pt; margin-bottom: 4px; }
h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin: 16px 0 8px 0;
}
h3 {
    font-size: 10.5pt;
    font-weight: 700;
    color: #1e293b;
    margin: 12px 0 4px 0;
}
p { margin: 0 0 8px 0; }
ul, ol { margin: 0 0 10px 0; padding-left: 20px; }
li { margin-bottom: 4px; }
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
    margin: 12px 0;
}
.data-table th {
    background: #0f172a;
    color: #ffffff;
    padding: 6px 8px;
    text-align: left;
    font-weight: 600;
    border: 1px solid #334155;
}
.data-table td {
    padding: 6px 8px;
    border: 1px solid #e2e8f0;
}
.data-table tr.even-row { background: #f8fafc; }
.data-table tr.odd-row { background: #ffffff; }
.badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 7.5pt;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-green { background: #dcfce7; color: #15803d; }
.badge-blue { background: #e0f2fe; color: #0369a1; }
.badge-indigo { background: #e0e7ff; color: #4338ca; }
.badge-yellow { background: #fef3c7; color: #b45309; }
.page-break { page-break-before: always; }
"""

def render_html_to_pdf(html_content: str, out_path: Path):
    temp_html = out_path.with_suffix(".temp.html")
    temp_html.write_text(html_content, encoding="utf-8")
    cmd = [
        CHROMIUM,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        f"--print-to-pdf={out_path}",
        str(temp_html)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    temp_html.unlink(missing_ok=True)
    print(f"Generated PDF: {out_path} ({out_path.stat().st_size} bytes)")

def build_executive_summary_pdf():
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DODAI OS — Executive Summary Dossier</title>
<style>{CSS_BASE}</style>
</head>
<body>
    <div class="header-bar"></div>
    <div class="header-banner">
        <div class="doc-meta">
            <span>Intel AI for Future Workforce Bootcamp 2026</span>
            <span>Submission Track: Agentic AI</span>
        </div>
        <h1 class="doc-title">DODAI OS: Executive Summary & Project Abstract</h1>
        <div class="doc-subtitle">Your Local Autonomous Linux Intelligence • Agentic Linux AI Assistant</div>
        <div class="doc-author">Author & System Architect: Prakash (prakash2006-xl) | Platform: Fedora Linux 40+ KDE Plasma 6 (Wayland)</div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-val">&lt; 3.8 ms</div>
            <div class="metric-lbl">Direct Fast-Path Latency</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">100% Offline</div>
            <div class="metric-lbl">Local Privacy & Sovereignty</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">7 Agents</div>
            <div class="metric-lbl">Coordinated DAG Core</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">135 / 135</div>
            <div class="metric-lbl">Tests Passed (100%)</div>
        </div>
    </div>

    <div class="callout-box">
        <div class="callout-title">💡 Strategic Vision & Core Concept</div>
        <div>DODAI OS is a local-first, verified autonomous AI operating assistant engineered for Linux personal computers. While standard desktop assistants operate as passive chatbots that respond with text, DODAI OS functions as an active operating system companion that understands user objectives, constructs multi-step Directed Acyclic Graph (DAG) execution plans, orchestrates specialized agents, executes real system and development tools, independently verifies ground-truth outcomes, and self-heals through bounded retries.</div>
    </div>

    <h2>1. Executive Summary (185 Words)</h2>
    <p>DODAI OS transforms the Linux desktop into an autonomous, agentic operating workplace. While traditional desktop assistants function merely as passive conversational wrappers that answer prompts with text, DODAI OS operates as an active, permission-aware multi-agent operating system. It possesses the capability to understand high-level user intent, formulate structured multi-step plans as Directed Acyclic Graphs (DAGs), dynamically delegate tasks across specialized autonomous agents, execute system and development tools in sandboxed workspaces, independently verify physical ground-truth results, self-heal through bounded retries, and retain memory across a 7-day rolling window.</p>
    <p>DODAI OS uniquely solves the tension between instant responsiveness and deep reasoning through a <strong>Dual-Tier Coexistence Architecture</strong>: Tier 1 provides sub-5ms local DBus and regex dispatch for instant desktop controls without GPU overhead; Tier 2 activates a hierarchical team of 7 specialized agents (Supervisor, Planner, Linux Intelligence, Developer, Research, Tool Execution, Verifier, and Recovery) for complex multi-step workflows. All operations strictly obey a 4-Tier Security Doctrine ensuring zero unauthorized root modifications and strict human-in-the-loop approval gating, making DODAI OS a private, robust, edge-first Agentic AI platform.</p>

    <h2>2. Project Abstract (310 Words)</h2>
    <p>Personal computing in the modern knowledge economy remains fundamentally manual. Knowledge workers, developers, and researchers spend considerable cognitive effort switching contexts, diagnosing system health, organizing workspaces, compiling research, scaffolding software projects, and verifying computational workflows. Existing artificial intelligence assistants remain confined to text generation; they lack operating system integration, cannot inspect system states, fail to verify whether their actions succeeded, and rely entirely on external cloud infrastructure that compromises user data privacy.</p>
    <p>DODAI OS solves this paradigm bottleneck by introducing an autonomous operating layer tailored for Fedora Linux (KDE Plasma 6 on Wayland). Built upon a local-first philosophy, DODAI OS integrates state-of-the-art quantized neural foundation models (including an ultra-lite 370M LoRA-tuned local brain and multi-modal models) alongside an open-architecture cloud AI bridge. The platform features an autonomous hierarchical multi-agent framework: when a user gives a high-level goal, the Supervisor and Planner Agents construct a Directed Acyclic Graph (DAG) with explicit task dependencies, delegating execution across dedicated Linux Intelligence, Developer, Research, and Tool Execution agents interfacing with 105 native tools.</p>
    <p>Crucially, DODAI OS enforces an architectural separation between execution and certification. An independent Verifier Agent evaluates ground-truth physical artifacts (file outputs, process states, stderr streams, unit test pass rates) before declaring task completion. If discrepancies arise, a bounded Recovery Agent analyzes errors and replans execution without infinite loops. Operating alongside a sub-5ms local fast-path for hardware window and media management, continuous acoustic wake recognition via Vosk, Faster-Whisper int8 STT, Piper neural speech synthesis, and 7-day rolling persistent thought retention, DODAI OS establishes a new standard for private, resilient, and verified Agentic AI operating systems on Linux personal computing hardware.</p>

    <div class="page-break"></div>
    <div class="header-bar"></div>

    <h2>3. Short Description for Google Submission Form</h2>
    <p>DODAI OS is an autonomous, local-first Agentic AI desktop operating assistant for Linux. Unlike conventional chatbots that produce text, DODAI OS understands complex natural-language goals, decomposes them into Directed Acyclic Graph (DAG) execution plans, and orchestrates a team of specialized agents (Linux Intel, Developer, Research, Tool Execution) to interact with real system tools, scaffold software, execute shell diagnostics, and compile publication-grade reports. It features an independent Verifier Agent that inspects physical filesystem and process ground truth, a bounded self-healing Recovery Agent, a sub-5ms fast path for window and hardware control, a 1.5GB SSD memory engine with 7-day rolling retention, and strict 4-Tier permission containment—delivering fully verified, private desktop autonomy.</p>

    <h2>4. Five Key Innovations</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th style="width: 25%;">Innovation</th>
                <th style="width: 45%;">Technical Implementation</th>
                <th style="width: 30%;">Operational Advantage</th>
            </tr>
        </thead>
        <tbody>
            <tr class="even-row">
                <td><strong>1. Dual-Tier Coexistence Architecture</strong></td>
                <td>Sub-5ms direct KWin DBus & regex fast-path paired seamlessly with an autonomous multi-agent DAG engine.</td>
                <td>Zero latency delay on simple tasks (window control, volume) while enabling deep reasoning for complex goals.</td>
            </tr>
            <tr class="odd-row">
                <td><strong>2. Independent Verification Gate</strong></td>
                <td>Architectural separation where an independent Verifier Agent validates exit codes, physical files, and test results.</td>
                <td>Eliminates LLM hallucination and self-certification of incomplete or failed tasks.</td>
            </tr>
            <tr class="even-row">
                <td><strong>3. Bounded Self-Healing Recovery</strong></td>
                <td>Runtime error capture triggering root-cause analysis, alternative strategy synthesis, and max 2 bounded retries.</td>
                <td>Prevents infinite loops and plan drift while autonomously correcting recoverable errors.</td>
            </tr>
            <tr class="odd-row">
                <td><strong>4. Ultra-Lite Local Brain (`nano-brain`)</strong></td>
                <td>SmolLM2-360M LoRA fine-tuned on CPU AVX2 FMA execution units (<150MB RAM, sub-350ms generation).</td>
                <td>Guarantees sub-second local inference and leaves 98% of system RAM free for actual applications.</td>
            </tr>
            <tr class="even-row">
                <td><strong>5. 7-Day Rolling High-Thought Memory</strong></td>
                <td>168-hour rolling memory pool in a 1.5GB NVMe ring buffer with autonomous weekly synthesis (.json & .md).</td>
                <td>Preserves historical context, past plans, and user preferences across reboots.</td>
            </tr>
        </tbody>
    </table>

    <h2>5. Five Important Agentic Capabilities</h2>
    <ul>
        <li><strong>Autonomous Goal Decomposition & DAG Planning:</strong> Decomposes complex multi-faceted objectives into Directed Acyclic Graphs with task dependency tracking.</li>
        <li><strong>Linux System Intelligence & Process Telemetry:</strong> Directly inspects `/proc`, system load, memory, disk vitals, and listening network sockets without manual user bash commands.</li>
        <li><strong>Autonomous Software Engineering:</strong> Scaffolds complete multi-file project directories, writes implementation code, and executes automated pytest suites in sandbox.</li>
        <li><strong>Multi-Facet Web Research & Document Synthesis:</strong> Synthesizes real-world research into publication-grade PDF and Word (.docx) documents with dynamic charts and comparison tables.</li>
        <li><strong>4-Tier Security & Sandbox Isolation:</strong> Strictly enforces Level 1 (ReadOnly) to Level 4 (Forbidden) boundaries protecting operating system kernel integrity.</li>
    </ul>

    <h2>6. Why DODAI OS Qualifies as an Agentic AI Project</h2>
    <p>DODAI OS satisfies every foundational pillar of genuine Agentic AI:
    (1) <em>Autonomous Perception</em> via continuous acoustic listening and operating system state monitoring;
    (2) <em>Deliberation</em> via the Supervisor and Planner Agents that formulate structured multi-step DAG plans;
    (3) <em>Delegation</em> to specialized agents with distinct role boundaries;
    (4) <em>Action</em> through direct execution of 105 Linux desktop tools;
    (5) <em>Evaluation</em> via an independent Verifier Agent checking physical ground truth;
    (6) <em>Self-Healing</em> through bounded recovery replanning; and
    (7) <em>Retention</em> across a 7-day rolling memory pool.</p>

    <h2>7. Real-World Problem Solved</h2>
    <p>Eliminates the cognitive friction and manual fragmentation of Linux desktop productivity. Modern engineers and knowledge workers waste 20-30% of their workday on repetitive operations: diagnosing memory leaks, checking network ports, organizing files, converting research into structured reports, scaffolding repetitive boilerplate, and toggling windows. DODAI OS acts as a 24/7 private, local autonomous partner that executes these multi-step workflows end-to-end with verified ground truth—saving hours daily while keeping confidential data 100% on the user's machine.</p>
</body>
</html>"""
    out_pdf = OUT_DIR / "DODAI_OS_Executive_Summary.pdf"
    render_html_to_pdf(html, out_pdf)

def build_model_and_function_pdf():
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DODAI OS — AI Models, Agent Functions and Execution Capabilities</title>
<style>{CSS_BASE}</style>
</head>
<body>
    <div class="header-bar"></div>
    <div class="header-banner">
        <div class="doc-meta">
            <span>Intel AI for Future Workforce Bootcamp 2026</span>
            <span>Technical Documentation Series</span>
        </div>
        <h1 class="doc-title">AI Models, Agent Functions and Execution Capabilities</h1>
        <div class="doc-subtitle">Comprehensive Architectural & Model Evaluation Dossier for DODAI OS</div>
        <div class="doc-author">Author: Prakash (prakash2006-xl) | Platform: Fedora Linux 40+ (KDE Plasma 6 / Wayland)</div>
    </div>

    <h2>1. Model-to-Function Mapping Table</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th style="width: 18%;">Component</th>
                <th style="width: 22%;">Model / Technology</th>
                <th style="width: 32%;">Primary Function</th>
                <th style="width: 16%;">Execution Mode</th>
                <th style="width: 12%;">Status</th>
            </tr>
        </thead>
        <tbody>
            <tr class="even-row">
                <td><strong>Local Ultra-Lite Brain</strong></td>
                <td>`nano-brain:latest`<br>(SmolLM2-360M-Instruct)</td>
                <td>Ultra-low-latency local conversational response, intent extraction, coding assistance, and reasoning under resource caps.</td>
                <td>Local CPU (AVX2 FMA, &lt;150MB RAM) via Ollama</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
            <tr class="odd-row">
                <td><strong>Local Multi-Modal Brain</strong></td>
                <td>`lfm3-omni:2b`<br>(Liquid AI 1.7B Q4_K_M)</td>
                <td>Multi-modal local agentic reasoning, multi-turn tool calling, structured planning, and image comprehension.</td>
                <td>Local Ollama Daemon (GPU/VRAM Standby)</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
            <tr class="even-row">
                <td><strong>Cloud Decider Bridge</strong></td>
                <td>OpenRouter / Perplexity `pplx-decider-flash-v1.3:free`</td>
                <td>Optional high-complexity DAG planning, fallback when local models are offloaded, and deep domain synthesis.</td>
                <td>Cloud API (HTTPS REST with Secret Masking)</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
            <tr class="odd-row">
                <td><strong>Acoustic Wake Recognizer</strong></td>
                <td>Vosk Kaldi FST<br>(vosk-model-small-en-us-0.15)</td>
                <td>Continuous real-time open-grammar listening for wake triggers (`"hey void"`, `"void"`) with &lt;120ms latency.</td>
                <td>Local CPU Subprocess (PipeWire Stream)</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
            <tr class="even-row">
                <td><strong>Speech-to-Text (STT)</strong></td>
                <td>Faster-Whisper Base int8<br>(AVX2 4-thread CPU)</td>
                <td>High-accuracy spoken utterance transcription with dynamic Silero VAD silence trimming (~350ms latency).</td>
                <td>Local CPU int8 Quantized</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
            <tr class="odd-row">
                <td><strong>Neural Speech Synthesis</strong></td>
                <td>Piper Neural TTS<br>(vits-piper-en_US-ryan-medium)</td>
                <td>Natural, high-fidelity 22.05 kHz voice generation (160+ wpm at 1.06x speed) via native PipeWire streaming.</td>
                <td>Local ONNX Runtime (Native PipeWire pw-play)</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
            <tr class="even-row">
                <td><strong>Multi-Agent Orchestrator</strong></td>
                <td>DODAI OS DAG Core<br>(Supervisor & Planner)</td>
                <td>Decomposes natural language goals into Directed Acyclic Graphs with dependency arrays and role assignments.</td>
                <td>Local Python Async Engine (`agentic/`)</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
            <tr class="odd-row">
                <td><strong>Tool Hub & DBus</strong></td>
                <td>105 Dodaios Native Tools + KWin Wayland DBus</td>
                <td>Direct operating system interaction: window management, process inspection, filesystem manipulation, and documents.</td>
                <td>Native Linux Subprocesses & DBus Calls</td>
                <td><span class="badge badge-green">Production</span></td>
            </tr>
        </tbody>
    </table>

    <div class="page-break"></div>
    <div class="header-bar"></div>

    <h2>2. Architectural Taxonomy: LLM vs. Agent vs. Orchestration vs. Executable Tool</h2>
    <p>To avoid conceptual ambiguity, DODAI OS maintains a strict architectural distinction across four tiers:</p>
    <ul>
        <li><strong>Foundation LLM (The Cognitive Engine):</strong> The neural language model (`nano-brain`, `lfm3-omni:2b`, or cloud provider) acts purely as an inference predictor. It interprets language, classifies intents, and predicts structured responses. It does <em>not</em> possess execution authority.</li>
        <li><strong>Agent (The Role-Bounded Actor):</strong> An autonomous software entity encapsulating a specific role (e.g., Developer Agent, Linux Intelligence Agent, Verifier Agent). Each agent has a defined system prompt, constrained tool access, state tracking, and specialized decision boundaries.</li>
        <li><strong>Orchestration Framework (The DAG Coordinator):</strong> The Supervisor and Planner agents in `agentic/orchestrator.py` that manage workflow state machines (`WorkflowLifecycleState`), schedule task execution order based on `depends_on` dependencies, and route results between agents.</li>
        <li><strong>Executable Tool (The Actuator):</strong> Sandboxed, deterministic Python/Shell functions registered in `ToolRegistry` (lines 20-100 of `agentic/tools.py`). Tools interact with the physical OS: reading `/proc`, scaffolding directories, executing `pytest`, or making DBus calls.</li>
    </ul>

    <h2>3. The Autonomous Deliberation & Planning Cycle</h2>
    <ol>
        <li><strong>Goal Ingestion:</strong> The user gives a natural-language command (voice or text). Vosk wakes the system, Faster-Whisper transcribes the audio, and phonetic normalization standardizes vocabulary.</li>
        <li><strong>Intent Classification:</strong> The `SupervisorAgent` inspects the request. Direct desktop controls (volume, window toggle, timers) route immediately to the sub-5ms fast-path. Multi-faceted complex requests activate the agentic pipeline.</li>
        <li><strong>DAG Formulation:</strong> The `PlannerAgent` analyzes the objective, breaks it down into discrete sub-tasks, assigns specialized agent roles, maps input/output dependencies (`depends_on`), and assigns security levels (Level 1 to Level 4).</li>
        <li><strong>Task Execution:</strong> The orchestrator executes tasks respecting dependency order. Execution agents invoke sandboxed tools and capture `ToolResult` outputs including exit codes, execution duration, and generated artifacts.</li>
        <li><strong>Independent Verification Gate:</strong> The `VerifierAgent` independently evaluates ground truth: verifying file existence, inspecting stdout/stderr for errors, checking return codes, or executing unit test suites.</li>
        <li><strong>Self-Healing Recovery:</strong> If the verifier detects failure, the `RecoveryAgent` inspects error traces, formulates an alternative strategy, and applies a bounded retry (max 2 attempts).</li>
        <li><strong>Completion & Memory Commit:</strong> On successful verification, the Supervisor commits the execution trace to the 7-day rolling memory pool (`memory/weekly_episodes.jsonl`), records an immutable audit log, and synthesizes a natural spoken response via Piper TTS.</li>
    </ol>

    <h2>4. Local Model Lifecycle & Memory Preservation</h2>
    <p>DODAI OS addresses the resource constraints of edge personal computers through dynamic model lifecycle management:</p>
    <ul>
        <li><strong>Ultra-Lite nano-brain Residency:</strong> Consumes only 98MB to 140MB RAM. Responds in ~210ms to ~350ms, enabling real-time local chat with near-zero CPU and memory impact.</li>
        <li><strong>On-Demand lfm3-omni:2b Loading:</strong> When multi-modal tool calling is needed, Ollama loads the 1.7B GGUF weights into APU/GPU memory.</li>
        <li><strong>Instant Standby Offloading:</strong> Upon voice command (<em>"Hey VOID, stop model"</em> or <em>"offload model"</em>), the system terminates the `llama-server` process, immediately freeing ~2.0 GB of RAM in under 20ms while seamlessly switching to Cloud AI fallback.</li>
    </ul>

    <h2>5. Online vs. Offline Capabilities Matrix</h2>
    <table class="data-table">
        <thead>
            <tr>
                <th style="width: 35%;">Subsystem / Capability</th>
                <th style="width: 20%;">Offline (Local)</th>
                <th style="width: 20%;">Online (Cloud)</th>
                <th style="width: 25%;">Execution Mechanism</th>
            </tr>
        </thead>
        <tbody>
            <tr class="even-row">
                <td>Acoustic Wake-Word Detection</td>
                <td><span class="badge badge-green">100% Offline</span></td>
                <td>N/A</td>
                <td>Vosk Kaldi FST on local CPU</td>
            </tr>
            <tr class="odd-row">
                <td>Speech-to-Text Transcription</td>
                <td><span class="badge badge-green">100% Offline</span></td>
                <td>Optional Cloud STT</td>
                <td>Faster-Whisper Base int8 (AVX2)</td>
            </tr>
            <tr class="even-row">
                <td>Sub-5ms Window & Media Controls</td>
                <td><span class="badge badge-green">100% Offline</span></td>
                <td>N/A</td>
                <td>KWin DBus / WirePlumber</td>
            </tr>
            <tr class="odd-row">
                <td>Linux System Vitals & Diagnostics</td>
                <td><span class="badge badge-green">100% Offline</span></td>
                <td>N/A</td>
                <td>Direct `/proc`, `df`, socket inspection</td>
            </tr>
            <tr class="even-row">
                <td>Autonomous Software Scaffolding</td>
                <td><span class="badge badge-green">100% Offline</span></td>
                <td>Enhanced via Cloud</td>
                <td>Python `DeveloperAgent` & `pytest`</td>
            </tr>
            <tr class="odd-row">
                <td>Publication Document Drafting</td>
                <td><span class="badge badge-green">100% Offline</span></td>
                <td>Enhanced via Cloud</td>
                <td>python-docx & Headless Chromium</td>
            </tr>
            <tr class="even-row">
                <td>Deep Live Web Research</td>
                <td>Offline Snippet Cache</td>
                <td><span class="badge badge-blue">Live Web Search</span></td>
                <td>DuckDuckGo Multi-Source Scraper</td>
            </tr>
            <tr class="odd-row">
                <td>Speech Generation (TTS)</td>
                <td><span class="badge badge-green">100% Offline</span></td>
                <td>N/A</td>
                <td>Piper Neural ONNX via `pw-play`</td>
            </tr>
        </tbody>
    </table>
</body>
</html>"""
    out_pdf = OUT_DIR / "DODAI_OS_Model_and_Function_Documentation.pdf"
    render_html_to_pdf(html, out_pdf)

if __name__ == "__main__":
    build_executive_summary_pdf()
    build_model_and_function_pdf()
