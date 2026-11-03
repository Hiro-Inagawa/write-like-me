# 04. Rule Mining

How to derive style rules from statistics and existing rule files.

---

## Three sources, in order

### Source 1: Existing rule files

Read any rule files the user identified (feedback logs, correction notes, style guides, writing principles documents). Extract every stated prohibition or prescription:

- Prohibitions: "never use", "don't", "avoid", "remove", "not allowed"
- Prescriptions: "always", "use", "prefer", "make sure", "should"
- Corrections: "this is wrong / here is the right version"

These rules have the highest confidence. They represent explicit user intent rather than inference. Record the source for each.

---

### Source 2: Auto-derive from extreme statistics

Look for features at the extremes of the distribution. Thresholds:

| Finding | Candidate rule |
|---------|----------------|
| Feature count = 0 in primary register, corpus of 20,000 words or more | "never uses X" |
| Feature count = 0 in primary register, corpus under 20,000 words | provisional rule, "has not used X so far", marked for the author's confirmation |
| Feature rate < 0.5% when general English baseline is ~2–5% | "rarely uses X" |
| Feature rate > 5× general English baseline | "frequently uses X, more than typical" |
| 0% short sentences (≤5 words) | "no fragment sentences" (provisional below 20,000 words) |
| 100% long sentences (≥30 words) | "always writes in extended sentences" — unlikely, flag as anomaly |
| Booster tokens = 0 | "never uses empty intensifiers" |
| Contractions = 0 in the primary register (`contractions.count` and `contractions.per_100w` in the stylometry JSON), corpus of 20,000 words or more | candidate rule "no contractions", set as `contractions: forbidden` once the author confirms it. English only, a German corpus has no contraction measure |
| Contractions = 0 in the primary register, corpus under 20,000 words | the same candidate rule, provisional, marked for the author's confirmation |
| Contractions above 0 | no rule. Report the rate per 100 words so the author sees it |
| Hedging rate < 0.2/100w | "hedges sparingly; calibrated to actual uncertainty" |

The general English baseline comparison is approximate. For function words, use the Mosteller & Wallace (1964) frequency tables as baseline. For sentence length, educated English prose typically runs 18–25 words/sentence.

---

### Source 3: Negative space

Look for sentence shapes and patterns that are absent from the corpus:

- **Short sentences for effect.** Does the corpus have any isolated short sentences (< 8 words)? If not, "no staccato sentences for rhetorical punch."
- **Tricolon constructions.** Does the corpus have runs of three parallel items as a rhetorical device? Count instances of "X, Y, and Z" where all three are syntactically parallel. If rare or absent, "no tricolon constructions."
- **Rhetorical questions.** Count question marks. If few and only in actual inquiry (not setup), "no rhetorical questions."
- **Second-person instructions.** "You should..." in essay context. If absent, "no instructional second-person in formal prose."
- **Announcement colons.** "The result: X". If absent, "no announcement colons."

---

## Conflicts with the universal baseline

After the three sources, run `python scripts/corpus_conflicts.py <corpus>`. It applies the universal baseline to the author's own writing and lists every rule that blocks, with counts and examples. A block in the author's own text means the author uses a construction the baseline forbids, for example `not only ... but also`. Present each one in Stage 5 as a conflict and let the author decide. Keeping the habit becomes an entry in `rule_overrides` of `profile.json`. Dropping the habit leaves the rule in force.

---

## Provisional rules

An absence in a small sample is weak evidence. Eight essays with no sentence of five words or fewer do not show that the author never writes one. A corpus under 20,000 words therefore never produces a ban from a count of 0. Every rule that rests on a measured distribution is emitted as provisional. That covers a zero count, the sentence length ranges, the comma rate, the hedge density and the pronoun rates.

How a provisional rule is handled:

1. `voice_profile.py init` lists it under `provisional.rules` in `profile.json`. A zero semicolon count becomes `review` instead of `forbidden`, and a zero short-sentence target no longer lets a staccato run block. Drift lines that come from provisional targets are labelled `(provisional)`.
2. The emitted `02-corrective.md` lists it in a section named Provisional rules, with the evidence and the word count.
3. The author confirms it or drops it after seeing it applied to a new text. Confirming means removing its name from `provisional.rules`. Dropping means deleting the rule.

Rules from an existing rule file stay firm, because they come from the author's explicit statement and not from a count.

---

## What to do with candidate rules

For each candidate rule, record:
1. The rule itself ("never uses em dashes")
2. The source (rule file / statistic / negative space)
3. The evidence (quote from rule file, or stat value)
4. Confidence (high = explicit statement or 0-count; medium = borderline stat; low = inference)

Present all candidate rules to the user at Stage 5. The user approves, rejects, or refines each one.

Say what an answer changes before asking. A yes makes the rule a checker rule with the severity shown in the list. A no drops the rule, and the checker never applies it. Mark provisional rules as provisional in the list.

---

## Common false positives

Some auto-derived rules are false positives:

- **"Never uses second-person"** in a corpus of only formal essays. The corpus just didn't require second-person, not that the author can't use it.
- **"Never uses past tense"** in an essay about current research, a topic artifact.
- **"Uses 'that' 40% more than baseline"**, could be a topic effect if the corpus covers a specific subject with many subordinate clauses starting with "that."

The user review stage catches these.

---

## What not to include as rules

- Rules about content, argument, or research. The skill is about voice, not ideas.
- Rules derived from a single unusual sentence. One outlier is not a pattern.
- Rules that would make the voice impossible to use across topics ("never uses 'research'").
