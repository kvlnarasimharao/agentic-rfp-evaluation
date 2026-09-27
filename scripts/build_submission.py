"""Build the detailed Word submission report from the published project data."""
import json
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RUN = json.loads((ROOT / "data" / "live_run.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "Agentic_RFP_Evaluation_Submission.docx"
BLACK = RGBColor(0, 0, 0)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin, sec.bottom_margin = Inches(.73), Inches(.72)
sec.left_margin, sec.right_margin = Inches(.78), Inches(.78)
for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "List Bullet"):
    style = doc.styles[name]
    style.font.name = "Aptos"
    style.font.color.rgb = BLACK
normal = doc.styles["Normal"]
normal.font.size = Pt(10.5)
normal.paragraph_format.space_after = Pt(7)
normal.paragraph_format.line_spacing = 1.13
title = doc.styles["Title"]
title.font.size, title.font.bold = Pt(20), True
title.paragraph_format.space_after = Pt(8)
subtitle = doc.styles["Subtitle"]
subtitle.font.size = Pt(10)
subtitle.paragraph_format.space_after = Pt(13)
for name, size, before, after in (("Heading 1", 13, 15, 6), ("Heading 2", 11, 10, 4)):
    style = doc.styles[name]
    style.font.size, style.font.bold = Pt(size), True
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.keep_with_next = True

def p(text):
    return doc.add_paragraph(text)

def h(text, level=1):
    return doc.add_heading(text, level=level)

def bullet(text):
    return doc.add_paragraph(text, style="List Bullet")

def grid(headers, rows, widths, centered=()):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement("w:" + side)
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "4")
        edge.set(qn("w:color"), "D9D9D9")
        borders.append(edge)
    t._tbl.tblPr.append(borders)
    for i, value in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = str(value)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "F0F0F0")
        cell._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
    for r, row in enumerate(t.rows):
        for i, cell in enumerate(row.cells):
            cell.width = Inches(widths[i])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for para in cell.paragraphs:
                para.paragraph_format.space_before = Pt(2)
                para.paragraph_format.space_after = Pt(2)
                para.paragraph_format.line_spacing = 1.05
                if i in centered:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.name = "Aptos"
                    run.font.size = Pt(8.6)
                    run.font.color.rgb = BLACK
                    if r == 0:
                        run.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t

title_paragraph = doc.add_paragraph("Agentic RFP Evaluation and Supplier Ranking", style="Title")
for property_set in (doc.styles["Title"]._element.get_or_add_pPr(), title_paragraph._p.get_or_add_pPr()):
    for border in property_set.findall(qn("w:pBdr")):
        property_set.remove(border)
doc.add_paragraph("Prepared by kvl.narasimharao", style="Subtitle")
p("This report presents a working application that compares supplier responses to a request for proposal. It explains how proposal PDFs are read, how criterion scores are checked, how Python calculates peer results and final ranks, and what the four-supplier demonstration produced. The repository includes the running application, sample proposals, saved results, tests, and screenshots.")

h("Project purpose")
p("A procurement team must review several supplier proposals against the same requirements. Manual reading makes the comparison slow and can lead to inconsistent scoring. This application produces an evidence-linked scorecard for each proposal and applies one published set of arithmetic and ranking rules to every supplier.")
p("The language model judges proposal content and supplies criterion scores, reasons, and evidence. Python validates that response, calculates every comparison measure, and assigns the final order. The model does not set benchmarks or ranks.")

h("What the application does")
for item in (
    "Loads active criteria and weights from SQLite and displays them in the Criteria tab.",
    "Accepts at least two supplier PDFs with supplier name, submission date, and historical experience rating.",
    "Evaluates each PDF independently against the criteria active at the start of the batch.",
    "Corrects missing, malformed, duplicate, and out-of-range model results and records warnings.",
    "Calculates weighted scores, peer benchmarks, gaps, relative percentages, PPI, and final ranks in Python.",
    "Saves the full batch under one run ID and offers leaderboard, scorecards, and JSON download.",
):
    bullet(item)

