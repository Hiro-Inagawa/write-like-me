# 07 — Verification

How to confirm the generated skill actually produces text that matches the corpus.

---

## The problem with "does this sound right?"

Qualitative impressions of style are unreliable. The author may feel the generated text "sounds like me" when it doesn't match their measured profile, or vice versa. Verification requires falsifiable checks.

---

## Held-out samples

During Stage 5 (rule review), identify 2–3 paragraphs from the primary register corpus that were NOT selected as exemplars. These are the held-out test samples.

Each held-out sample should:
- Be representative of the primary register (not an unusual section)
- Be a complete paragraph, not a sentence fragment
- Cover a topic different from any of the selected exemplars

---

## Generation test

Using the generated skill in a fresh session (no prior context):

1. Give Claude a topic prompt that is similar to the held-out sample but not the same sentence.
2. Ask Claude to write one paragraph using the voice skill.
3. Do not show Claude the held-out sample during generation.

Example: if the held-out sample is about stochastic individuality in AI, the test prompt might be "Write a paragraph about how small initial differences compound over time in complex systems."

---

## Falsifiable checks

Compare the generated paragraph against the held-out sample on these metrics:

| Check | Pass condition |
|-------|----------------|
| Em dashes | Generated count matches corpus rule (0 if rule says zero) |
| Semicolons | Generated count matches corpus rule (0 if rule says zero) |
| Announcement colons | Generated count matches corpus rule |
| Mean sentence length | Within ±10 words of corpus mean |
| Short sentences | No consecutive short sentences if corpus shows none |
| Boosters | Zero if corpus shows zero boosters in primary register |
| Hedge density | Within 0.1/100w of corpus mean |
| Concession rate | Generated paragraph has at least one "but/however/though" construction if corpus concession rate > 0.15 |

---

## Reporting

Report each check as pass or fail. For failed checks, state:
- What the corpus says (the target)
- What the generated text produced
- Which specific rule needs to be sharpened in `02-corrective.md` to catch this

---

## Iteration

If more than one check fails, revise the relevant file and run one more generation test. Do not iterate more than twice — if the skill fails repeatedly on the same check, the rule may need to be rephrased as a harder constraint rather than a soft guide.

---

## What verification does not test

- Whether the generated text is good writing — that is the author's judgment
- Whether the voice is indistinguishable from the author — stylometric methods have detection limits
- Whether the skill handles unusual registers or edge cases — it is calibrated to the primary register only
