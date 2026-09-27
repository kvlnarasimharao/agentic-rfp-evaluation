"""Generate four fictional two-page proposals and a reproducible example run."""
import json
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rfp.database import connect, initialize
from rfp.workflow import evaluate_batch

REQUEST = "The university seeks a secure supplier evaluation portal for 200 procurement users. The portal must import proposal PDFs, support role-based access, show traceable scores, and export results. Delivery is expected within 16 weeks."

PROPOSALS = {
    "Apex Systems": {
        "summary": "Apex proposes a modular web portal with a documented REST API, event-driven ingestion, and a managed relational database. It meets the 200-user target with a tested 500-user load profile.",
        "solution": "The integration plan names SSO via SAML, procurement ERP exchange through REST, PDF text extraction, audit events, and export to JSON. Architecture diagrams identify separate ingestion, scoring, and review services.",
        "implementation": "A 15-week plan assigns a project manager, two engineers, a security lead, and a tester. Milestones: discovery weeks 1-2; build weeks 3-9; integration weeks 10-12; testing weeks 13-14; handover week 15. The risk register covers ERP delays.",
        "price": "Fixed implementation fee: USD 138,000. Annual support: USD 22,000. Total first year: USD 160,000. Assumes one ERP connector and no migration of legacy files; additional connectors are priced separately.",
        "security": "Controls include SAML SSO, least-privilege roles, encryption in transit and at rest, quarterly penetration tests, daily backups, 365-day audit retention, and an incident notification target of 24 hours. ISO 27001 certification is stated with certificate number AX-27001-24.",
        "support": "Business-hours support with a four-hour response for critical incidents and 99.5% target availability. Apex lists two similar university projects and offers references, but no named contact details.",
        "risk": "The higher first-year price and separate connector charges may increase procurement cost.",
        "scores": [9, 7, 6, 9, 7], "date": "2026-09-15", "rating": 8.5,
    },
    "BrightPath Tech": {
        "summary": "BrightPath proposes a compact portal focused on rapid deployment and low cost. It covers proposal upload, a review screen, and CSV export for the 200-user team.",
        "solution": "The solution uses a single application server and hosted database. BrightPath mentions an ERP connection but does not specify protocol, fields, error handling, or scale test results.",
        "implementation": "An eight-week schedule covers discovery in week 1, configuration in weeks 2-5, testing in weeks 6-7, and launch in week 8. A lead developer and one tester are named by role. No contingency time is allocated.",
        "price": "Fixed implementation fee: USD 65,000. Annual support: USD 12,000. Total first year: USD 77,000. Price includes one integration and 12 months of hosting; taxes are excluded.",
        "security": "The proposal says data will be encrypted and users will have passwords. It does not describe access roles, audit retention, independent testing, incident response, privacy controls, or certifications.",
        "support": "Email support is available on business days with a two-day response target. BrightPath cites one small nonprofit deployment but supplies no reference contact.",
        "risk": "Security assurance and integration detail are limited; the accelerated plan has no schedule buffer.",
        "scores": [5, 7, 9, 3, 4], "date": "2026-09-14", "rating": 4.0,
    },
    "NexaWorks": {
        "summary": "NexaWorks proposes a balanced procurement portal with document intake, reviewer workflow, score traceability, and JSON export for the 200-user university team.",
        "solution": "The design separates PDF intake, evaluation, and reporting. It specifies REST integration with the ERP, SAML SSO, a staging environment, and a 250-user performance test.",
        "implementation": "A 12-week plan has named role owners and acceptance gates: discovery weeks 1-2, prototype weeks 3-4, implementation weeks 5-8, ERP integration weeks 9-10, testing week 11, and training plus go-live week 12. A two-week fallback window and weekly risk review are included.",
        "price": "Implementation fee: USD 99,000. Annual support: USD 18,000. Total first year: USD 117,000. Includes one ERP connector, training, and migration of up to 2,000 PDFs. Additional migration is USD 3 per file.",
        "security": "Controls include role-based access, SAML SSO, encryption in transit and at rest, monthly vulnerability scans, daily backups, and 180-day audit logs. Incident notification is within 48 hours. No external certification is claimed.",
        "support": "A named service manager, 24-hour critical incident channel, two-hour response target, quarterly service reviews, and 99.7% availability target are offered. Three public-sector projects and two contactable references are listed.",
        "risk": "External certification is not claimed and extra migration volume costs more.",
        "scores": [8, 10, 8, 8, 10], "date": "2026-09-16", "rating": 8.0,
    },
    "Orbit Digital": {
        "summary": "Orbit Digital emphasizes prior public-sector delivery and a managed portal for document review, scorecards, and export.",
        "solution": "The proposal describes configurable reviewer screens and a managed database. It says the solution integrates with the university ERP, but gives no interface specification, data mapping, or failure recovery design. A 300-user load test is offered.",
        "implementation": "A 14-week plan covers discovery weeks 1-3, build weeks 4-10, test weeks 11-12, and rollout weeks 13-14. A project manager, three developers, and a support specialist are assigned. ERP dependencies are flagged but no fallback milestone is shown.",
        "price": "Implementation fee: USD 110,000. Annual support: USD 19,000. Total first year: USD 129,000. Includes hosting and training. ERP customization is time-and-materials at USD 135 per hour.",
        "security": "Controls include SSO, encrypted storage, weekly backups, role permissions, annual penetration testing, and a 90-day audit trail. Incident notification timing and privacy deletion policy are not stated.",
        "support": "A 24-hour help desk and one-hour critical response target are offered. Orbit lists five government deployments and three named reference organizations with contact details.",
        "risk": "ERP scope and customization cost are uncertain; security response timing is missing.",
        "scores": [6, 7, 7, 6, 9], "date": "2026-09-13", "rating": 9.5,
    },
}


