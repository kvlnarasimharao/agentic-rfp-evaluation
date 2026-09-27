import json
import tempfile
import unittest
from pathlib import Path

from rfp.database import active_criteria, connect, initialize, load_run
from rfp.evaluation import normalize_response
from rfp.scoring import score_and_rank
from rfp.workflow import evaluate_batch


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = connect(Path(self.tmp.name) / "test.sqlite3")
        initialize(self.conn)
        self.criteria = active_criteria(self.conn)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_normalization_fills_missing_and_clips_scores(self):
        raw = {"criteria": [
            {"criterion_id": 1, "score": 99, "evidence": "quote"},
            {"criterion_id": 2, "score": "bad"},
            {"criterion_id": 1, "score": 5},
        ]}
        result, warnings = normalize_response(raw, self.criteria, "Supplier")
        self.assertEqual([x["score"] for x in result["criteria"]], [10, 0, 0, 0, 0])
        self.assertTrue(any("clipped" in x for x in warnings))
        self.assertTrue(any("duplicate" in x for x in warnings))
        self.assertTrue(any("missing" in x for x in warnings))

    def test_weighted_scores_and_peer_metrics(self):
        def supplier(name, scores, submitted, rating):
            return {"supplier_name": name, "submission_date": submitted,
                    "experience_rating": rating, "criteria": [
                        {"criterion_id": c["criterion_id"], "score": score,
                         "max_score": c["max_score"], "weight": c["weight"]}
                        for c, score in zip(self.criteria, scores)]}
        ranked, benchmark = score_and_rank([
            supplier("A", [10, 8, 8, 8, 8], "2026-09-20", 8),
            supplier("B", [8, 10, 10, 10, 10], "2026-09-19", 7),
        ], self.criteria)
        self.assertEqual(benchmark[1], 10)
        self.assertEqual(ranked[0]["supplier_name"], "B")
        self.assertEqual(ranked[0]["absolute_score"], 94)
        self.assertEqual(ranked[0]["criteria"][0]["gap"], -2)
        self.assertEqual(ranked[0]["ppi"], 94)

    def test_tie_break_order_and_zero_benchmark(self):
        criteria = [{"criterion_id": 1, "weight": 100, "max_score": 10}]
        def s(name, date, rating):
            return {"supplier_name": name, "submission_date": date,
                    "experience_rating": rating, "criteria": [
                        {"criterion_id": 1, "score": 0, "max_score": 10, "weight": 100}]}
        ranked, _ = score_and_rank([
            s("Zed", "2026-09-01", 8), s("Ada", "2026-09-01", 8),
            s("Bea", "2026-08-31", 1), s("Cal", "2026-09-01", 9)
        ], criteria)
        self.assertEqual([x["supplier_name"] for x in ranked], ["Bea", "Cal", "Ada", "Zed"])
        self.assertTrue(all(x["ppi"] == 100 for x in ranked))

    def test_workflow_persists_complete_run(self):
        pdf_path = Path(__file__).resolve().parents[1] / "data" / "proposals" / "apex_systems.pdf"
        pdf = pdf_path.read_bytes()
        entries = [{"supplier_name": name, "submission_date": "2026-09-01",
                    "experience_rating": 5, "pdf_bytes": pdf} for name in ("One", "Two")]
        def evaluator(prompt, api_key, model):
            return json.dumps({"criteria": [{"criterion_id": c["criterion_id"],
                "score": 5, "evidence": "test", "justification": "test"} for c in self.criteria]})
        result = evaluate_batch(self.conn, entries, evaluator)
        saved = load_run(self.conn, result["rfp_run_id"])
        self.assertEqual(len(saved["suppliers"]), 2)
        self.assertEqual(saved["suppliers"][0]["final_rank"], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM supplier_results").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
