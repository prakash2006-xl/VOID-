#!/usr/bin/env python3
"""
Generate High-Resolution Architecture & Workflow Diagrams for DODAI OS Intel Bootcamp Submission
Outputs:
  - DODAI_OS_System_Architecture.png (300 DPI)
  - DODAI_OS_Agent_Workflow.png (300 DPI)
"""

import os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = Path("/run/media/prakash/TR_39/VOID/DODAI_OS_INTEL_BOOTCAMP_SUBMISSION")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_system_architecture():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # Background canvas
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')

    # Main Header
    ax.text(7.0, 8.15, "DODAI OS — SYSTEM ARCHITECTURE & RUNTIME ENGINE",
            ha='center', va='center', color='#38bdf8', fontsize=16, fontweight='bold')
    ax.text(7.0, 7.85, "Local Autonomous Linux Intelligence • Fedora KDE Plasma 6 (Wayland) • Intel Bootcamp 2026",
            ha='center', va='center', color='#94a3b8', fontsize=10)

    # 1. USER INTERACTION & INPUT LAYER (Top Left)
    rect_input_box = patches.FancyBboxPatch((0.5, 5.0), 3.8, 2.5, boxstyle="round,pad=0.1,rounding_size=0.15",
                                            facecolor='#1e293b', edgecolor='#38bdf8', linewidth=1.5)
    ax.add_patch(rect_input_box)
    ax.text(2.4, 7.25, "1. USER INTERACTION & PERCEPTION", ha='center', va='center', color='#38bdf8', fontsize=10, fontweight='bold')
    
    inputs = [
        "• Vosk Kaldi Real-Time Wake FST ('hey void')",
        "• Faster-Whisper Base int8 (AVX2 4-thread STT)",
        "• PySide6 Glass Island Widget (50px Dynamic Island)",
        "• 3D Fibonacci Neural Core (QPainter Matrix)",
        "• PipeWire 1.4 Native Audio Stream (pw-play)"
    ]
    for i, t in enumerate(inputs):
        ax.text(0.7, 6.85 - (i * 0.38), t, ha='left', va='center', color='#f8fafc', fontsize=8)

    # 2. DUAL-TIER INTENT ROUTER (Top Center)
    rect_router_box = patches.FancyBboxPatch((4.8, 5.0), 4.4, 2.5, boxstyle="round,pad=0.1,rounding_size=0.15",
                                             facecolor='#1e293b', edgecolor='#818cf8', linewidth=1.5)
    ax.add_patch(rect_router_box)
    ax.text(7.0, 7.25, "2. DUAL-TIER COEXISTENCE ROUTER", ha='center', va='center', color='#818cf8', fontsize=10, fontweight='bold')
    
    router_items = [
        "• Sub-5ms Local Fast Path (Direct Regex & DBus)",
        "  - KWin Window Control (Min/Max/Close/Desktop)",
        "  - Volume, Brightness, AST Math, Timers",
        "• Complex Goal Classifier (Supervisor Router)",
        "• Phonetic & Typo Tolerance Normalizer",
        "• Compound Multi-Command Splitting"
    ]
    for i, t in enumerate(router_items):
        ax.text(5.0, 6.85 - (i * 0.34), t, ha='left', va='center', color='#f8fafc', fontsize=7.8)

    # 3. AI MODELS & COGNITIVE BRAIN (Top Right)
    rect_ai_box = patches.FancyBboxPatch((9.7, 5.0), 3.8, 2.5, boxstyle="round,pad=0.1,rounding_size=0.15",
                                         facecolor='#1e293b', edgecolor='#34d399', linewidth=1.5)
    ax.add_patch(rect_ai_box)
    ax.text(11.6, 7.25, "3. AI BRAIN & INFERENCE CORE", ha='center', va='center', color='#34d399', fontsize=10, fontweight='bold')
    
    ai_items = [
        "• Local Ultra-Lite: nano-brain (370M LoRA)",
        "  - <150MB RAM, Sub-350ms Latency (Ollama)",
        "• Multi-Modal Local: lfm3-omni:2b (1.7B GGUF)",
        "• Cloud AI Bridge: OpenRouter / Perplexity",
        "• Dynamic Lifecycle: Standby Unload (~2GB VRAM)",
        "• Piper Neural TTS (Ryan Medium ONNX)"
    ]
    for i, t in enumerate(ai_items):
        ax.text(9.9, 6.85 - (i * 0.34), t, ha='left', va='center', color='#f8fafc', fontsize=7.8)

    # CONNECTING ARROWS Top row
    ax.annotate('', xy=(4.75, 6.25), xytext=(4.35, 6.25),
                arrowprops=dict(arrowstyle="->", color='#38bdf8', lw=2.0))
    ax.annotate('', xy=(9.65, 6.25), xytext=(9.25, 6.25),
                arrowprops=dict(arrowstyle="<->", color='#818cf8', lw=2.0))

    # 4. MULTI-AGENT ORCHESTRATION ENGINE (Middle Span)
    rect_agents_box = patches.FancyBboxPatch((0.5, 2.3), 8.7, 2.3, boxstyle="round,pad=0.1,rounding_size=0.15",
                                             facecolor='#0284c7', edgecolor='#38bdf8', linewidth=1.5, alpha=0.15)
    ax.add_patch(rect_agents_box)
    ax.text(4.85, 4.35, "4. HIERARCHICAL MULTI-AGENT DAG ORCHESTRATOR", ha='center', va='center', color='#38bdf8', fontsize=11, fontweight='bold')

    agent_boxes = [
        (0.7, 2.5, 1.8, 1.5, "Supervisor Agent\n\nGoal Classification\nState Machine\nAudit Trail", "#0f172a", "#38bdf8"),
        (2.7, 2.5, 1.8, 1.5, "Planner Agent\n\nDAG Task Graph\nDependency Order\nAgent Routing", "#0f172a", "#818cf8"),
        (4.7, 2.5, 2.1, 1.5, "Execution Agents\n\n• Linux Intelligence\n• Developer Agent\n• Research Agent\n• Tool Exec Agent", "#0f172a", "#34d399"),
        (7.0, 2.5, 2.0, 1.5, "Verification & Healing\n\n• Verifier Agent\n  (Ground-Truth Gate)\n• Recovery Agent\n  (Max 2 Retries)", "#0f172a", "#fbbf24")
    ]
    for x, y, w, h, text, bg, border in agent_boxes:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.1",
                                    facecolor=bg, edgecolor=border, linewidth=1.3)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', color='#f8fafc', fontsize=7.2, fontweight='bold')

    for ax_idx in range(len(agent_boxes) - 1):
        x1 = agent_boxes[ax_idx][0] + agent_boxes[ax_idx][2]
        x2 = agent_boxes[ax_idx+1][0]
        y_c = agent_boxes[ax_idx][1] + agent_boxes[ax_idx][3]/2
        ax.annotate('', xy=(x2, y_c), xytext=(x1, y_c),
                    arrowprops=dict(arrowstyle="->", color='#38bdf8', lw=1.8))

    # Down arrow from Router to Agents
    ax.annotate('', xy=(4.85, 4.65), xytext=(7.0, 4.95),
                arrowprops=dict(arrowstyle="->", color='#818cf8', lw=2.0))

    # 5. MEMORY & PERSISTENCE ENGINE (Middle Right)
    rect_mem_box = patches.FancyBboxPatch((9.7, 2.3), 3.8, 2.3, boxstyle="round,pad=0.1,rounding_size=0.15",
                                          facecolor='#1e293b', edgecolor='#fbbf24', linewidth=1.5)
    ax.add_patch(rect_mem_box)
    ax.text(11.6, 4.35, "5. 7-DAY PERSISTENT MEMORY", ha='center', va='center', color='#fbbf24', fontsize=10, fontweight='bold')
    mem_items = [
        "• 1.5 GB NVMe SSD Ring Buffer (facts.json)",
        "• 168-Hour Rolling High-Memory Episodes",
        "• Autonomous Weekly Digest (JSON & MD)",
        "• Cross-Turn Contextual Query Engine",
        "• Active Task Manager (tasks.json)",
        "• Immutable Audit Logger (JSONL)"
    ]
    for i, t in enumerate(mem_items):
        ax.text(9.9, 4.0 - (i * 0.32), t, ha='left', va='center', color='#f8fafc', fontsize=7.8)

    # 6. TOOL REGISTRY & LINUX RUNTIME INTEGRATION (Bottom Span)
    rect_tools_box = patches.FancyBboxPatch((0.5, 0.3), 13.0, 1.7, boxstyle="round,pad=0.1,rounding_size=0.15",
                                            facecolor='#1e293b', edgecolor='#10b981', linewidth=1.5)
    ax.add_patch(rect_tools_box)
    ax.text(7.0, 1.75, "6. TOOL EXECUTION FRAMEWORK & LINUX DESKTOP INTEGRATION", ha='center', va='center', color='#10b981', fontsize=10.5, fontweight='bold')

    tool_cols = [
        ("4-Tier Security Gate", "• Level 1: ReadOnly\n• Level 2: Safe Workspace\n• Level 3: User Approval\n• Level 4: FORBIDDEN (sudo, /etc)"),
        ("105 Dodaios Native Tools", "• Multi-Source Web Search\n• Safe Python Scaffolding\n• PyTest Workspace Runner\n• Vitals (/proc, df, loadavg)"),
        ("Desktop Document Engine", "• Publication-Grade PDF (HTML/CSS)\n• Formatted Word Docs (.docx)\n• Excel Workbooks (.xlsx)\n• Dynamic Matplotlib Diagrams"),
        ("Desktop & Media Control", "• KWin DBus Window Calls\n• Chromium Tab/Window DBus\n• PipeWire Audio / WirePlumber\n• Universal File/App Launcher")
    ]
    for i, (col_title, col_text) in enumerate(tool_cols):
        cx = 0.8 + (i * 3.2)
        ax.text(cx, 1.45, col_title, ha='left', va='center', color='#34d399', fontsize=8.2, fontweight='bold')
        ax.text(cx, 0.85, col_text, ha='left', va='center', color='#cbd5e1', fontsize=7.2)

    # Connecting arrow to Bottom layer
    ax.annotate('', xy=(4.85, 2.05), xytext=(4.85, 2.25),
                arrowprops=dict(arrowstyle="->", color='#10b981', lw=2.0))

    plt.tight_layout()
    out_file = OUT_DIR / "DODAI_OS_System_Architecture.png"
    plt.savefig(out_file, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {out_file}")

def generate_agent_workflow():
    fig, ax = plt.subplots(figsize=(14, 8.5), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # Background canvas
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')

    # Header
    ax.text(7.0, 8.15, "DODAI OS — AUTONOMOUS AGENTIC EXECUTION WORKFLOW & VERIFICATION CYCLE",
            ha='center', va='center', color='#38bdf8', fontsize=15, fontweight='bold')
    ax.text(7.0, 7.85, "Goal Decomposition • DAG Execution • Independent Ground-Truth Verification • Self-Healing Recovery",
            ha='center', va='center', color='#94a3b8', fontsize=10)

    # Workflow Steps across grid
    steps = [
        # (x, y, w, h, step_title, role_title, details, border_color)
        (0.6, 5.0, 2.7, 2.4, "STEP 1: INGESTION & INTENT", "Perception & Classification",
         "• Natural Language Voice / Text\n• Vosk FST -> Faster-Whisper\n• Phonetic Typo Tolerance\n• Intent Classification:\n  -> Direct Fast-Path (<5ms)\n  -> Agentic Multi-Step Goal", "#38bdf8"),
        
        (3.8, 5.0, 2.7, 2.4, "STEP 2: GOAL DECOMPOSITION", "Planner Agent",
         "• Objective Analysis\n• Sub-Goal Formulation\n• DAG Construction (Tasks)\n• Dependency Mapping (`depends_on`)\n• Agent Assignment (Linux/Dev/Tool)\n• Permission Validation (Level 1-4)", "#818cf8"),
        
        (7.0, 5.0, 2.9, 2.4, "STEP 3: AUTONOMOUS EXECUTION", "Specialized Agents",
         "• Linux Intel Agent (/proc vitals)\n• Developer Agent (Scaffold/Write)\n• Research Agent (Web/Synthesis)\n• Tool Execution Agent (105 Tools)\n• Workspace Sandbox Containment\n• Structured Artifact Output", "#34d399"),
        
        (10.4, 5.0, 3.0, 2.4, "STEP 4: VERIFICATION GATE", "Verifier Agent (Independent)",
         "• Architectural Separation Gate\n• Physical File Verification\n• Exit Code & Stderr Inspection\n• Unit Test Runner (pytest pass)\n• Success / Failure Certification\n• Artifact Integrity Validation", "#fbbf24"),

        (3.8, 1.4, 3.8, 2.6, "STEP 5: RECOVERY & SELF-HEALING", "Recovery Agent (Bounded)",
         "• Activated on Task Failure\n• Maximum 2 Bounded Retries\n• Root Cause Error Analysis\n• Alternative Strategy Synthesis\n• Dynamic Plan Reconstruction\n• Prevents Infinite Loops & Plan Drift", "#f87171"),

        (8.5, 1.4, 4.9, 2.6, "STEP 6: COMPLETION & MEMORY", "Supervisor & Retention",
         "• Final Goal Verification Synthesis\n• 7-Day Rolling Memory Episode Commit\n• Immutable Audit Event Logged\n• Natural Spoken Output (Piper Neural TTS)\n• Glass Card UI Real-Time Update\n• Ground-Truth Artifact Delivery", "#10b981")
    ]

    for x, y, w, h, step_title, role_title, details, border in steps:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    facecolor='#1e293b', edgecolor=border, linewidth=1.6)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.28, step_title, ha='center', va='center', color=border, fontsize=9.5, fontweight='bold')
        ax.text(x + w/2, y + h - 0.58, role_title, ha='center', va='center', color='#cbd5e1', fontsize=8.2, fontstyle='italic')
        ax.text(x + 0.15, y + (h - 0.75)/2, details, ha='left', va='center', color='#f8fafc', fontsize=7.6, linespacing=1.35)

    # Arrows between Top Steps
    ax.annotate('', xy=(3.75, 6.2), xytext=(3.35, 6.2), arrowprops=dict(arrowstyle="->", color='#38bdf8', lw=2.2))
    ax.annotate('', xy=(6.95, 6.2), xytext=(6.55, 6.2), arrowprops=dict(arrowstyle="->", color='#818cf8', lw=2.2))
    ax.annotate('', xy=(10.35, 6.2), xytext=(9.95, 6.2), arrowprops=dict(arrowstyle="->", color='#34d399', lw=2.2))

    # Path from Step 4 (Verifier) -> If PASS -> Step 6 (Completion)
    ax.annotate('VERIFIED: PASS', xy=(11.5, 4.05), xytext=(11.5, 4.95),
                arrowprops=dict(arrowstyle="->", color='#10b981', lw=2.2),
                ha='center', va='center', color='#10b981', fontsize=8.5, fontweight='bold')

    # Path from Step 4 (Verifier) -> If FAIL -> Step 5 (Recovery)
    ax.annotate('FAILURE DETECTED', xy=(5.7, 4.05), xytext=(10.8, 4.95),
                arrowprops=dict(arrowstyle="->", color='#f87171', lw=2.0, linestyle='--'),
                ha='center', va='center', color='#f87171', fontsize=8.5, fontweight='bold')

    # Path from Step 5 (Recovery) -> Retry to Step 3 (Execution)
    ax.annotate('REFINED PLAN (Retry <= 2)', xy=(8.0, 4.95), xytext=(5.7, 4.05),
                arrowprops=dict(arrowstyle="->", color='#fbbf24', lw=2.0, linestyle=':'),
                ha='center', va='center', color='#fbbf24', fontsize=8.2, fontweight='bold')

    # Path from Step 5 (Recovery Max Exceeded) -> Step 6 (Report Failure with Truthful Bounds)
    ax.annotate('MAX RETRIES EXCEEDED', xy=(8.45, 2.7), xytext=(7.65, 2.7),
                arrowprops=dict(arrowstyle="->", color='#f87171', lw=1.8),
                ha='center', va='center', color='#f87171', fontsize=7.8, fontweight='bold')

    plt.tight_layout()
    out_file = OUT_DIR / "DODAI_OS_Agent_Workflow.png"
    plt.savefig(out_file, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {out_file}")

if __name__ == "__main__":
    generate_system_architecture()
    generate_agent_workflow()

