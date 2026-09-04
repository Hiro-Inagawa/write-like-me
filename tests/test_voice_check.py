import json
import subprocess
import sys
import unittest
from pathlib import Path

from voice_check import check_text
from voice_profile import DEFAULT_PROFILE

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "scripts" / "voice_check.py"


def run_cli(*args, stdin=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True, encoding="utf-8")


class CheckTextTests(unittest.TestCase):
    def test_ai_tells_block(self):
        result = check_text((FIX / "ai_tells.md").read_text(encoding="utf-8"), DEFAULT_PROFILE, "default")
        self.assertEqual(result["verdict"], "BLOCK")
        for rule in ("EM_DASH", "STANCE_OPENER", "EVALUATIVE_ADJECTIVE", "PERFORMATIVE_VERB",
                     "FILLER_OPENER", "NOT_ONLY_BUT_ALSO", "BUILDUP_BEFORE_DATA", "SUMMARY_OPENER"):
            self.assertIn(rule, result["counts"], rule)

    def test_clean_passes(self):
        result = check_text((FIX / "clean.md").read_text(encoding="utf-8"), DEFAULT_PROFILE, "default")
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["hits"], [])

    def test_citation_sections_are_skipped_by_default(self):
        text = "# Title\n\nClean prose here.\n\n## Sources\n\n- Paper -- arXiv, 2024. Clearly innovative work.\n"
        self.assertEqual(check_text(text, DEFAULT_PROFILE, "default")["verdict"], "PASS")
        self.assertEqual(check_text(text, DEFAULT_PROFILE, "default", skip_citations=False)["verdict"], "BLOCK")

    def test_related_link_sections_are_skipped(self):
        text = "Prose here.\n\n## Related\n\n- [[Safety and Red-Teaming]] -- ../04-ecosystem/safety.md\n"
        self.assertEqual(check_text(text, DEFAULT_PROFILE, "default")["verdict"], "PASS")

    def test_quoted_words_do_not_hit(self):
        text = 'The authors called it "the previous state-of-the-art" in their paper.'
        self.assertEqual(check_text(text, DEFAULT_PROFILE, "default")["verdict"], "PASS")
        self.assertEqual(check_text("This state-of-the-art tool is fast.", DEFAULT_PROFILE, "default")["verdict"], "BLOCK")

    def test_drift_reports_review_when_targets_exist(self):
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        profile["thresholds"]["min_words_for_drift"] = 10
        profile["registers"] = {"article": {"targets": {"mean_sentence_words": [28, 38]}}}
        result = check_text("Short one here. Short two here. Short three here now.", profile, "article")
        metrics = [d["metric"] for d in result["drift"]]
        self.assertIn("mean_sentence_words", metrics)
        self.assertEqual(result["verdict"], "REVIEW")

    def test_drift_skipped_below_min_words(self):
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        profile["registers"] = {"article": {"targets": {"mean_sentence_words": [28, 38]}}}
        result = check_text("Short one here.", profile, "article")
        self.assertEqual(result["drift"], [])


class CliTests(unittest.TestCase):
    def test_block_exit_code_and_token(self):
        proc = run_cli(str(FIX / "ai_tells.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(proc.stdout.rstrip().endswith("VOICE_CHECK_BLOCK"))

    def test_pass_exit_code_and_token(self):
        proc = run_cli(str(FIX / "clean.md"))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(proc.stdout.rstrip().endswith("VOICE_CHECK_PASS"))

    def test_json_output(self):
        proc = run_cli(str(FIX / "ai_tells.md"), "--json")
        data = json.loads(proc.stdout.rsplit("\n", 2)[0])
        self.assertEqual(data["verdict"], "BLOCK")

    def test_stdin(self):
        proc = run_cli("-", stdin="Frankly, this is fine.")
        self.assertEqual(proc.returncode, 1)

    def test_missing_file_is_exit_2(self):
        proc = run_cli(str(FIX / "nope.md"))
        self.assertEqual(proc.returncode, 2)

    def test_strict_promotes_review(self):
        proc = run_cli("-", "--strict", stdin="That said, the plan holds together across the whole quarter.")
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
