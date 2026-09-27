"""Create a clean PDF copy of the submission report."""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

ROOT = Path(__file__).resolve().parents[1]
run = json.loads((ROOT / "data" / "live_run.json").read_text(encoding="utf-8"))
output = ROOT / "docs" / "Agentic_RFP_Evaluation_Submission.pdf"
output.parent.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                          fontSize=19, leading=24, textColor=colors.HexColor("#142632"),
                          spaceAfter=13))
styles.add(ParagraphStyle(name="ReportBody", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=9.2, leading=13.2, spaceAfter=8))
styles.add(ParagraphStyle(name="ReportHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
                          fontSize=11.5, leading=15, textColor=colors.HexColor("#174E69"),
                          spaceBefore=12, spaceAfter=5))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=8, leading=11, spaceAfter=6))

story = []
def p(text, style="ReportBody"):
    story.append(Paragraph(text, styles[style]))
def h(text):
    p(text, "ReportHeading")
def t(headers, rows, widths):
    data = [[Paragraph(str(x), styles["Small"]) for x in headers]]
    data += [[Paragraph(str(x), styles["Small"]) for x in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEAF0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#142632")),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#CFD9DE")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 7))

p("Agentic RFP Evaluation and Supplier Ranking", "ReportTitle")
p("Project submission report | 27 September 2026", "Small")
p("This project evaluates supplier proposals for a fictional university procurement request. It reads each PDF, asks a language model for criterion scores with document evidence, checks the model response, and then uses fixed Python rules to calculate scores and rank suppliers. A completed four-supplier run, validation example, source code, and fictional proposals are included.")
h("What the application delivers")
t(["Requirement", "Implemented behavior"], [
    ("Criteria", "SQLite stores criterion names, descriptions, weights, maximum scores, and active status. The editor enforces a 100% active total."),
    ("Supplier input", "Streamlit accepts multiple PDFs, supplier names, dates, and experience ratings."),
    ("AI evaluation", "Gemini or Ollama Cloud receives extracted text and current criteria; it returns JSON scores, reasons, evidence, risks, and a summary."),
    ("Validation", "Missing or invalid scores become zero, out-of-range scores are clipped, and corrections appear as warnings."),
    ("Ranking and records", "Python computes all measures and tie breaks; SQLite saves a full batch under one run ID; JSON export is available."),
], [100, 380])
h("System flow")
p("The orchestrator loads the active criteria immediately before a batch. For each supplier, it extracts selectable PDF text, builds a prompt from the current criteria, calls the selected model, and normalizes the JSON response. After all suppliers are assessed, the scoring module finds criterion benchmarks, computes the peer measures, sorts the suppliers, and saves the completed result. The interface shows the leaderboard, criterion details, evidence, warnings, and a download button.")
h("Scoring and ranking rules")
t(["Measure", "Calculation"], [
    ("Absolute score", "Sum of (criterion score / maximum score) x weight"),
    ("Benchmark and gap", "Highest valid criterion score in the batch; supplier score minus benchmark"),
    ("Relative performance", "Supplier score / benchmark x 100; use 100% when the benchmark is zero"),
    ("Peer Performance Index", "Weighted average of criterion relative percentages"),
    ("Final rank", "Higher PPI, earlier date, higher experience rating, supplier name A to Z"),
], [135, 345])
story.append(PageBreak())
h("Completed Gemini evaluation")
p("Four fictional two-page proposals were evaluated with Gemini 2.5 Flash. The model produced criterion-level judgments; Python calculated the following final values.")
t(["Rank", "Supplier", "Absolute score", "PPI"], [
    (s["final_rank"], s["supplier_name"], f"{s['absolute_score']:.1f}", f"{s['ppi']:.4f}")
    for s in run["suppliers"]
], [48, 195, 115, 122])
p("Apex Systems ranked first with strong architecture and security detail. NexaWorks followed with a strong implementation plan and support offer. Orbit Digital had strong references but less integration detail. BrightPath Tech had the lowest price but limited security detail. The model returned a malformed risks list for BrightPath; the validator recorded a warning and retained the valid criterion scores.")
h("Validation and testing")
p("The separate validation example includes an out-of-range criterion score that is corrected to zero. Four automated tests pass. They cover missing and malformed results, score clipping, weighted scores and peer measures, all tie breaks, a zero benchmark, and complete SQLite persistence. The local Streamlit interface was opened and checked for the criteria view, evaluation form, sample leaderboard, scorecards, and export control.")
h("Project files and demonstration")
p("The repository contains the Streamlit application, Python modules, requirements file, database seed script, four proposal PDFs, the completed JSON export, the validation example, and tests. To start locally, install requirements, run the seed script, and launch streamlit run streamlit_app.py. The Sample run tab displays the completed evaluation without a key. The hosted app has a Gemini key configured in Streamlit secrets, so a new batch can be evaluated without entering a key.")
p("Public repository: https://github.com/kvlnarasimharao/agentic-rfp-evaluation", "Small")
p("Live application: https://rfp-evaluation-kvlnarasimharao.streamlit.app/", "Small")
h("Technical references")
p("Google AI for Developers, Gemini generateContent API: https://ai.google.dev/api/generate-content", "Small")
p("Streamlit, Deploy your app on Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy", "Small")
p("Streamlit, Secrets management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management", "Small")
story.append(PageBreak())
h("Application screenshots")
p("Completed four-supplier Gemini evaluation in the Sample run tab.")
story.append(Image(str(ROOT / "docs" / "screenshots" / "leaderboard.jpg"), width=480, height=257))
story.append(Spacer(1, 15))
p("Active criteria and weights loaded from SQLite.")
story.append(Image(str(ROOT / "docs" / "screenshots" / "criteria.jpg"), width=480, height=254))

def footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64737C"))
    canvas.drawString(57, 32, "Agentic RFP Evaluation and Supplier Ranking")
    canvas.drawRightString(A4[0] - 57, 32, str(doc.page))

SimpleDocTemplate(str(output), pagesize=A4, leftMargin=57, rightMargin=57,
                  topMargin=52, bottomMargin=50).build(story, onFirstPage=footer, onLaterPages=footer)
print(output)
