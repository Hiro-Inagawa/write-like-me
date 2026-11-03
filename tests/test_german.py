"""German support: measurements, profile, rules and the command line."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import stylometry
from stylometry import compute_features, split_sentences, tokenize_words
from voice_check import check_text
from voice_lang import detect_language
from voice_profile import DEFAULT_PROFILE, DEFAULT_PROFILE_DE, default_profile, init_from_stylometry, validate_profile

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = (
    "Ab dem 1. Januar 2027 läuft die Anmeldung nur noch online. Wer bis zum 31. Dezember einen Termin bucht, "
    "wird wie bisher bedient. Danach schickt das Amt die Unterlagen per Post, z. B. als Brief.\n\n"
    "Die Gebühr steigt von 12 € auf 15 €. Ich finde das teuer, aber wir zahlen es trotzdem."
)


def rules_of(text, profile=DEFAULT_PROFILE_DE, register="default"):
    return set(check_text(text, profile, register)["counts"])


class Measurements(unittest.TestCase):
    def test_words_with_umlauts_stay_whole(self):
        self.assertEqual(tokenize_words("Für die Größe gilt: über"), ["für", "die", "größe", "gilt", "über"])

    def test_german_abbreviations_and_ordinals_do_not_split(self):
        text = "Das gilt z. B. für Kunden. Am 2. November kam er. Im 3. Kapitel steht es. Über alles."
        self.assertEqual(len(split_sentences(text)), 4)

    def test_german_profile_uses_german_word_lists(self):
        f = compute_features(SAMPLE, use_textstat=False, use_spacy=False, language="de")
        self.assertEqual(f["language"], "de")
        self.assertNotIn("contractions", f)
        self.assertGreater(f["pronouns"]["first_sg_per_100w"], 0)
        self.assertIn("die", f["lexical"]["function_word_profile"])

    def test_english_profile_is_unchanged(self):
        f = compute_features("I think we're done. The report is late.", use_textstat=False, use_spacy=False)
        self.assertNotIn("language", f)
        self.assertEqual(f["contractions"]["count"], 1)

    @unittest.skipUnless(stylometry.HAS_TEXTSTAT, "textstat not installed")
    def test_german_readability_uses_german_formulas(self):
        out = stylometry.compute_readability(SAMPLE, "de")
        self.assertIn("wiener_sachtextformel", out)
        self.assertNotIn("gunning_fog", out)
        self.assertIn("gunning_fog", stylometry.compute_readability("The report was late. We met on Thursday."))


def _has_german_model():
    if not stylometry.HAS_SPACY:
        return False
    try:
        stylometry._spacy.load("de_core_news_sm")
        return True
    except OSError:
        return False


@unittest.skipUnless(_has_german_model(), "spaCy or de_core_news_sm not installed")
class GermanSpacy(unittest.TestCase):
    def test_passive_and_nominal_style_are_measured(self):
        out = stylometry.compute_spacy_features(SAMPLE, "de")
        self.assertGreater(out["passive_ratio"], 0)
        self.assertGreater(out["lexical_density"], 0)


class Profile(unittest.TestCase):
    def test_default_profile_by_language(self):
        self.assertIs(default_profile("de"), DEFAULT_PROFILE_DE)
        self.assertIs(default_profile("en"), DEFAULT_PROFILE)
        self.assertEqual(validate_profile(DEFAULT_PROFILE_DE), [])

    def test_unknown_language_and_bad_policy_are_rejected(self):
        bad = dict(DEFAULT_PROFILE_DE, language="fr",
                   registers={"default": {"gender_characters": "sometimes", "en_dash": "maybe"}})
        errors = " ".join(validate_profile(bad))
        self.assertIn("language", errors)
        self.assertIn("gender_characters", errors)
        self.assertIn("en_dash", errors)

    def test_init_keeps_the_corpus_language(self):
        stylo = compute_features(SAMPLE * 3, use_textstat=False, use_spacy=False, language="de")
        profile = init_from_stylometry("demo", "brief", stylo)
        self.assertEqual(profile["language"], "de")
        self.assertIn("innovativ", profile["bans"]["evaluative_block"])
        self.assertEqual(validate_profile(profile), [])


class Rules(unittest.TestCase):
    def test_correct_german_passes(self):
        self.assertEqual(check_text(SAMPLE, DEFAULT_PROFILE_DE, "default")["verdict"], "PASS")

    def test_german_rules_do_not_run_for_english(self):
        self.assertNotIn("DE_QUOTES", rules_of('He called it "final".', DEFAULT_PROFILE))

    def test_gender_choice_belongs_to_the_voice(self):
        text = "Unsere Kund*innen zahlen per Rechnung. Alle Kund*innen bekommen sie per E-Mail."
        self.assertEqual(check_text(text, DEFAULT_PROFILE_DE, "default")["verdict"], "PASS")
        banned = dict(DEFAULT_PROFILE_DE, registers={"brief": {"gender_characters": "forbidden"}})
        self.assertEqual(check_text(text, banned, "brief")["verdict"], "BLOCK")

    def test_mixed_gender_forms_are_flagged(self):
        self.assertIn("DE_GENDER_MIX", rules_of("Unsere Kund*innen zahlen sofort. Viele Kunden zahlen später."))
        self.assertIn("DE_GENDER_MIX", rules_of("Die KundInnen zahlen sofort. Die Kund:innen zahlen später."))

    def test_address_mix_needs_both_forms(self):
        self.assertIn("DE_ADDRESS_MIX", rules_of("Senden Sie uns die Datei. Dann kannst du loslegen."))
        self.assertNotIn("DE_ADDRESS_MIX", rules_of("Sie kam spät. Dann kannst du loslegen."))

    def test_quoted_words_are_someone_elses(self):
        self.assertNotIn("DE_CALQUE", rules_of("Der Chef sagte „das macht Sinn“ und ging."))


class Detection(unittest.TestCase):
    def test_detects_german_and_english(self):
        self.assertEqual(detect_language(SAMPLE), "de")
        self.assertEqual(detect_language("Das Meeting war gut. Der Plan steht."), "de")
        self.assertEqual(detect_language("The plan is simple and it works for the team."), "en")
        self.assertEqual(detect_language("Is this the real thing? I do not know."), "en")

    def test_too_little_evidence_stays_english(self):
        for text in ("", "Hallo", "# Überblick", "Design System 2026"):
            self.assertEqual(detect_language(text), "en", text)


class CommandLine(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, *args], cwd=ROOT, input=stdin, capture_output=True,
                              text=True, encoding="utf-8")

    def test_voice_check_language_flag(self):
        res = self.run_cli("scripts/voice_check.py", "-", "--language", "de", "--json",
                           stdin='Er nannte es "fertig" und ging.')
        result = json.loads(res.stdout.rsplit("\n", 2)[0])
        self.assertEqual(res.returncode, 1)
        self.assertIn("DE_QUOTES", result["counts"])

    def test_voice_check_detects_german_without_flag(self):
        res = self.run_cli("scripts/voice_check.py", "-", "--json",
                           stdin='Er nannte es "fertig" und ging nicht mehr in das Büro.')
        result = json.loads(res.stdout.rsplit("\n", 2)[0])
        self.assertEqual(result["language"], "de")
        self.assertIn("DE_QUOTES", result["counts"])

    def test_voice_check_detects_english_without_flag(self):
        res = self.run_cli("scripts/voice_check.py", "-", "--json",
                           stdin='He called it "done" and it was the end of the day for the team.')
        result = json.loads(res.stdout.rsplit("\n", 2)[0])
        self.assertEqual(result["language"], "en")
        self.assertNotIn("DE_QUOTES", result["counts"])

    def test_stylometry_detects_language_without_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp, "korpus.md")
            corpus.write_text(SAMPLE, encoding="utf-8")
            out = Path(tmp, "p.json")
            res = self.run_cli("scripts/stylometry.py", str(corpus), "--no-spacy", "--no-textstat",
                               "--output", str(out))
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("language detected as de", res.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["language"], "de")

    def test_stylometry_language_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp, "korpus.md")
            corpus.write_text(SAMPLE, encoding="utf-8")
            out = Path(tmp, "p.json")
            res = self.run_cli("scripts/stylometry.py", str(corpus), "--language", "de", "--no-spacy",
                               "--no-textstat", "--output", str(out))
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["language"], "de")

    def test_german_goldens_gate(self):
        res = self.run_cli("eval/voice_eval.py", "score", "--goldens", "eval/goldens/universal-de.goldens.jsonl",
                           "--language", "de", "--gate", "eval/baselines/universal-de.json")
        self.assertTrue(res.stdout.strip().endswith("VOICE_EVAL_OK"), res.stdout)


if __name__ == "__main__":
    unittest.main()
