import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from voice_check import check_text
from voice_eval import verify_files
from voice_profile import DEFAULT_PROFILE, init_from_stylometry, preflight, validate_profile

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "voice_check.py"
PROFILE_SCRIPT = ROOT / "scripts" / "voice_profile.py"


def ids(text, register_overrides=None, **kw):
    profile = copy.deepcopy(DEFAULT_PROFILE)
    if register_overrides:
        profile["registers"] = {"default": dict(register_overrides)}
    return check_text(text, profile, "default", **kw)


def stylo(words=None, semicolons=0.0, short=0.0, hedge=0.233):
    data = {"syntactic": {"sentence_stats": {"mean_words": 20.0, "pct_short_le5": short, "pct_long_ge30": 0.1}},
            "punctuation": {"comma_per_sentence": 1.5, "semicolon_per_1000w": semicolons},
            "hedging_booster": {"hedge_per_100w": hedge, "boost_per_100w": 0.0},
            "pronouns": {"first_sg_per_100w": 0.3}}
    if words is not None:
        data["corpus_stats"] = {"word_count": words}
    return data


class ClosingCaveatTests(unittest.TestCase):
    BODY = "The kettle heats water in two minutes.\n\nThe lid locks while the water is hot.\n\n"

    def test_final_paragraph_caveat_opener(self):
        for tail in ("Keep in mind that the handle gets warm.", "Note that the base stays warm.",
                     "Just so you know, the filter is optional.", "A small caveat applies to old units."):
            self.assertIn("CLOSING_CAVEAT", ids(self.BODY + tail)["counts"], tail)

    def test_however_opens_final_paragraph_only_when_there_are_two_paragraphs(self):
        self.assertIn("CLOSING_CAVEAT", ids(self.BODY + "However, some units lack the filter.")["counts"])
        self.assertNotIn("CLOSING_CAVEAT", ids("However, the pump runs quietly.")["counts"])

    def test_caveat_in_the_middle_is_not_closing(self):
        text = "That said, the base is warm.\n\nThe lid locks.\n\nThe pump is quiet.\n\nThe filter slides out."
        self.assertNotIn("CLOSING_CAVEAT", ids(text)["counts"])

    def test_phrases_and_level_come_from_the_profile(self):
        profile = copy.deepcopy(DEFAULT_PROFILE)
        profile["bans"]["caveat_phrases"] = ["a word of warning"]
        profile["registers"] = {"default": {"closing_caveat": "block"}}
        result = check_text(self.BODY + "A word of warning about the lid.", profile, "default")
        self.assertEqual(result["verdict"], "BLOCK")
        self.assertNotIn("CLOSING_CAVEAT", check_text(self.BODY + "Keep in mind the lid.", profile, "default")["counts"])


class AntithesisTests(unittest.TestCase):
    def test_heading_and_short_line(self):
        self.assertIn("COMPRESSED_ANTITHESIS", ids("# Clarity, not clutter")["counts"])
        self.assertIn("COMPRESSED_ANTITHESIS", ids("Made for walkers rather than drivers.")["counts"])

    def test_long_sentence_flags_only_a_short_closing_tail(self):
        long_tail = "The pump was tested for six weeks in three homes and owners call it steady, not noisy."
        self.assertIn("COMPRESSED_ANTITHESIS", ids(long_tail)["counts"])
        comparison = "Most owners chose the small model rather than the large one because a flat has little space."
        self.assertNotIn("COMPRESSED_ANTITHESIS", ids(comparison)["counts"])
        wide = "The pump was tested for six weeks in three homes and it stayed steady, not as loud as the old unit was."
        self.assertNotIn("COMPRESSED_ANTITHESIS", ids(wide)["counts"])


class BenefitTailTests(unittest.TestCase):
    def test_tails(self):
        for text in ("The app syncs notes, so you can resume later.", "It lists orders, helping you plan.",
                     "It removes lead, ensuring clean water.", "It stores files, which lets you search them.",
                     "It runs nightly, which means you never wait."):
            self.assertIn("BENEFIT_TAIL", ids(text)["counts"], text)

    def test_plain_sentences_pass(self):
        self.assertNotIn("BENEFIT_TAIL", ids("The app syncs notes every minute.")["counts"])
        self.assertNotIn("BENEFIT_TAIL", ids("Ensuring the lid is closed comes first.")["counts"])

    def test_register_can_turn_it_off(self):
        self.assertNotIn("BENEFIT_TAIL", ids("It lists orders, helping you plan.", {"benefit_tail": "off"})["counts"])