h("Submission requirements and included files")
p("The source brief is Agentic_RFP_Evaluation_Mini_Project.pdf, section 10, Submission Requirements. Every requested item is present in the public repository or at the live application link.")
grid(["Required item", "Included deliverable"], [
    ("Complete source code", "streamlit_app.py, rfp/, scripts/, tests/, and requirements.txt in the public repository"),
    ("SQLite setup", "scripts/seed_db.py and rfp/database.py create and seed five sample criteria"),
    ("Four supplier PDFs", "data/proposals/apex_systems.pdf, brightpath_tech.pdf, nexaworks.pdf, orbit_digital.pdf"),
    ("Public deployed app", "https://rfp-evaluation-kvlnarasimharao.streamlit.app/"),
    ("README", "README.md contains setup, architecture, formulas, assumptions, and screenshots"),
    ("Completed JSON export", "data/live_run.json stores one completed four-supplier RFP run"),
    ("Short demonstration", "Sample run shows a successful Gemini result and a separate validation example"),
], [2.0, 4.9])

doc.add_page_break()
h("Source code structure")
grid(["Path", "Responsibility"], [
    ("streamlit_app.py", "Upload form, criteria editor, leaderboard, detailed scorecards, saved runs, export"),
    ("rfp/evaluation.py", "PDF extraction, dynamic prompt, model request, response normalization"),
    ("rfp/scoring.py", "Weighted arithmetic, peer comparison, deterministic ranking"),
    ("rfp/workflow.py", "Ordered batch evaluation and persistence"),
    ("rfp/database.py", "SQLite schema, criteria operations, completed run records"),
    ("scripts/ and tests/", "Sample generation, database seed, live run, document build, automated checks"),
], [1.8, 5.1])

h("System workflow")
p("The user uploads the proposals and enters metadata. The orchestrator reloads active criteria, reads text from each PDF, and builds a prompt from those database rows. Gemini or Ollama Cloud returns a JSON assessment for one supplier at a time. The validator creates a complete, bounded scorecard even when fields are missing or malformed. Once all suppliers have scorecards, Python calculates the peer measures and sorts the batch. The complete result is committed to SQLite and shown in Streamlit.")
grid(["Stage", "Input", "Output"], [
    ("Setup", "SQLite criteria", "Active criteria with total weight of 100%"),
    ("Evaluate", "PDF text and active criteria", "Scores, reasons, evidence, risks, summary"),
    ("Validate", "Model JSON", "Complete scorecards and warnings"),
    ("Compare", "Validated supplier scores", "Benchmarks, gaps, relative results, PPI"),
    ("Finish", "Peer results and metadata", "Ranks, saved run, leaderboard, JSON export"),
], [1.05, 2.55, 3.3])

h("Evaluation criteria")
p("Criteria are stored in SQLite rather than fixed in the prompt. The editor allows activation, deactivation, and weight changes. A batch cannot start unless active weights total 100%. Each criterion uses a maximum score of 10 in the included demonstration.")
grid(["Criterion", "Weight", "What is inspected"], [
    (c["name"], f"{c['weight']:g}%", c["description"]) for c in RUN["criteria"]
], [2.0, .75, 4.15], centered=(1,))

h("Scoring and tie breaks")
p("For each criterion, the absolute contribution is the validated score divided by its maximum score, multiplied by the criterion weight. The absolute score is the sum of those contributions. The benchmark is the highest validated score for that criterion among suppliers in the batch. A supplier's gap is its score minus the benchmark, so a benchmark leader has a gap of zero.")
p("Relative performance is supplier score divided by benchmark, multiplied by 100. When every supplier scores zero on a criterion, the benchmark is zero and relative performance is set to 100% for all suppliers on that criterion. PPI is the sum of each relative percentage multiplied by its criterion weight divided by 100. It is calculated before display rounding is applied.")
p("Final sorting is fixed: higher PPI first, then earlier submission date, then higher historical experience rating, then supplier name in ascending alphabetical order. Sequential ranks start at 1 after sorting. Experience affects a tie break only; it does not change criterion or absolute scores.")