def make_pdf(name, data, output):
    variants = {
        "Apex Systems": {
            "accent": "#203B4B", "tint": "#EDF2F4", "title_size": 22,
            "title_align": TA_LEFT, "section_prefix": "", "lead": "TECHNICAL SOLUTION",
            "page_two": "Commercial offer and assurance",
            "first_order": [("Executive summary", "summary"),
                            ("Proposed solution", "solution"),
                            ("Implementation approach and timeline", "implementation")],
            "second_order": [("Security and compliance", "security"),
                             ("Support and experience", "support"),
                             ("Delivery considerations", "risk")],
        },
        "BrightPath Tech": {
            "accent": "#965A24", "tint": "#F8F0E8", "title_size": 24,
            "title_align": TA_LEFT, "section_prefix": "", "lead": "RAPID DELIVERY OFFER",
            "page_two": "Pricing and service commitment",
            "first_order": [("Executive summary", "summary"),
                            ("Implementation approach and timeline", "implementation"),
                            ("Proposed solution", "solution")],
            "second_order": [("Support and experience", "support"),
                             ("Security and compliance", "security"),
                             ("Delivery considerations", "risk")],
        },
        "NexaWorks": {
            "accent": "#2D594E", "tint": "#EDF4F0", "title_size": 21,
            "title_align": TA_CENTER, "section_prefix": "0", "lead": "IMPLEMENTATION PROPOSAL",
            "page_two": "Commercial and operating plan",
            "first_order": [("Executive summary", "summary"),
                            ("Proposed solution", "solution"),
                            ("Implementation approach and timeline", "implementation")],
            "second_order": [("Security and compliance", "security"),
                             ("Support and experience", "support"),
                             ("Delivery considerations", "risk")],
        },
        "Orbit Digital": {
            "accent": "#514B60", "tint": "#F1F0F4", "title_size": 22,
            "title_align": TA_RIGHT, "section_prefix": "", "lead": "PUBLIC SECTOR DELIVERY",
            "page_two": "Experience, commercial terms and controls",
            "first_order": [("Executive summary", "summary"),
                            ("Proposed solution", "solution"),
                            ("Implementation approach and timeline", "implementation")],
            "second_order": [("Support, experience and references", "support"),
                             ("Security and compliance", "security"),
                             ("Delivery considerations", "risk")],
        },
    }
    fees = {
        "Apex Systems": ("138,000", "22,000", "160,000"),
        "BrightPath Tech": ("65,000", "12,000", "77,000"),
        "NexaWorks": ("99,000", "18,000", "117,000"),
        "Orbit Digital": ("110,000", "19,000", "129,000"),
    }
    v = variants[name]
    accent = colors.HexColor(v["accent"])
    tint = colors.HexColor(v["tint"])
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ProposalTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=v["title_size"], leading=v["title_size"] + 3,
        textColor=accent, alignment=v["title_align"], spaceAfter=6))
    styles.add(ParagraphStyle(name="ProposalLead", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=accent,
        alignment=v["title_align"], spaceAfter=15))
    styles.add(ParagraphStyle(name="ProposalSection", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=11.5, leading=14,
        textColor=accent, spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name="ProposalBody", parent=styles["BodyText"],
        fontName="Helvetica", fontSize=10.3, leading=15.5, spaceAfter=10))
    styles.add(ParagraphStyle(name="ProposalSmall", parent=styles["BodyText"],
        fontName="Helvetica", fontSize=9.1, leading=13.4, spaceAfter=6))
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=54, leftMargin=54,
                            topMargin=48, bottomMargin=48)
    story = []
    def section(label, key, index=None):
        display = label
        if v["section_prefix"] and index is not None:
            display = str(index).zfill(2) + "  " + label
        story.append(Paragraph(display, styles["ProposalSection"]))
        story.append(Paragraph(data[key], styles["ProposalBody"]))
    def rule():
        story.append(HRFlowable(width="100%", thickness=1.2, color=accent))
        story.append(Spacer(1, 12))
    def price_table():
        rows = [["Cost item", "USD"], ["Implementation", fees[name][0]],
                ["Annual support", fees[name][1]], ["First-year total", fees[name][2]]]
        table = Table(rows, colWidths=[330, 150], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), tint),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, -1), (-1, -1), .7, accent),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(table)
        story.append(Spacer(1, 9))
        story.append(Paragraph(data["price"], styles["ProposalSmall"]))
    story.append(Paragraph(name, styles["ProposalTitle"]))
    story.append(Paragraph(v["lead"], styles["ProposalLead"]))
    if name in ("Apex Systems", "Orbit Digital"):
        rule()
    if name == "BrightPath Tech":
        card = Table([[Paragraph(data["summary"], styles["ProposalBody"])]], colWidths=[480])
        card.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), tint),
            ("LEFTPADDING", (0, 0), (-1, -1), 13),
            ("RIGHTPADDING", (0, 0), (-1, -1), 13),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        story.append(card)
        story.append(Spacer(1, 8))
    story.append(Paragraph("Requirement understood", styles["ProposalSection"]))
    story.append(Paragraph(REQUEST, styles["ProposalSmall"]))
    for i, (label, key) in enumerate(v["first_order"], 1):
        if name == "BrightPath Tech" and key == "summary":
            continue
        section(label, key, i)
    story.append(PageBreak())
    story.append(Paragraph(v["page_two"], styles["ProposalTitle"]))
    if name == "NexaWorks":
        rule()
    if name == "Orbit Digital":
        section(*v["second_order"][0], 1)
    story.append(Paragraph("Price and assumptions", styles["ProposalSection"]))
    price_table()
    remaining = v["second_order"][1:] if name == "Orbit Digital" else v["second_order"]
    for i, (label, key) in enumerate(remaining, 2 if name == "Orbit Digital" else 1):
        section(label, key, i)
    doc.build(story)

