import json
import tempfile
import unittest
from pathlib import Path

from voice_profile import DEFAULT_PROFILE, load_profile, resolve_register, validate_profile, init_from_stylometry


class ProfileTests(unittest.TestCase):
    def test_default_profile_is_valid(self):
        self.assertEqual(validate_profile(DEFAULT_PROFILE), [])

    def test_missing_register_falls_back_to_defaults(self):
        reg = resolve_register(DEFAULT_PROFILE, "does-not-exist")
        self.assertEqual(reg["semicolons"], "off")
        self.assertEqual(reg["announcement_colon"], "review")

    def test_register_override_merges_over_defaults(self):
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        profile["registers"] = {"article": {"semicolons": "forbidden"}}
        reg = resolve_register(profile, "article")
        self.assertEqual(reg["semicolons"], "forbidden")
        self.assertEqual(reg["contractions"], "off")

    def test_validate_reports_bad_values(self):
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        profile["registers"] = {"x": {"semicolons": "maybe"}}
        errors = validate_profile(profile)
        self.assertTrue(any("semicolons" in e for e in errors))

    def test_init_from_stylometry_sets_ranges(self):
        stylo = {"syntactic": {"sentence_stats": {"mean_words": 33.0, "pct_short_le5": 0.0, "pct_long_ge30": 0.6},
                               "concession_rate": 0.2},
                 "punctuation": {"comma_per_sentence": 2.0, "semicolon_per_1000w": 0.0},
                 "hedging_booster": {"hedge_per_100w": 0.233, "boost_per_100w": 0.0},
                 "pronouns": {"first_sg_per_100w": 0.28}}
        profile = init_from_stylometry("example", "article-public", stylo)
        reg = profile["registers"]["article-public"]
        self.assertEqual(reg["targets"]["mean_sentence_words"], [28, 38])
        self.assertEqual(reg["targets"]["pct_short_le5_max"], 0.0)
        self.assertEqual(reg["semicolons"], "forbidden")
        self.assertEqual(validate_profile(profile), [])

    def test_validate_rule_overrides(self):
        profile = json.loads(json.dumps(DEFAULT_PROFILE))
        profile["rule_overrides"] = {"EM_DASH": "review"}
        self.assertEqual(validate_profile(profile), [])
        profile["rule_overrides"] = {"EM_DASH": "maybe"}
        self.assertTrue(any("rule_overrides" in e for e in validate_profile(profile)))

    def test_load_profile_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "profile.json"
            p.write_text(json.dumps(DEFAULT_PROFILE), encoding="utf-8")
            self.assertEqual(load_profile(p)["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