class TaglineTests(unittest.TestCase):
    def test_taglines(self):
        for text in ("Clarity. Speed. Results.", "Simplicity and power for every team", "Excellence without compromise"):
            self.assertIn("TAGLINE", ids(text)["counts"], text)

    def test_sentences_with_verbs_and_tables_pass(self):
        for text in ("Quality control starts at the loading dock.", "Trust is earned slowly.",
                     "| Speed | Value |\n|---|---|\n| Fast | 5 |", "# Speed and trust"):
            self.assertNotIn("TAGLINE", ids(text)["counts"], text)


class LengthBandTests(unittest.TestCase):
    BAND = {"length": {"min": 5, "max": 12}}

    def test_outside_band_blocks_when_both_set(self):
        self.assertEqual(ids("Too short.", self.BAND)["verdict"], "BLOCK")
        long = "word " * 20
        self.assertEqual(ids(long, self.BAND)["verdict"], "BLOCK")
        self.assertNotIn("LENGTH_BAND", ids("This sentence has exactly eight words in it.", self.BAND)["counts"])

    def test_one_sided_band_reviews(self):
        result = ids("Too short.", {"length": {"min": 5}})
        self.assertEqual(result["verdict"], "REVIEW")

    def test_validation(self):
        profile = copy.deepcopy(DEFAULT_PROFILE)
        profile["registers"] = {"a": {"length": {"min": 10, "max": 5}}}
        self.assertTrue(any("length" in e for e in validate_profile(profile)))
        profile["registers"] = {"a": {"length": {"min": 5, "max": 10}}}
        self.assertEqual(validate_profile(profile), [])


class AdditionsTests(unittest.TestCase):
    EXPL = "The Fernwood pump holds 2 litres. It runs for 40 minutes at 90% power."

    def test_missing_number_and_name(self):
        result = ids("The Fernwood pump holds 3 litres. It was built by Marlow.", explanation=self.EXPL)
        items = sorted(h["message"].split("'")[1] for h in result["hits"] if h["rule"] == "ADDITION")
        self.assertEqual(items, ["3", "Marlow"])

    def test_percent_needs_a_percent_in_the_explanation(self):
        self.assertNotIn("ADDITION", ids("It runs at 90% power.", explanation=self.EXPL)["counts"])
        self.assertIn("ADDITION", ids("It runs for 40% of the time.", explanation=self.EXPL)["counts"])

    def test_sentence_start_capitals_are_not_names(self):
        self.assertNotIn("ADDITION", ids("Water moves to the kettle.", explanation=self.EXPL)["counts"])

    def test_inactive_without_an_explanation(self):
        self.assertNotIn("ADDITION", ids("Marlow built 3 pumps.")["counts"])

    def test_cli_flag(self):
        with tempfile.TemporaryDirectory() as d:
            draft, expl = Path(d) / "d.md", Path(d) / "e.md"
            draft.write_text("The pump holds 5 litres.\n", encoding="utf-8")
            expl.write_text("The pump holds 2 litres.\n", encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), str(draft), "--explanation", str(expl)],
                                  capture_output=True, text=True, encoding="utf-8")
            self.assertIn("ADDITION", proc.stdout)
            self.assertTrue(proc.stdout.rstrip().endswith("VOICE_CHECK_REVIEW"))


class RepeatedPhraseTests(unittest.TestCase):
    def test_match_ignores_case_and_whitespace(self):
        result = ids("Notes, tasks and files, All  In One\nPlace.", rejected=["all in one place"])
        self.assertEqual(result["verdict"], "BLOCK")
        self.assertIn("REPEATED_PHRASE", result["counts"])

    def test_no_match_and_no_list(self):
        self.assertEqual(ids("Files sit in one folder.", rejected=["all in one place"])["verdict"], "PASS")
        self.assertEqual(ids("All in one place.")["verdict"], "PASS")

    def test_cli_flag(self):
        with tempfile.TemporaryDirectory() as d:
            draft, rej = Path(d) / "d.md", Path(d) / "r.txt"
            draft.write_text("A tool built for the way you live.\n", encoding="utf-8")
            rej.write_text("built for the way you live\n\n", encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), str(draft), "--rejected", str(rej)],
                                  capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(proc.returncode, 1)
            self.assertTrue(proc.stdout.rstrip().endswith("VOICE_CHECK_BLOCK"))


class TricolonSeverityTests(unittest.TestCase):
    TEXT = "The pump is quiet, the lid is safe, and the base is cool."

    def test_default_is_info_and_does_not_change_the_verdict(self):
        result = ids(self.TEXT)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual([h["severity"] for h in result["hits"]], ["info"])

    def test_register_sets_the_severity(self):
        self.assertEqual(ids(self.TEXT, {"tricolon": "review"})["verdict"], "REVIEW")
        self.assertEqual(ids(self.TEXT, {"tricolon": "block"})["verdict"], "BLOCK")
        self.assertEqual(ids(self.TEXT, {"tricolon": "off"})["hits"], [])


