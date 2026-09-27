from datetime import datetime, timezone
from uuid import uuid4

from .database import active_criteria, save_run
from .evaluation import build_prompt, call_llm, extract_pdf_text, normalize_response
from .scoring import score_and_rank


def evaluate_batch(conn, entries, evaluator=None):
    if len(entries) < 2:
        raise ValueError("Upload at least two supplier proposals.")
    names = [entry["supplier_name"].strip() for entry in entries]
    if any(not name for name in names) or len({name.casefold() for name in names}) != len(names):
        raise ValueError("Each supplier needs a unique, nonempty name.")
    criteria = active_criteria(conn)  # reload immediately before each batch
    evaluator = evaluator or call_llm
    suppliers, warnings = [], []
    for entry in entries:
        name = entry["supplier_name"].strip()
        rating = float(entry["experience_rating"])
        if rating < 0 or rating > 10:
            raise ValueError(f"{name}: experience rating must be 0 to 10.")
        text = extract_pdf_text(entry["pdf_bytes"])
        prompt = build_prompt(name, criteria, text)
        raw = evaluator(prompt, entry.get("api_key", ""), entry.get("model", "gpt-4o-mini"))
        result, supplier_warnings = normalize_response(raw, criteria, name)
        result.update({"submission_date": entry["submission_date"], "experience_rating": rating})
        suppliers.append(result)
        warnings.extend(supplier_warnings)
    ranked, benchmark = score_and_rank(suppliers, criteria)
    result = {
        "rfp_run_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "criteria": criteria,
        "benchmark": benchmark,
        "suppliers": ranked,
        "warnings": warnings,
        "tie_break_order": ["Higher PPI", "Earlier submission date", "Higher experience rating", "Supplier name A to Z"],
        "rules": {"zero_benchmark_relative_percent": 100, "rank_start": 1},
    }
    save_run(conn, result)
    return result
