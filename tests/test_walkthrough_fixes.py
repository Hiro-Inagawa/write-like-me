"""Tests for the defects a first-time walkthrough of the build workflow found."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from corpus_conflicts import find_conflicts
from extract_author_turns import is_generated_artifact as extract_is_generated
from stylometry import compute_contraction_stats, compute_features, is_generated_artifact, load_corpus
from voice_check import check_text
from voice_eval import verify_files
from voice_profile import DEFAULT_PROFILE, POLICY_NOTE, preflight

ROOT = Path(__file__).resolve().parent.parent
STYLOMETRY = ROOT / "scripts" / "stylometry.py"
REPORT = ROOT / "scripts" / "generate_report_from_json.py"
PROFILE = ROOT / "scripts" / "voice_profile.py"
CONFLICTS = ROOT / "scripts" / "corpus_conflicts.py"

PROSE = ("The kettle heats water in two minutes. The lid locks while the water is hot. "
         "We tested it on a gas stove and on an induction plate. It worked on both. ") * 6


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8")


def make_corpus(base: Path) -> Path:
    corpus = base / "corpus"
    corpus.mkdir()
    (corpus / "a.md").write_text(PROSE, encoding="utf-8")
    return corpus


class OutputFolderTests(unittest.TestCase):
    def test_output_creates_missing_parent_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = make_corpus(Path(tmp))
            out = Path(tmp) / "voices" / "me" / "essay.stylometry.json"
            proc = run(STYLOMETRY, corpus, "--register", "essay", "--output", out, "--no-spacy", "--no-textstat")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out.exists())

    def test_bare_report_goes_next_to_the_output_and_not_into_the_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = make_corpus(Path(tmp))
            out = Path(tmp) / "voices" / "me" / "essay.stylometry.json"
            proc = run(STYLOMETRY, corpus, "--output", out, "--report", "--no-spacy", "--no-textstat")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(len(list(out.parent.glob("_STYLE-PROFILE-*.md"))), 1)
            self.assertEqual(list(corpus.glob("_STYLE-PROFILE-*.md")), [])

    def test_bare_report_without_output_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = make_corpus(Path(tmp))
            proc = run(STYLOMETRY, corpus, "--report", "--no-spacy", "--no-textstat")
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(list(corpus.glob("*")), [corpus / "a.md"])

    def test_report_script_defaults_to_the_folder_of_the_first_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = make_corpus(Path(tmp))
            out = Path(tmp) / "voices" / "me" / "essay.stylometry.json"
            run(STYLOMETRY, corpus, "--output", out, "--no-spacy", "--no-textstat")
            proc = run(REPORT, out, "--author", "Test")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(len(list(out.parent.glob("_STYLE-PROFILE-*.md"))), 1)
            self.assertEqual(list(corpus.glob("_STYLE-PROFILE-*.md")), [])

    def test_report_script_still_honors_an_explicit_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = make_corpus(Path(tmp))
            out = Path(tmp) / "essay.stylometry.json"
            run(STYLOMETRY, corpus, "--output", out, "--no-spacy", "--no-textstat")
            target = Path(tmp) / "reports" / "r.md"
            self.assertEqual(run(REPORT, out, "--output", target).returncode, 0)
            self.assertTrue(target.exists())

    def test_console_notes_are_ascii(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = make_corpus(Path(tmp))
            proc = run(STYLOMETRY, corpus, "--output", Path(tmp) / "o.json")
            proc.stderr.encode("ascii")


class GeneratedFileSkipTests(unittest.TestCase):
    def build(self, base: Path) -> Path:
        corpus = make_corpus(base)
        (corpus / "_STYLE-PROFILE-2026-10-06.md").write_text("report " * 500, encoding="utf-8")
        (corpus / "voices" / "me").mkdir(parents=True)
        (corpus / "voices" / "me" / "01-generative.md").write_text("generated " * 500, encoding="utf-8")
        return corpus

    def test_helper_recognizes_reports_and_voices_folders(self):
        root = Path("/c")
        self.assertTrue(is_generated_artifact(root / "_STYLE-PROFILE-x.md", root))
        self.assertTrue(is_generated_artifact(root / "voices" / "me" / "a.md", root))
        self.assertFalse(is_generated_artifact(root / "essays" / "a.md", root))
        self.assertTrue(extract_is_generated(root / "voices" / "a.md", root))
        self.assertFalse(extract_is_generated(root / "a.md", root))

    def test_a_corpus_that_lives_inside_a_voices_folder_is_kept(self):
        root = Path("/work/voices/corpus")
        self.assertFalse(is_generated_artifact(root / "a.md", root))

    def test_load_corpus_skips_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = self.build(Path(tmp))
            combined, _ = load_corpus(corpus)
            self.assertNotIn("report", combined)
            self.assertNotIn("generated", combined)
            self.assertIn("kettle", combined)


class ContractionTests(unittest.TestCase):
    def test_count_and_rate_per_100_words(self):
        stats = compute_contraction_stats("It's done and we don't need more. The team's plan holds.", 10)
        self.assertEqual(stats["count"], 2)
        self.assertEqual(stats["per_100w"], 20.0)

    def test_curly_apostrophe_counts(self):
        self.assertEqual(compute_contraction_stats("It’s fine.", 2)["count"], 1)

    def test_zero_contractions(self):
        stats = compute_contraction_stats("It is done and we do not need more.", 9)
        self.assertEqual((stats["count"], stats["per_100w"]), (0, 0.0))

    def test_features_carry_the_contraction_block(self):
        features = compute_features(PROSE + "We don't mind.", use_textstat=False, use_spacy=False)
        self.assertEqual(features["contractions"]["count"], 1)
        self.assertGreater(features["contractions"]["per_100w"], 0)


class PolicyTests(unittest.TestCase):
    def test_init_prints_the_policy_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = make_corpus(Path(tmp))
            stylo = Path(tmp) / "essay.stylometry.json"
            run(STYLOMETRY, corpus, "--output", stylo, "--no-spacy", "--no-textstat")
            out = Path(tmp) / "voices" / "me" / "profile.json"
            proc = run(PROFILE, "init", "--voice", "me", "--register", "essay", "--from-stylometry", stylo,
                       "--output", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("contractions and questions start as off", proc.stdout)
            self.assertIn("forbidden", proc.stdout)
            self.assertIn("contractions and questions start as off", POLICY_NOTE)

    def test_caveat_phrases_include_results_may_vary(self):
        phrases = DEFAULT_PROFILE["bans"]["caveat_phrases"]
        self.assertIn("results may vary", phrases)
        self.assertIn("your mileage may vary", phrases)
        body = "The kettle heats water in two minutes.\n\nThe lid locks while the water is hot.\n\n"
        for tail in ("Results may vary.", "Your mileage may vary."):
            result = check_text(body + tail, DEFAULT_PROFILE, "default")
            self.assertIn("CLOSING_CAVEAT", result["counts"], tail)

    def test_preflight_names_the_floor(self):
        self.assertTrue(any("build stops" in line for line in preflight(4000)))
        self.assertFalse(any("build stops" in line for line in preflight(5000)))
        self.assertTrue(any("provisional" in line for line in preflight(12000)))


class StrictVerifyTests(unittest.TestCase):
    def test_a_review_hit_fails_verify_only_under_strict(self):
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        profile["registers"] = {"default": {"semicolons": "review"}}
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "s.md"
            sample.write_text("The kettle heats fast; the lid locks while hot.", encoding="utf-8")
            self.assertTrue(verify_files([sample], profile, "default")["ok"])
            self.assertFalse(verify_files([sample], profile, "default", strict=True)["ok"])


class CorpusConflictTests(unittest.TestCase):
    def test_blocks_in_the_authors_own_writing_are_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp)
            (corpus / "a.md").write_text("The tool is not only fast but also cheap. It works.", encoding="utf-8")
            (corpus / "b.md").write_text("We went home. It was not only late but also cold.", encoding="utf-8")
            (corpus / "_STYLE-PROFILE-x.md").write_text("It is not only a but also b.", encoding="utf-8")
            rows = find_conflicts(corpus)
            self.assertEqual([r["rule"] for r in rows], ["NOT_ONLY_BUT_ALSO"])
            self.assertEqual((rows[0]["count"], rows[0]["files"]), (2, 2))

    def test_cli_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.md").write_text("The tool is fast and cheap.", encoding="utf-8")
            proc = run(CONFLICTS, tmp)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout.strip().splitlines()[-1], "VOICE_CONFLICTS_NONE")
            (Path(tmp) / "b.md").write_text("It is not only fast but also cheap.", encoding="utf-8")
            proc = run(CONFLICTS, tmp)
            self.assertIn("CONFLICT NOT_ONLY_BUT_ALSO", proc.stdout)
            self.assertEqual(proc.stdout.strip().splitlines()[-1], "VOICE_CONFLICTS_FOUND")


if __name__ == "__main__":
    unittest.main()