class ProvisionalRuleTests(unittest.TestCase):
    def test_small_corpus_zero_count_is_provisional_not_a_ban(self):
        profile = init_from_stylometry("t", "essay", stylo(words=8000))
        reg = profile["registers"]["essay"]
        self.assertEqual(reg["semicolons"], "review")
        self.assertEqual(profile["provisional"]["words"], 8000)
        self.assertEqual(sorted(profile["provisional"]["rules"]), ["pct_short_le5_max", "semicolons", "targets"])
        self.assertEqual(validate_profile(profile), [])

    def test_large_corpus_zero_count_stays_a_rule(self):
        profile = init_from_stylometry("t", "essay", stylo(words=40000))
        self.assertEqual(profile["registers"]["essay"]["semicolons"], "forbidden")
        self.assertNotIn("provisional", profile)

    def test_provisional_zero_short_target_does_not_block_staccato(self):
        profile = init_from_stylometry("t", "essay", stylo(words=8000))
        text = "The result is clear. Variation increases. This is the whole argument."
        result = check_text(text, profile, "essay")
        staccato = [h for h in result["hits"] if h["rule"] == "STACCATO_RUN"]
        self.assertEqual([h["severity"] for h in staccato], ["review"])
        confirmed = copy.deepcopy(profile)
        confirmed["provisional"]["rules"] = []
        staccato = [h for h in check_text(text, confirmed, "essay")["hits"] if h["rule"] == "STACCATO_RUN"]
        self.assertEqual([h["severity"] for h in staccato], ["block"])

    def test_drift_on_provisional_targets_is_labelled(self):
        profile = init_from_stylometry("t", "essay", stylo(words=8000))
        profile["thresholds"]["min_words_for_drift"] = 10
        result = check_text("Short one here. Short two here. Short three here now.", profile, "essay")
        self.assertTrue(result["drift"] and all(d.get("provisional") for d in result["drift"]))

    def test_preflight_lists_a_small_corpus(self):
        self.assertTrue(any("provisional" in line for line in preflight(5000)))
        self.assertFalse(any("provisional" in line for line in preflight(30000)))

    def test_preflight_cli_token(self):
        proc = subprocess.run([sys.executable, str(PROFILE_SCRIPT), "preflight", "--corpus-words", "100"],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout.rstrip().endswith("VOICE_PREFLIGHT_DONE"))


class HedgeToleranceTests(unittest.TestCase):
    def setUp(self):
        self.profile = init_from_stylometry("t", "essay", stylo(hedge=0.5))
        self.profile["thresholds"]["min_words_for_drift"] = 10
        self.profile["registers"]["essay"]["targets"] = {"hedge_per_100w_mean": 0.5}
        self.text = "The pump might run. " * 3 + "The lid locks and stays shut until the water cools down."

    def _hedge_drift(self, tolerance):
        profile = copy.deepcopy(self.profile)
        profile["thresholds"]["hedge_tolerance"] = tolerance
        return [d for d in check_text(self.text, profile, "essay")["drift"] if d["metric"] == "hedge_per_100w_mean"]

    def test_the_profile_tolerance_decides_drift(self):
        self.assertTrue(self._hedge_drift(0.1))
        self.assertEqual(self._hedge_drift(50), [])

    def test_init_writes_the_mean_and_the_default_tolerance(self):
        self.assertEqual(self.profile["thresholds"]["hedge_tolerance"], 0.5)
        fresh = init_from_stylometry("t", "essay", stylo(hedge=0.233))
        self.assertEqual(fresh["registers"]["essay"]["targets"]["hedge_per_100w_mean"], 0.233)


class VerifyFilesTests(unittest.TestCase):
    def test_verify_scores_each_sample_from_a_file(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad = Path(d) / "good.md", Path(d) / "bad.md"
            good.write_text("The pump moves water to the kettle.\n", encoding="utf-8")
            bad.write_text("The pump moves water to the kettle — quietly.\n", encoding="utf-8")
            self.assertTrue(verify_files([good], DEFAULT_PROFILE, "default")["ok"])
            outcome = verify_files([good, bad], DEFAULT_PROFILE, "default")
            self.assertFalse(outcome["ok"])
            self.assertEqual([r["ok"] for r in outcome["rows"]], [True, False])

    def test_verify_cli(self):
        with tempfile.TemporaryDirectory() as d:
            sample, profile = Path(d) / "s.md", Path(d) / "profile.json"
            sample.write_text("The pump moves water to the kettle.\n", encoding="utf-8")
            profile.write_text(json.dumps(DEFAULT_PROFILE), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(ROOT / "eval" / "voice_eval.py"), "verify",
                                   "--profile", str(profile), str(sample)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(proc.returncode, 0, proc.stdout)
            self.assertTrue(proc.stdout.rstrip().endswith("VOICE_EVAL_OK"))


if __name__ == "__main__":
    unittest.main()