h("Worked calculation for Apex Systems")
p("Apex received scores of 9, 9, 7, 9, and 8 out of 10 for the five criteria. Its absolute score is (9/10 × 30) + (9/10 × 20) + (7/10 × 20) + (9/10 × 20) + (8/10 × 10) = 85. The benchmark for each criterion in the four-supplier run was 9. Apex therefore had relative results of 100%, 100%, 77.7778%, 100%, and 88.8889%. Applying the five weights gives a PPI of 94.4445 after display rounding.")

h("Model response validation")
p("The evaluator requests valid JSON with one entry per active criterion, including criterion ID, score, explanation, and supporting evidence. The validator uses the database criterion IDs and maximum scores as the source of truth. It applies the following rules before any arithmetic:")
for item in (
    "Invalid JSON or a non-object response becomes an empty assessment; missing criteria receive zero.",
    "Unknown and duplicate criterion IDs are ignored. Missing expected criteria receive zero.",
    "Non-numeric or non-finite scores become zero. Scores outside the range are clipped.",
    "Missing explanations receive a placeholder. Missing evidence is flagged in the warnings.",
    "A malformed risks field becomes an empty list. Every correction is recorded with the supplier name.",
):
    bullet(item)
p("Supplier names must be unique within a batch. Experience ratings must be between 0 and 10. Submission dates are checked before ranking. The application rejects PDFs that contain too little selectable text.")

h("Stored data and output")
p("SQLite has three tables: evaluation_criteria, rfp_runs, and supplier_results. The first stores the editable rubric. The run table stores the creation time, criteria snapshot, warnings, and complete result JSON. The supplier table stores each supplier's metadata, absolute score, PPI, rank, and scorecard. One RFP_RUN_ID connects all suppliers in a batch. The API key is not written to these tables or to the JSON export.")
p("The interface has Evaluate, Criteria, Saved runs, and Sample run tabs. A completed run displays the ranked leaderboard, every criterion's score and evidence, peer comparisons, warnings, and a JSON download. The Sample run tab includes the completed Gemini result and a separate validation example.")

h("Demonstration data")
grid(["Supplier", "PDF file", "Intended difference"], [
    ("Apex Systems", "apex_systems.pdf", "Strong design and security; higher price"),
    ("BrightPath Tech", "brightpath_tech.pdf", "Lowest price and fast timeline; weak compliance detail"),
    ("NexaWorks", "nexaworks.pdf", "Balanced cost; strongest plan and support"),
    ("Orbit Digital", "orbit_digital.pdf", "Strong references; vague integration scope"),
], [1.5, 2.1, 3.3])
p("Four fictional two-page proposals were prepared for the same university procurement request. They differ in architecture, implementation timing, cost, security detail, support, and references. Gemini 2.5 Flash evaluated all four in a completed batch. The table reports Python's final calculations; scores in the five criterion columns are out of 10.")
grid(["Rank", "Supplier", "Tech", "Plan", "Value", "Security", "Support", "Absolute", "PPI"], [
    (s["final_rank"], s["supplier_name"], *[f"{item['score']:g}" for item in s["criteria"]],
     f"{s['absolute_score']:.1f}", f"{s['ppi']:.4f}") for s in RUN["suppliers"]
], [.43, 1.39, .52, .52, .52, .63, .61, .75, .73], centered=(0, 2, 3, 4, 5, 6, 7, 8))
p("Apex Systems ranked first with strong technical and security detail. NexaWorks followed with a strong plan and support offer. Orbit Digital had substantial references but less detail on ERP integration. BrightPath Tech had the lowest price but limited security detail. The model returned a malformed risks field for BrightPath; validation replaced it with an empty list and retained its valid criterion scores.")
p("The saved run ID is " + RUN["rfp_run_id"] + ". The complete result is in data/live_run.json. A separate data/sample_run.json deliberately includes an out-of-range score so the correction path can be demonstrated without a model call.")

