import unittest

from voice_profile import DEFAULT_PROFILE, resolve_register
from voice_rules import run_rules
from voice_segment import segment


def hits_for(text, register=None, profile=None, kinds=None):
    profile = profile or DEFAULT_PROFILE
    reg = register or resolve_register(profile, profile.get("default_register", "default"))
    return run_rules(segment(text), profile, reg)


def rule_ids(text, **kw):
    return sorted({h.rule for h in hits_for(text, **kw)})


def forbidding(**overrides):
    reg = resolve_register(DEFAULT_PROFILE, "default")
    reg.update(overrides)
    return reg


class UniversalRuleTests(unittest.TestCase):
    def test_em_dash_blocks(self):
        hits = hits_for("The weights are fixed — but the execution is not.")
        self.assertEqual([h.rule for h in hits], ["EM_DASH"])
        self.assertEqual(hits[0].severity, "block")
        self.assertEqual(hits[0].line, 1)

    def test_double_hyphen_counts_as_em_dash(self):
        self.assertIn("EM_DASH", rule_ids("Fixed -- but not really."))

    def test_en_dash_range_is_fine(self):
        self.assertEqual(rule_ids("Between 2020–2024 the rate fell."), [])

    def test_stance_opener(self):
        self.assertIn("STANCE_OPENER", rule_ids("Importantly, the results held."))
        self.assertNotIn("STANCE_OPENER", rule_ids("The results were surprisingly stable."))

    def test_filler_opener(self):
        self.assertIn("FILLER_OPENER", rule_ids("It is worth noting that the data shows variation."))

    def test_performative_verb(self):
        self.assertIn("PERFORMATIVE_VERB", rule_ids("This paper delves into the relationship."))
        self.assertNotIn("PERFORMATIVE_VERB", rule_ids("This paper examines the relationship."))

    def test_not_only_but_also(self):
        self.assertIn("NOT_ONLY_BUT_ALSO", rule_ids("The model is not only accurate but also fast."))

    def test_summary_opener(self):
        self.assertIn("SUMMARY_OPENER", rule_ids("In conclusion, the approach works."))
        self.assertNotIn("SUMMARY_OPENER", rule_ids("The approach works. In conclusion sections we say so."))

    def test_evaluative_adjective_block_and_review(self):
        self.assertIn("EVALUATIVE_ADJECTIVE", rule_ids("This innovative approach reduces time."))
        soft = hits_for("This robust approach reduces time.")
        self.assertEqual(soft[0].rule, "EVALUATIVE_ADJECTIVE_SOFT")
        self.assertEqual(soft[0].severity, "review")

    def test_buildup_before_data(self):
        self.assertIn("BUILDUP_BEFORE_DATA", rule_ids("The data tell a consistent story: hedging ranged from 0 to 2.31."))
        self.assertNotIn("BUILDUP_BEFORE_DATA", rule_ids("Hedging ranged from 0 to 2.31 per 100 words."))

    def test_buildup_ignores_label_lines(self):
        self.assertEqual(rule_ids("Last verified: 2026-09-04"), [])
        self.assertEqual(rule_ids("Universal eval: 30 goldens, block recall 1.0."), [])
        self.assertIn("BUILDUP_BEFORE_DATA", rule_ids("The numbers tell the whole story here: 30 goldens passed."))

    def test_empty_intensifier(self):
        self.assertIn("EMPTY_INTENSIFIER", rule_ids("The pattern is clearly real and structured."))

    def test_hedge_connective_reviews_by_default(self):
        hits = hits_for("That said, the plan holds.")
        self.assertEqual(hits[0].rule, "HEDGE_CONNECTIVE")
        self.assertEqual(hits[0].severity, "review")

    def test_headings_are_checked_for_em_dash_only(self):
        self.assertEqual(rule_ids("# Results — summary"), ["EM_DASH"])
        self.assertEqual(rule_ids("# Honestly a heading"), [])


