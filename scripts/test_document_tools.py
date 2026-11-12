import docx
import openpyxl
from pathlib import Path
import urllib.parse
import os
import time

DOCS_DIR = Path("/home/prakash/Documents")
REPORTS_DIR = DOCS_DIR / "Reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def test_draft_docx(title: str, sections: list[dict], filename: str = "") -> str:
    doc = docx.Document()
    doc.add_heading(title, level=0)
    p_meta = doc.add_paragraph()
    p_meta.add_run(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} | Author: Prakash (via VOID AI)").italic = True
    
    for sec in sections:
        h = sec.get("heading", "")
        if h:
            doc.add_heading(h, level=1)
        body = sec.get("content", "")
        if body:
            lines = body.split("\n")
            for line in lines:
                l = line.strip()
                if l.startswith("- ") or l.startswith("* "):
                    doc.add_paragraph(l[2:], style="List Bullet")
                elif l:
                    doc.add_paragraph(l)
        
        tbl_data = sec.get("table")
        if tbl_data and isinstance(tbl_data, dict):
            headers = tbl_data.get("headers", [])
            rows = tbl_data.get("rows", [])
            if headers and rows:
                tbl = doc.add_table(rows=len(rows)+1, cols=len(headers))
                tbl.style = "Table Grid"
                for c_idx, h_text in enumerate(headers):
                    cell = tbl.cell(0, c_idx)
                    cell.text = str(h_text)
                    for p in cell.paragraphs:
                        for run in p.runs:
                            run.font.bold = True
                for r_idx, r_data in enumerate(rows):
                    for c_idx, val in enumerate(r_data):
                        tbl.cell(r_idx + 1, c_idx).text = str(val)

    safe_name = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "document"
    out = (REPORTS_DIR / f"{safe_name}.docx") if not filename else Path(filename)
    doc.save(out)
    return str(out)

def test_draft_xlsx(title: str, headers: list[str], rows: list[list], sheet_name: str = "Data", filename: str = "") -> str:
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name or "Data"

    # Header styling
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    hdr_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    center = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = center
        cell.border = thin_border

    for r_data in rows:
        ws.append(r_data)
        r_num = ws.max_row
        for col_idx in range(1, len(r_data) + 1):
            cell = ws.cell(row=r_num, column=col_idx)
            cell.border = thin_border

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    safe_name = "".join(c for c in title if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "spreadsheet"
    out = (REPORTS_DIR / f"{safe_name}.xlsx") if not filename else Path(filename)
    wb.save(out)
    return str(out)

# Run tests
docx_path = test_draft_docx("AI Market Analysis 2026", [
    {"heading": "Executive Summary", "content": "Autonomous desktop AI assistants are rapidly evolving into proactive companions."},
    {"heading": "Key Performance Metrics", "table": {
        "headers": ["Model", "Context Length", "Latency", "Status"],
        "rows": [["lfm3-omni:2b", "4096", "45ms", "Resident"], ["llama3.2:3b", "8192", "110ms", "Standby"]]
    }}
])
print("DOCX Path:", docx_path, "Exists:", Path(docx_path).exists())

xlsx_path = test_draft_xlsx("System Performance Log", ["Component", "Usage", "Threshold", "Status"], [
    ["CPU Load", "12%", "85%", "Optimal"],
    ["RAM Memory", "4.2 GB / 16 GB", "90%", "Healthy"],
    ["NVMe SSD", "45% used", "95%", "Clean"]
])
print("XLSX Path:", xlsx_path, "Exists:", Path(xlsx_path).exists())

# Cleanup
Path(docx_path).unlink(missing_ok=True)
Path(xlsx_path).unlink(missing_ok=True)
print("Test completed successfully.")
