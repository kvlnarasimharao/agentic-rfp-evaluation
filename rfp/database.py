import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CRITERIA = [
    (1, "Technical Capability", "Architecture, integrations, scalability, technical fit", 30, 10, 1),
    (2, "Implementation Plan", "Timeline, milestones, staffing, risk plan", 20, 10, 1),
    (3, "Commercial Value", "Pricing clarity, total cost, assumptions", 20, 10, 1),
    (4, "Security & Compliance", "Controls, certifications, privacy, auditability", 20, 10, 1),
    (5, "Support & Experience", "Support model, similar projects, references", 10, 10, 1),
]


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS evaluation_criteria (
            criterion_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            weight REAL NOT NULL CHECK(weight >= 0),
            max_score REAL NOT NULL CHECK(max_score > 0),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
        );
        CREATE TABLE IF NOT EXISTS rfp_runs (
            rfp_run_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            criteria_json TEXT NOT NULL,
            warnings_json TEXT NOT NULL,
            result_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS supplier_results (
            rfp_run_id TEXT NOT NULL REFERENCES rfp_runs(rfp_run_id),
            supplier_name TEXT NOT NULL,
            submission_date TEXT NOT NULL,
            experience_rating REAL NOT NULL,
            absolute_score REAL NOT NULL,
            ppi REAL NOT NULL,
            final_rank INTEGER NOT NULL,
            result_json TEXT NOT NULL,
            PRIMARY KEY (rfp_run_id, supplier_name)
        );
    """)
    if conn.execute("SELECT COUNT(*) FROM evaluation_criteria").fetchone()[0] == 0:
        conn.executemany("INSERT INTO evaluation_criteria VALUES (?, ?, ?, ?, ?, ?)", DEFAULT_CRITERIA)
    conn.commit()


def active_criteria(conn):
    rows = [dict(row) for row in conn.execute(
        "SELECT * FROM evaluation_criteria WHERE is_active = 1 ORDER BY criterion_id"
    )]
    if not rows:
        raise ValueError("Activate at least one criterion before evaluation.")
    if abs(sum(row["weight"] for row in rows) - 100) > 0.0001:
        raise ValueError("Active criterion weights must total 100%.")
    return rows


def save_criteria(conn, rows):
    ids = [int(row["criterion_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Criterion IDs must be unique.")
    active = [row for row in rows if row["is_active"]]
    if not active or abs(sum(float(row["weight"]) for row in active) - 100) > 0.0001:
        raise ValueError("Active criterion weights must total 100%.")
    for row in rows:
        if float(row["weight"]) < 0 or float(row["max_score"]) <= 0:
            raise ValueError("Weights cannot be negative and maximum scores must be positive.")
    with conn:
        for row in rows:
            conn.execute("""UPDATE evaluation_criteria
                SET name=?, description=?, weight=?, max_score=?, is_active=?
                WHERE criterion_id=?""", (
                str(row["name"]).strip(), str(row["description"]).strip(),
                float(row["weight"]), float(row["max_score"]),
                int(bool(row["is_active"])), int(row["criterion_id"]),
            ))


def save_run(conn, result):
    with conn:
        conn.execute("INSERT INTO rfp_runs VALUES (?, ?, ?, ?, ?, ?)", (
            result["rfp_run_id"], result["created_at"], "completed",
            json.dumps(result["criteria"]), json.dumps(result["warnings"]), json.dumps(result),
        ))
        for supplier in result["suppliers"]:
            conn.execute("INSERT INTO supplier_results VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                result["rfp_run_id"], supplier["supplier_name"], supplier["submission_date"],
                supplier["experience_rating"], supplier["absolute_score"], supplier["ppi"],
                supplier["final_rank"], json.dumps(supplier),
            ))


def list_runs(conn):
    return [dict(row) for row in conn.execute(
        "SELECT rfp_run_id, created_at, status FROM rfp_runs ORDER BY created_at DESC"
    )]


def load_run(conn, run_id):
    row = conn.execute("SELECT result_json FROM rfp_runs WHERE rfp_run_id=?", (run_id,)).fetchone()
    return json.loads(row[0]) if row else None