class ProfileRuleTests(unittest.TestCase):
    def test_semicolon_in_prose_when_forbidden(self):
        reg = forbidding(semicolons="forbidden")
        self.assertIn("SEMICOLON_PROSE", rule_ids("Two effects compound; each amplifies the other.", register=reg))
        self.assertEqual(rule_ids("- item one; item two", register=reg), [])
        self.assertEqual(rule_ids("Two effects compound. Each amplifies the other.", register=reg), [])

    def test_announcement_colon(self):
        reg = forbidding(announcement_colon="block")
        self.assertIn("ANNOUNCEMENT_COLON", rule_ids("The result is predictable: variation increases.", register=reg))
        self.assertEqual(rule_ids("Two respects: the cost and the time.", register=reg), [])
        self.assertEqual(rule_ids("The following three effects: cost and time.", register=reg), [])
        self.assertEqual(rule_ids("Status: Current", register=reg), [])
        self.assertIn("ANNOUNCEMENT_COLON", rule_ids("These results show one thing: the model fails.", register=reg))
        self.assertEqual(rule_ids("See https://example.com/x for the file.", register=reg), [])
        self.assertEqual(rule_ids("The meeting is at 14:30 today.", register=reg), [])

    def test_staccato_run(self):
        reg = forbidding()
        reg["targets"] = {"pct_short_le5_max": 0.0}
        hits = hits_for("The result is clear. Variation increases. This is the whole argument.", register=reg)
        self.assertEqual(hits[0].rule, "STACCATO_RUN")
        self.assertEqual(hits[0].severity, "block")
        self.assertEqual(rule_ids("The result is clear. Variation increases predictably across every condition we measured.", register=reg), [])

    def test_tricolon_is_review(self):
        hits = hits_for("The capabilities are the same, the knowledge the same, and the values the same.")
        self.assertTrue(any(h.rule == "TRICOLON" and h.severity == "review" for h in hits))

    def test_asyndetic_tricolon_is_review(self):
        hits = hits_for("The capabilities are the same, the knowledge the same, the apparent values the same.")
        self.assertTrue(any(h.rule == "TRICOLON" and h.severity == "review" for h in hits))
        self.assertEqual(rule_ids("We measured cost, time, scope."), [])

    def test_compressed_antithesis(self):
        self.assertIn("COMPRESSED_ANTITHESIS", rule_ids("Accuracy comes from structure, not prompting."))
        self.assertIn("COMPRESSED_ANTITHESIS", rule_ids("Engineered for citation rather than clicks."))

    def test_protest_framing(self):
        self.assertIn("PROTEST_FRAMING", rule_ids("None of this is invented from scratch."))

    def test_contractions_when_forbidden(self):
        reg = forbidding(contractions="forbidden")
        self.assertIn("CONTRACTION", rule_ids("It's done and we don't need more.", register=reg))
        self.assertEqual(rule_ids("Its cover is done and the team's plan holds.", register=reg), [])
        self.assertEqual(rule_ids("It's done.", register=forbidding()), [])

    def test_questions_when_forbidden(self):
        reg = forbidding(questions="forbidden")
        hits = hits_for("Why does this matter? Because it compounds.", register=reg)
        self.assertEqual(hits[0].rule, "RHETORICAL_QUESTION")
        self.assertEqual(hits[0].severity, "review")

    def test_meta_commentary_when_blocked(self):
        reg = forbidding(meta_commentary="block")
        self.assertIn("META_COMMENTARY", rule_ids("Great question, let me know if you need more.", register=reg))

    def test_extra_phrases_from_profile(self):
        profile = dict(DEFAULT_PROFILE)
        profile["bans"] = dict(DEFAULT_PROFILE["bans"], extra_phrases=["at the end of the day"])
        self.assertIn("EXTRA_PHRASE", rule_ids("At the end of the day it works.", profile=profile))


if __name__ == "__main__":
    unittest.main()
