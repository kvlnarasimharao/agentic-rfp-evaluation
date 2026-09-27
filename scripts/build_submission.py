"""Build the Word submission report from the verified live run."""
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
result = json.loads((ROOT / "data" / "live_run.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "Agentic_RFP_Evaluation_Submission.docx"
OUT.parent.mkdir(parents=True, exist_ok=True)

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(.75)
sec.bottom_margin = Inches(.7)
sec.left_margin = Inches(.85)
sec.right_margin = Inches(.85)

styles = doc.styles
for name in ("Normal", "Title", "Heading 1", "Heading 2"):
    styles[name].font.name = "Aptos"
styles["Normal"].font.size = Pt(9.5)
styles["Normal"].paragraph_format.space_after = Pt(6)
styles["Normal"].paragraph_format.line_spacing = 1.12
styles["Title"].font.size = Pt(21)
styles["Title"].font.bold = True
styles["Title"].font.color.rgb = RGBColor(20, 38, 50)
styles["Title"].paragraph_format.space_after = Pt(12)
styles["Heading 1"].font.size = Pt(12)
styles["Heading 1"].font.bold = True
styles["Heading 1"].font.color.rgb = RGBColor(23, 78, 105)
styles["Heading 1"].paragraph_format.space_before = Pt(12)
styles["Heading 1"].paragraph_format.space_after = Pt(5)
styles["Heading 2"].font.size = Pt(10)
styles["Heading 2"].font.bold = True
styles["Heading 2"].font.color.rgb = RGBColor(23, 78, 105)


def paragraph(text="", style=None):
    return doc.add_paragraph(text, style=style)


def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Shading Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, head in enumerate(headers):
        t.rows[0].cells[i].text = head
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if widths:
        for row in t.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(1)
                for run in p.runs:
                    run.font.size = Pt(8.5)
    paragraph()
    return t


paragraph("Agentic RFP Evaluation and Supplier Ranking", "Title")
paragraph("Project submission report | 27 September 2026")
paragraph("This project evaluates supplier proposals for a fictional university procurement request. It reads each PDF, asks a language model for criterion scores with document evidence, checks the model response, and then uses fixed Python rules to calculate scores and rank suppliers. A completed four-supplier run, validation example, source code, and fictional proposals are included.")

doc.add_heading("What the application delivers", level=1)
table(["Requirement", "Implemented behavior"], [
    ("Criteria", "SQLite stores criterion names, descriptions, weights, maximum scores, and active status. The editor enforces a 100% active total."),
    ("Supplier input", "Streamlit accepts multiple PDFs, supplier names, dates, and experience ratings."),
    ("AI evaluation", "Gemini or Ollama Cloud receives extracted text and the current criteria; it returns JSON scores, reasons, evidence, risks, and a summary."),
    ("Validation", "Missing or invalid scores become zero, out-of-range scores are clipped, and corrections appear as warnings."),
    ("Ranking and records", "Python computes all measures and tie breaks; SQLite saves a full batch under one run ID; JSON export is available."),
], [1.35, 5.1])

doc.add_heading("System flow", level=1)
paragraph("The orchestrator loads the active criteria immediately before a batch. For each supplier, it extracts selectable PDF text, builds a prompt from the current criteria, calls the selected model, and normalizes the JSON response. After all suppliers are assessed, the scoring module finds criterion benchmarks, computes the peer measures, sorts the suppliers, and saves the completed result. The interface shows the leaderboard, criterion details, evidence, warnings, and a download button.")

doc.add_heading("Scoring and ranking rules", level=1)
table(["Measure", "Calculation"], [
    ("Absolute score", "Sum of (criterion score / maximum score) x weight"),
    ("Benchmark and gap", "Highest valid criterion score in the batch; supplier score minus benchmark"),
    ("Relative performance", "Supplier score / benchmark x 100; use 100% when the benchmark is zero"),
    ("Peer Performance Index", "Weighted average of criterion relative percentages"),
    ("Final rank", "Higher PPI, earlier date, higher experience rating, supplier name A to Z"),
], [1.8, 4.65])

doc.add_page_break()
doc.add_heading("Completed Gemini evaluation", level=1)
paragraph("Four fictional two-page proposals were evaluated with Gemini 2.5 Flash. The model produced criterion-level judgments; Python calculated the following final values.")
table(["Rank", "Supplier", "Absolute score", "PPI"], [
    (s["final_rank"], s["supplier_name"], f"{s['absolute_score']:.1f}", f"{s['ppi']:.4f}")
    for s in result["suppliers"]
], [.65, 2.2, 1.5, 1.5])
paragraph("Apex Systems ranked first with strong architecture and security detail. NexaWorks followed with a strong implementation plan and support offer. Orbit Digital had strong references but less integration detail. BrightPath Tech had the lowest price but limited security detail. The model returned a malformed risks list for BrightPath; the validator recorded a warning and retained the valid criterion scores.")

doc.add_heading("Validation and testing", level=1)
paragraph("The separate validation example includes an out-of-range criterion score that is corrected to zero. Four automated tests pass. They cover missing and malformed results, score clipping, weighted scores and peer measures, all tie breaks, a zero benchmark, and complete SQLite persistence. The local Streamlit interface was opened and checked for the criteria view, evaluation form, sample leaderboard, scorecards, and export control.")

doc.add_heading("Project files and demonstration", level=1)
paragraph("The repository contains the Streamlit application, Python modules, requirements file, database seed script, four proposal PDFs, the completed JSON export, the validation example, and tests. To start locally, install requirements, run the seed script, and launch `streamlit run streamlit_app.py`. The Sample run tab displays the completed evaluation without a key. The hosted app has a Gemini key configured in Streamlit secrets, so a new batch can be evaluated without entering a key.")
paragraph("Public repository: https://github.com/kvlnarasimharao/agentic-rfp-evaluation")
paragraph("Live application: https://rfp-evaluation-kvlnarasimharao.streamlit.app/")

doc.add_heading("Technical references", level=1)
paragraph("Google AI for Developers, Gemini generateContent API: https://ai.google.dev/api/generate-content")
paragraph("Streamlit, Deploy your app on Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy")
paragraph("Streamlit, Secrets management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management")

doc.add_page_break()
doc.add_heading("Application screenshots", level=1)
paragraph("Completed four-supplier Gemini evaluation in the Sample run tab.")
doc.add_picture(str(ROOT / "docs" / "screenshots" / "leaderboard.jpg"), width=Inches(6.65))
paragraph("Active criteria and weights loaded from SQLite.")
doc.add_picture(str(ROOT / "docs" / "screenshots" / "criteria.jpg"), width=Inches(6.65))

footer = sec.footer.paragraphs[0]
footer.text = "Agentic RFP Evaluation and Supplier Ranking"
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.runs[0].font.size = Pt(8)
footer.runs[0].font.color.rgb = RGBColor(90, 104, 112)

doc.save(OUT)
print(OUT)
