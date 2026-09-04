import json
import tempfile
import unittest
from pathlib import Path

from voice_eval import gate, load_goldens, score
from voice_profile import DEFAULT_PROFILE

GOLDENS = [
    {"id": "g1", "text": "Fixed — but not.", "expect": "block", "rules": ["EM_DASH"]},
    {"id": "g2", "text": "That said, it holds.", "expect": "review", "rules": ["HEDGE_CONNECTIVE"]},
    {"id": "g3", "text": "Accuracy rose from 71% to 89%.", "expect": "pass"},
    {"id": "g4", "text": "Frankly, it works.", "expect": "pass"},
]


class EvalTests(unittest.TestCase):
    def test_load_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "g.jsonl"
            p.write_text('{"id":"a","text":"x","expect":"pass"}\n{"id":"a","text":"y","expect":"pass"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_goldens(p)

    def test_load_skips_comments_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "g.jsonl"
            p.write_text('# header\n\n{"id":"a","text":"x","expect":"pass"}\n', encoding="utf-8")
            self.assertEqual(len(load_goldens(p)), 1)

    def test_score_metrics(self):
        result = score(GOLDENS, DEFAULT_PROFILE, "default")
        m = result["metrics"]
        self.assertEqual(m["block_recall"], 1.0)
        self.assertEqual(m["review_recall"], 1.0)
        self.assertEqual(m["false_alarm_rate"], 0.5)
        self.assertEqual(m["failures"], ["g4"])
        self.assertEqual(result["per_rule"]["EM_DASH"]["hit"], 1)
        self.assertEqual(result["per_rule"]["STANCE_OPENER"]["spurious"], 1)

    def test_gate_flags_regression(self):
        base = {"block_recall": 1.0, "review_recall": 1.0, "false_alarm_rate": 0.0}
        self.assertEqual(gate({"block_recall": 1.0, "review_recall": 1.0, "false_alarm_rate": 0.0}, base, 0.0), [])
        problems = gate({"block_recall": 0.9, "review_recall": 1.0, "false_alarm_rate": 0.1}, base, 0.0)
        self.assertEqual(len(problems), 2)


if __name__ == "__main__":
    unittest.main()
