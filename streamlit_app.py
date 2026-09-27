import json
import os
from datetime import date
from pathlib import Path

import streamlit as st

from rfp.database import active_criteria, connect, initialize, list_runs, load_run, save_criteria
from rfp.workflow import evaluate_batch

ROOT = Path(__file__).parent
DB_PATH = Path(os.environ.get("RFP_DB_PATH", ROOT / "data" / "rfp.sqlite3"))


def database():
    connection = connect(DB_PATH)
    initialize(connection)
    return connection


def show_run(result, key_prefix):
    st.subheader("Leaderboard")
    st.dataframe([{
        "Rank": s["final_rank"], "Supplier": s["supplier_name"],
        "Absolute score / 100": s["absolute_score"], "PPI / 100": s["ppi"],
        "Submitted": s["submission_date"], "Experience / 10": s["experience_rating"],
    } for s in result["suppliers"]], hide_index=True, use_container_width=True)
    st.caption("Order: higher PPI, earlier submission, higher experience, then supplier name A to Z.")
    st.subheader("Detailed scorecards")
    for supplier in result["suppliers"]:
        with st.expander(f"#{supplier['final_rank']} {supplier['supplier_name']}"):
            st.write(supplier["overall_summary"])
            for item in supplier["criteria"]:
                st.markdown(f"**{item['name']} - {item['score']:g}/{item['max_score']:g}**  "
                            f"Weight {item['weight']:g}% | Best {item['benchmark']:g} | "
                            f"Gap {item['gap']:g} | Peer {item['relative_percent']:g}%")
                st.write(item["justification"])
                st.caption(f"Evidence: {item['evidence']}")
            if supplier["risks"]:
                st.write("Risks: " + "; ".join(supplier["risks"]))
    st.subheader("Run details")
    st.code(result["rfp_run_id"])
    if result["warnings"]:
        st.warning("Validation warnings\n\n" + "\n\n".join(result["warnings"]))
    else:
        st.success("All scorecards passed normalization without warnings.")
    st.download_button("Download complete result as JSON", json.dumps(result, indent=2),
                       file_name=f"rfp_run_{result['rfp_run_id']}.json", mime="application/json",
                       key=f"download_{key_prefix}_{result['rfp_run_id']}")


st.set_page_config(page_title="RFP Supplier Evaluation", layout="wide")
st.title("RFP Supplier Evaluation")
st.write("Compare supplier proposals using document evidence and transparent ranking rules.")
conn = database()
tab_evaluate, tab_criteria, tab_runs, tab_sample = st.tabs(
    ["Evaluate", "Criteria", "Saved runs", "Sample run"]
)

with tab_criteria:
    st.subheader("Evaluation criteria")
    rows = [dict(row) for row in conn.execute("SELECT * FROM evaluation_criteria ORDER BY criterion_id")]
    edited = st.data_editor(rows, hide_index=True, use_container_width=True,
                            disabled=["criterion_id"], num_rows="fixed",
                            column_config={"is_active": st.column_config.CheckboxColumn("Active")})
    active = [row for row in rows if row["is_active"]]
    st.caption(f"Current active weight: {sum(row['weight'] for row in active):g}%")
    if st.button("Save criteria"):
        try:
            save_criteria(conn, edited.to_dict("records") if hasattr(edited, "to_dict") else edited)
            st.success("Criteria saved. The next run will use these values.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

with tab_evaluate:
    st.subheader("New evaluation batch")
    st.caption("Upload text-based PDFs. Every file is evaluated with the active criteria shown above.")
    files = st.file_uploader("Supplier proposal PDFs", type="pdf", accept_multiple_files=True)
    try:
        criteria = active_criteria(conn)
        st.info("Active weights total 100%. " + ", ".join(
            f"{c['name']} {c['weight']:g}%" for c in criteria))
    except ValueError as exc:
        st.error(str(exc))
    entries = []
    for index, file in enumerate(files or []):
        with st.container(border=True):
            st.markdown(f"**{file.name}**")
            a, b, c = st.columns(3)
            name = a.text_input("Supplier name", Path(file.name).stem.replace("_", " "), key=f"name_{index}")
            submitted = b.date_input("Submission date", date.today(), key=f"date_{index}")
            experience = c.number_input("Historical experience / 10", 0.0, 10.0, 5.0,
                                        0.5, key=f"rating_{index}")
            entries.append({"supplier_name": name, "submission_date": submitted.isoformat(),
                            "experience_rating": experience, "pdf_bytes": file.getvalue()})
    with st.expander("AI connection"):
        provider = st.selectbox("Provider", ["Gemini", "Ollama Cloud"])
        secret_name = "GEMINI_API_KEY" if provider == "Gemini" else "OLLAMA_API_KEY"
        try:
            hosted_key_available = bool(os.environ.get(secret_name) or st.secrets.get(secret_name, ""))
        except Exception:
            hosted_key_available = bool(os.environ.get(secret_name))
        st.caption("A hosted key is available. Leave this blank to use it." if hosted_key_available
                   else "Enter your API key. It is not saved in SQLite or the JSON export.")
        api_key = st.text_input("API key", type="password")
        model = st.text_input("Model", value="gemini-2.5-flash" if provider == "Gemini" else "gpt-oss:120b-cloud")
    if st.button("Evaluate suppliers", type="primary", disabled=len(entries) < 2):
        for entry in entries:
            secret_name = "GEMINI_API_KEY" if provider == "Gemini" else "OLLAMA_API_KEY"
            try:
                stored_key = st.secrets.get(secret_name, "")
            except Exception:
                stored_key = ""
            entry["api_key"] = api_key or os.environ.get(secret_name, "") or stored_key
            entry["model"] = model
        try:
            with st.spinner("Reading PDFs and evaluating suppliers..."):
                result = evaluate_batch(conn, entries)
            st.session_state["latest_run"] = result
            st.success("Evaluation completed and saved.")
        except Exception as exc:
            st.error(f"Evaluation stopped: {exc}")
    if "latest_run" in st.session_state:
        show_run(st.session_state["latest_run"], "latest")

with tab_runs:
    runs = list_runs(conn)
    if runs:
        selected = st.selectbox("Select a saved run", [r["rfp_run_id"] for r in runs],
                                format_func=lambda x: next(r["created_at"] + " - " + x[:8]
                                                            for r in runs if r["rfp_run_id"] == x))
        show_run(load_run(conn, selected), "saved")
    else:
        st.info("No evaluation runs saved yet.")

with tab_sample:
    example = st.selectbox("Example", ["Live Gemini evaluation", "Validation example"])
    st.write("Both examples use the four fictional supplier proposals.")
    filename = "live_run.json" if example == "Live Gemini evaluation" else "sample_run.json"
    sample = json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
    show_run(sample, "sample")