def main():
    folder = ROOT / "data" / "proposals"
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in PROPOSALS.items():
        make_pdf(name, data, folder / (name.lower().replace(" ", "_") + ".pdf"))
    conn = connect(ROOT / "data" / "rfp.sqlite3")
    initialize(conn)
    entries = [{"supplier_name": name, "submission_date": data["date"],
                "experience_rating": data["rating"],
                "pdf_bytes": (folder / (name.lower().replace(" ", "_") + ".pdf")).read_bytes()}
               for name, data in PROPOSALS.items()]
    def sample_evaluator(prompt, api_key, model):
        name = re.search(r"Supplier: (.+)\n", prompt).group(1)
        data = PROPOSALS[name]
        evidence = [data[k] for k in ("solution", "implementation", "price", "security", "support")]
        criteria = [{"criterion_id": i, "score": score, "max_score": 10,
                     "justification": f"The proposal provides the quoted {label.lower()} detail.",
                     "evidence": evidence[i - 1]}
                    for i, (score, label) in enumerate(zip(data["scores"],
                        ["technical", "implementation", "commercial", "security", "support"]), 1)]
        if name == "BrightPath Tech":
            criteria[3]["score"] = -2  # intentional validation example, normalized to zero
        return json.dumps({"supplier_name": name, "criteria": criteria,
                           "risks": [data["risk"]], "overall_summary": data["summary"]})
    result = evaluate_batch(conn, entries, evaluator=sample_evaluator)
    (ROOT / "data" / "sample_run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Generated four PDFs and sample run:", result["rfp_run_id"])


if __name__ == "__main__":
    main()
