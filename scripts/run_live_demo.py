"""Evaluate the four sample PDFs with Gemini using GEMINI_API_KEY from the environment."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rfp.database import connect, initialize
from rfp.workflow import evaluate_batch

METADATA = [
    ("Apex Systems", "2026-09-15", 8.5),
    ("BrightPath Tech", "2026-09-14", 4.0),
    ("NexaWorks", "2026-09-16", 8.0),
    ("Orbit Digital", "2026-09-13", 9.5),
]


def main():
    key = os.environ["GEMINI_API_KEY"]
    conn = connect(ROOT / "data" / "rfp.sqlite3")
    initialize(conn)
    entries = [{"supplier_name": name, "submission_date": submitted,
                "experience_rating": rating, "api_key": key, "model": "gemini-2.5-flash",
                "pdf_bytes": (ROOT / "data" / "proposals" /
                              (name.lower().replace(" ", "_") + ".pdf")).read_bytes()}
               for name, submitted, rating in METADATA]
    result = evaluate_batch(conn, entries)
    (ROOT / "data" / "live_run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Run:", result["rfp_run_id"])
    print("Ranking:", [(x["final_rank"], x["supplier_name"], x["ppi"])
                       for x in result["suppliers"]])
    print("Warnings:", len(result["warnings"]))


if __name__ == "__main__":
    main()