h("Testing and verification")
grid(["Check", "Result"], [
    ("Response normalization", "Missing results, duplicate IDs, invalid values, and clipping are covered."),
    ("Scoring and ranking", "Weighted score, peer measures, zero benchmark, and every tie break are covered."),
    ("Persistence", "A complete two-supplier run is saved and loaded from SQLite."),
    ("Application", "The live app opens; Sample run shows four ranks, scorecards, warnings, and JSON download."),
], [1.55, 5.35])
p("All four automated tests passed. The four proposal PDFs were evaluated in one Gemini batch, and the local interface was checked for criteria editing, input, sample results, scorecards, and export. The public Streamlit app was opened and its saved sample run was checked.")

h("Demonstration sequence")
p("Successful run: open the live app and select Sample run, then Live Gemini evaluation. The leaderboard shows four final ranks. Expand Apex Systems to inspect the criterion explanations, supporting evidence, benchmark, gap, and relative percentages. Use Download complete result as JSON to export the saved run.")
p("Validation case: in Sample run, select Validation example. Its deliberately out-of-range criterion score is clipped to zero before scoring, and the warning is shown in Run details. The completed Gemini example also displays a malformed risks-field warning for BrightPath Tech. These cases demonstrate that model output is checked before ranking.")

doc.add_page_break()
h("How to run and present the project")
p("Public repository: https://github.com/kvlnarasimharao/agentic-rfp-evaluation")
p("Live application: https://rfp-evaluation-kvlnarasimharao.streamlit.app/")
p("In the live app, open Sample run to review the completed comparison, then open Criteria to view the active weights. To evaluate new proposals, use Evaluate, upload at least two text-based PDFs, fill supplier metadata, and select Evaluate suppliers. The hosted Gemini key is held in Streamlit secrets, so no key entry is needed for that deployment.")
p("For a local run, clone the repository, install packages from requirements.txt, run python scripts/seed_db.py, then run streamlit run streamlit_app.py. Set GEMINI_API_KEY locally to evaluate a new batch. The sample run is viewable without a key. Run python -m unittest discover -s tests -v to repeat the automated checks.")

h("Operating conditions")
p("PDFs must contain selectable text; scanned images require text recognition before upload. The model's judgment and cited evidence should be reviewed for procurement use. The public cloud deployment uses local SQLite storage that may reset when the app instance restarts, so completed results should be downloaded as JSON when a durable record is needed.")

h("References")
for item in (
    "Source brief, Agentic_RFP_Evaluation_Mini_Project.pdf, sections 1 to 10",
    "Google AI for Developers, Gemini generateContent API: https://ai.google.dev/api/generate-content",
    "Streamlit, Deploy your app on Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy",
    "Streamlit, Secrets management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management",
):
    p(item)

doc.add_page_break()
h("Application screenshots")
p("Completed four-supplier evaluation in the Sample run tab.")
bw_dir = ROOT / "tmp" / "submission_screenshots"
bw_dir.mkdir(parents=True, exist_ok=True)
for screenshot_name in ("leaderboard", "criteria"):
    Image.open(ROOT / "docs" / "screenshots" / f"{screenshot_name}.jpg").convert("L").save(
        bw_dir / f"{screenshot_name}.jpg", quality=95)
doc.add_picture(str(bw_dir / "leaderboard.jpg"), width=Inches(6.75))
p("Active criteria and weights loaded from SQLite.")
doc.add_picture(str(bw_dir / "criteria.jpg"), width=Inches(6.75))

doc.save(OUT)
print(OUT)

