# 04 — Rule Mining

How to derive style rules from statistics and existing rule files.

---

## Three sources, in order

### Source 1: Existing rule files

Read any rule files the user identified (feedback logs, correction notes, style guides, writing principles documents). Extract every stated prohibition or prescription:

- Prohibitions: "never use", "don't", "avoid", "remove", "not allowed"
- Prescriptions: "always", "use", "prefer", "make sure", "should"
- Corrections: "this is wrong / here is the right version"

These rules have the highest confidence — they represent explicit user intent rather than inference. Record the source for each.

**For Hiro's first-run, known source files:**
- `memory/feedback_punctuation.md` — zero em-dashes, zero semicolons
- `memory/feedback_colon_style.md` — no announcement colons, no empty intensifiers
- `__KAIRO/SELF/07_CORRECTIONS.md` — correction log with examples

---

### Source 2: Auto-derive from extreme statistics

Look for features at the extremes of the distribution. Thresholds:

| Finding | Candidate rule |
|---------|----------------|
| Feature count = 0 in primary register | "never uses X" |
| Feature rate < 0.5% when general English baseline is ~2–5% | "rarely uses X" |
| Feature rate > 5× general English baseline | "frequently uses X, more than typical" |
| 0% short sentences (≤5 words) | "no fragment sentences" |
| 100% long sentences (≥30 words) | "always writes in extended sentences" — unlikely, flag as anomaly |
| Booster tokens = 0 | "never uses empty intensifiers" |
| Hedging rate < 0.2/100w | "hedges sparingly; calibrated to actual uncertainty" |

The general English baseline comparison is approximate. For function words, use the Mosteller & Wallace (1964) frequency tables as baseline. For sentence length, educated English prose typically runs 18–25 words/sentence.

---

### Source 3: Negative space

Look for sentence shapes and patterns that are absent from the corpus:

- **Short sentences for effect.** Does the corpus have any isolated short sentences (< 8 words)? If not, "no staccato sentences for rhetorical punch."
- **Tricolon constructions.** Does the corpus have runs of three parallel items as a rhetorical device? Count instances of "X, Y, and Z" where all three are syntactically parallel. If rare or absent, "no tricolon constructions."
- **Rhetorical questions.** Count question marks. If few and only in genuine inquiry (not setup), "no rhetorical questions."
- **Second-person instructions.** "You should..." in essay context. If absent, "no instructional second-person in formal prose."
- **Announcement colons.** "The result: X". If absent, "no announcement colons."

---

## What to do with candidate rules

For each candidate rule, record:
1. The rule itself ("never uses em dashes")
2. The source (rule file / statistic / negative space)
3. The evidence (quote from rule file, or stat value)
4. Confidence (high = explicit statement or 0-count; medium = borderline stat; low = inference)

Present all candidate rules to the user at Stage 5. The user approves, rejects, or refines each one.

---

## Common false positives

Some auto-derived rules are false positives:

- **"Never uses second-person"** in a corpus of only formal essays — the corpus just didn't require second-person, not that the author can't use it.
- **"Never uses past tense"** in an essay about current research — topic artifact.
- **"Uses 'that' 40% more than baseline"** — could be a topic effect if the corpus covers a specific subject with many subordinate clauses starting with "that."

The user review stage catches these.

---

## What not to include as rules

- Rules about content, argument, or research — the skill is about voice, not ideas.
- Rules derived from a single unusual sentence — one outlier is not a pattern.
- Rules that would make the voice impossible to use across topics ("never uses 'research'").
