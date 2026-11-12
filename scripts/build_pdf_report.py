#!/usr/bin/env python3
"""
VOID Agentic OS — Complete Technical Report PDF Builder
Generates a polished, academic and engineering publication-grade PDF report
using Chromium headless rendering from semantic HTML with embedded SVG diagrams
and verified screenshots.
"""

import os
import sys
import subprocess
from pathlib import Path
import markdown

REPORTS_DIR = Path("/run/media/prakash/TR_39/VOID/docs/reports")
ASSETS_DIR = REPORTS_DIR / "assets"
MD_FILE = REPORTS_DIR / "VOID_Complete_Technical_Project_Report.md"
HTML_FILE = REPORTS_DIR / "VOID_Complete_Technical_Project_Report.html"
PDF_FILE = REPORTS_DIR / "VOID_Complete_Technical_Project_Report.pdf"
HOME_PDF = Path("/home/prakash/VOID_Complete_Technical_Project_Report.pdf")

def read_svg(name: str) -> str:
    path = ASSETS_DIR / name
    if path.exists():
        return f'<div class="diagram-container"><div class="diagram-caption">Figure: {name.replace(".svg", "").replace("_", " ").title()}</div>{path.read_text(encoding="utf-8")}</div>'
    return ""

def read_img_base64(name: str) -> str:
    import base64
    path = ASSETS_DIR / name
    if path.exists():
        b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f'<div class="screenshot-box"><img src="data:image/png;base64,{b64}" class="screenshot-img"/><div class="screenshot-caption">{name.replace(".png", "").replace("_", " ").title()}</div></div>'
    return ""

