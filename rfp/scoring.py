from datetime import date


def score_and_rank(suppliers, criteria):
    if not suppliers:
        raise ValueError("At least one supplier is required.")
    benchmark = {int(c["criterion_id"]): max(
        next(item["score"] for item in s["criteria"] if item["criterion_id"] == c["criterion_id"])
        for s in suppliers
    ) for c in criteria}
    exact_ppi = {}
    for supplier in suppliers:
        date.fromisoformat(supplier["submission_date"])
        supplier["absolute_score"] = round(sum(
            item["score"] / item["max_score"] * item["weight"]
            for item in supplier["criteria"]
        ), 4)
        peer_terms = []
        for item in supplier["criteria"]:
            best = benchmark[item["criterion_id"]]
            item["benchmark"] = best
            item["gap"] = round(item["score"] - best, 4)
            relative = item["score"] / best * 100 if best > 0 else 100.0
            item["relative_percent"] = round(relative, 4)
            peer_terms.append(relative * item["weight"] / 100)
        exact_ppi[id(supplier)] = sum(peer_terms)
        supplier["ppi"] = round(exact_ppi[id(supplier)], 4)
    ranked = sorted(suppliers, key=lambda s: (
        -exact_ppi[id(s)], s["submission_date"], -float(s["experience_rating"]),
        s["supplier_name"].casefold(), s["supplier_name"],
    ))
    for rank, supplier in enumerate(ranked, 1):
        supplier["final_rank"] = rank
    return ranked, benchmark
