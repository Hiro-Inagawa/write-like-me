"""The optional textstat and spaCy tiers produce numbers when their libraries are installed."""
import unittest

import stylometry
from stylometry import compute_readability, compute_spacy_features

SAMPLE = (
    "The report was late. We rescheduled the review for Thursday, which suited everyone. "
    "The team finished the draft and sent it to the client before noon."
)


@unittest.skipUnless(stylometry.HAS_TEXTSTAT, "textstat not installed")
class ReadabilityTier(unittest.TestCase):
    def test_all_four_scores_are_present(self):
        out = compute_readability(SAMPLE)
        self.assertEqual(
            set(out),
            {"flesch_kincaid_grade", "gunning_fog", "flesch_reading_ease", "avg_syllables_per_word"},
        )

    def test_one_failing_metric_keeps_the_others(self):
        original = stylometry._textstat.gunning_fog
        stylometry._textstat.gunning_fog = lambda text: 1 / 0
        try:
            out = compute_readability(SAMPLE)
        finally:
            stylometry._textstat.gunning_fog = original
        self.assertNotIn("gunning_fog", out)
        self.assertIn("flesch_kincaid_grade", out)


def _has_model():
    if not stylometry.HAS_SPACY:
        return False
    try:
        stylometry._spacy.load("en_core_web_sm")
        return True
    except OSError:
        return False


@unittest.skipUnless(_has_model(), "spaCy or en_core_web_sm not installed")
class SpacyTier(unittest.TestCase):
    def test_lexical_density_is_a_measurement(self):
        dense = compute_spacy_features("Engineers quickly rebuilt broken bridges near rural villages.")
        sparse = compute_spacy_features("It was what we wanted, and that was that.")
        self.assertGreater(dense["lexical_density"], sparse["lexical_density"])
        self.assertLess(dense["lexical_density"], 1.0)
        self.assertGreater(sparse["lexical_density"], 0.0)


if __name__ == "__main__":
    unittest.main()
