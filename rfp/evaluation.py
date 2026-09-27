import json
import math
import re
from io import BytesIO
from urllib.request import Request, urlopen

from pypdf import PdfReader


def extract_pdf_text(pdf_bytes):
    reader = PdfReader(BytesIO(pdf_bytes))
    if len(reader.pages) == 0:
        raise ValueError("PDF has no pages.")
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) < 100:
        raise ValueError("PDF contains too little selectable text. Use a text-based PDF.")
    return text[:60000]


def build_prompt(supplier_name, criteria, document_text):
    rubric = [{k: row[k] for k in ("criterion_id", "name", "description", "max_score")}
              for row in criteria]
    return f"""Evaluate this supplier proposal using ONLY evidence in the document.
Return JSON only, with supplier_name, criteria, risks, and overall_summary.
Return exactly one criterion result for every active criterion. Each result must contain
criterion_id, score, max_score, justification, and evidence. Use numeric scores from 0
through max_score. Evidence must be a short, direct quotation from the document.
If evidence is absent, score 0 and say what is missing. Do not invent facts.
Supplier: {supplier_name}
Active criteria: {json.dumps(rubric, ensure_ascii=False)}
Document: <proposal>\n{document_text}\n</proposal>"""


def call_llm(prompt, api_key, model):
    if not api_key:
        raise ValueError("Enter an API key to evaluate uploaded proposals.")
    if model.startswith("gemini-"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}],
                   "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
        result = _post_json(url, headers, payload)
        return result["candidates"][0]["content"]["parts"][0]["text"]
    payload = {"model": model, "messages": [
        {"role": "system", "content": "You assess RFP evidence and return valid JSON only."},
        {"role": "user", "content": prompt}], "temperature": 0}
    result = _post_json("https://ollama.com/v1/chat/completions", {
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, payload)
    return result["choices"][0]["message"]["content"]


def _post_json(url, headers, payload):
    request = Request(url, data=json.dumps(payload).encode("utf-8"),
                      headers=headers, method="POST")
    with urlopen(request, timeout=120) as response:
        return json.load(response)


def normalize_response(raw, criteria, supplier_name):
    warnings = []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        data = {}
        warnings.append(f"{supplier_name}: invalid JSON; all criteria scored zero.")
    if not isinstance(data, dict):
        data = {}
        warnings.append(f"{supplier_name}: JSON root was not an object.")
    items = data.get("criteria")
    if not isinstance(items, list):
        items = []
        warnings.append(f"{supplier_name}: missing criteria list.")
    found = {}
    expected_ids = {int(c["criterion_id"]) for c in criteria}
    for item in items:
        if not isinstance(item, dict):
            warnings.append(f"{supplier_name}: ignored malformed criterion entry.")
            continue
        try:
            criterion_id = int(item.get("criterion_id"))
        except (TypeError, ValueError):
            warnings.append(f"{supplier_name}: ignored criterion with invalid ID.")
            continue
        if criterion_id not in expected_ids or criterion_id in found:
            warnings.append(f"{supplier_name}: ignored unknown or duplicate criterion {criterion_id}.")
            continue
        found[criterion_id] = item
    normalized = []
    for criterion in criteria:
        cid = int(criterion["criterion_id"])
        item = found.get(cid, {})
        if not item:
            warnings.append(f"{supplier_name}: criterion {cid} missing; scored zero.")
        try:
            score = float(item.get("score", 0))
            if not math.isfinite(score):
                raise ValueError
        except (ValueError, TypeError):
            score = 0.0
            warnings.append(f"{supplier_name}: criterion {cid} had an invalid score; scored zero.")
        clipped = min(max(score, 0), float(criterion["max_score"]))
        if clipped != score:
            warnings.append(f"{supplier_name}: criterion {cid} score clipped to range.")
        evidence = str(item.get("evidence") or "").strip()
        justification = str(item.get("justification") or "").strip()
        if not evidence:
            warnings.append(f"{supplier_name}: criterion {cid} has no cited evidence.")
        normalized.append({
            "criterion_id": cid, "name": criterion["name"], "score": clipped,
            "max_score": float(criterion["max_score"]), "weight": float(criterion["weight"]),
            "justification": justification or "No explanation supplied.",
            "evidence": evidence or "No evidence supplied.",
        })
    risks = data.get("risks", [])
    if not isinstance(risks, list):
        risks = []
        warnings.append(f"{supplier_name}: malformed risks list.")
    return {
        "supplier_name": supplier_name,
        "criteria": normalized,
        "risks": [str(x) for x in risks],
        "overall_summary": str(data.get("overall_summary") or "No summary supplied."),
    }, warnings