def build_html():
    raw_md = MD_FILE.read_text(encoding="utf-8")
    
    # Insert diagram hooks before conversion
    diagram_inserts = {
        "# CHAPTER 7: Original VOID Architecture": read_svg("06_voice_pipeline.svg") + read_svg("02_original_vs_upgraded.svg"),
        "# CHAPTER 10: New System Architecture": read_svg("01_system_architecture.svg"),
        "# CHAPTER 11: Multi-Agent Architecture": read_svg("03_multi_agent_dag.svg"),
        "# CHAPTER 13: Agent Orchestration Engine": read_svg("04_orchestration_lifecycle.svg"),
        "# CHAPTER 15: Tool Integration": read_svg("05_tool_execution_architecture.svg"),
        "# CHAPTER 16: Real-World Workflow Demonstrations": read_svg("11_autonomous_development_workflow.svg"),
        "# CHAPTER 17: Local AI Architecture": read_svg("07_provider_architecture.svg"),
        "# CHAPTER 19: Memory and Context Management": read_svg("08_memory_architecture.svg"),
        "# CHAPTER 20: Permission and Security Architecture": read_svg("09_permission_approval_workflow.svg") + read_svg("12_failure_recovery_workflow.svg"),
        "# CHAPTER 21: VOID Glass Flow UI": read_svg("10_ui_agent_communication.svg") + f'<div class="screenshot-gallery">{read_img_base64("globe_idle.png")}{read_img_base64("globe_thinking.png")}{read_img_base64("globe_executing.png")}{read_img_base64("glass_effect_verified.png")}{read_img_base64("glass_expanded_verified.png")}</div>',
    }

    modified_md = raw_md
    for marker, diag_html in diagram_inserts.items():
        if marker in modified_md:
            modified_md = modified_md.replace(marker, f"{marker}\n\n{diag_html}\n\n")

    body_html = markdown.markdown(modified_md, extensions=['tables', 'fenced_code', 'toc'])

    css = """
    @page {
        size: A4;
        margin: 18mm 14mm 18mm 14mm;
        @bottom-right {
            content: "Page " counter(page);
            font-size: 9pt;
            color: #64748b;
            font-family: 'Inter', system-ui, sans-serif;
        }
        @top-right {
            content: "VOID Agentic OS — Master Technical Report";
            font-size: 8pt;
            color: #94a3b8;
            font-family: 'Inter', system-ui, sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    }

    *, *:before, *:after {
        box-sizing: border-box;
    }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #1e293b;
        background: #ffffff;
        line-height: 1.6;
        font-size: 10pt;
        margin: 0;
        padding: 0;
    }

    h1 {
        font-size: 18pt;
        font-weight: 800;
        color: #0f172a;
        border-bottom: 2px solid #0284c7;
        padding-bottom: 6px;
        margin-top: 30px;
        margin-bottom: 14px;
        page-break-before: always;
        letter-spacing: -0.3px;
    }

    h1:first-of-type {
        page-break-before: avoid;
    }

    h2 {
        font-size: 13pt;
        font-weight: 700;
        color: #0369a1;
        margin-top: 22px;
        margin-bottom: 8px;
    }

    h3 {
        font-size: 11pt;
        font-weight: 600;
        color: #334155;
        margin-top: 16px;
        margin-bottom: 6px;
    }

    p {
        margin-top: 0;
        margin-bottom: 10px;
        text-align: justify;
    }

    ul, ol {
        margin-top: 0;
        margin-bottom: 12px;
        padding-left: 20px;
    }

    li {
        margin-bottom: 4px;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 14px 0 20px 0;
        font-size: 8.5pt;
        page-break-inside: auto;
    }

    tr {
        page-break-inside: avoid;
        page-break-after: auto;
    }

    thead {
        display: table-header-group;
    }

    th {
        background: #0f172a;
        color: #ffffff;
        font-weight: 600;
        text-align: left;
        padding: 7px 9px;
        border: 1px solid #334155;
    }

    td {
        padding: 6px 9px;
        border: 1px solid #cbd5e1;
        vertical-align: middle;
    }

    tbody tr:nth-child(even) {
        background-color: #f8fafc;
    }

    code {
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace;
        font-size: 8.5pt;
        background: #f1f5f9;
        color: #0f172a;
        padding: 1px 4px;
        border-radius: 3px;
        border: 1px solid #e2e8f0;
    }

    pre {
        background: #0f172a;
        color: #f8fafc;
        padding: 12px 14px;
        border-radius: 6px;
        overflow-x: auto;
        font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
        font-size: 8.5pt;
        line-height: 1.45;
        margin: 12px 0 16px 0;
        page-break-inside: avoid;
    }

    pre code {
        background: transparent;
        color: inherit;
        padding: 0;
        border: none;
    }

    blockquote {
        margin: 12px 0;
        padding: 10px 14px;
        background: #f0f9ff;
        border-left: 4px solid #0284c7;
        color: #0369a1;
        font-style: italic;
    }

    .diagram-container {
        margin: 18px auto;
        text-align: center;
        page-break-inside: avoid;
        background: #0f172a;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .diagram-container svg {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 0 auto;
    }

    .diagram-caption {
        font-size: 9pt;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .screenshot-gallery {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: center;
        margin: 16px 0;
        page-break-inside: avoid;
    }

    .screenshot-box {
        text-align: center;
        background: #1e293b;
        padding: 8px;
        border-radius: 8px;
        border: 1px solid #334155;
    }

    .screenshot-img {
        max-height: 140px;
        border-radius: 4px;
        display: block;
        margin: 0 auto;
    }

    .screenshot-caption {
        font-size: 7.5pt;
        color: #94a3b8;
        margin-top: 4px;
        font-weight: 500;
    }

    .cover-page {
        page-break-after: always;
        text-align: center;
        padding-top: 60px;
    }

    .cover-title {
        font-size: 28pt;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }

    .cover-subtitle {
        font-size: 14pt;
        font-weight: 600;
        color: #0284c7;
        margin-bottom: 24px;
    }

    .cover-badge {
        display: inline-block;
        background: #e0f2fe;
        color: #0369a1;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 10pt;
        font-weight: 700;
        margin-bottom: 40px;
    }

    .cover-meta {
        margin: 40px auto;
        max-width: 500px;
        text-align: left;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px 24px;
        font-size: 10pt;
    }

    .cover-meta table {
        margin: 0;
    }

    .cover-meta td {
        border: none;
        padding: 4px 6px;
    }
    """

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VOID Agentic OS — Complete Technical Report</title>
    <style>{css}</style>
</head>
<body>
    {body_html}
</body>
</html>"""

    HTML_FILE.write_text(full_html, encoding='utf-8')
    print(f"Generated HTML report: {HTML_FILE} ({len(full_html)} bytes)")

def convert_to_pdf():
    cmd = [
        "chromium-browser",
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        f"--print-to-pdf={PDF_FILE}",
        str(HTML_FILE)
    ]
    print(f"Rendering PDF with Chromium: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if res.returncode == 0 and PDF_FILE.exists():
        print(f"Successfully generated PDF: {PDF_FILE} ({PDF_FILE.stat().st_size} bytes)")
        import shutil
        shutil.copy2(PDF_FILE, HOME_PDF)
        print(f"Copied PDF to user home: {HOME_PDF}")
    else:
        print(f"PDF generation failed! Returncode={res.returncode}\n{res.stderr}\n{res.stdout}")
        sys.exit(1)

if __name__ == "__main__":
    build_html()
    convert_to_pdf()

