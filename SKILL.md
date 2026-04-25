---
name: write-like-me
description: Use when writing or revising prose, or when building a new writing voice from a corpus. On invoke: checks the voices/ folder. If voices exist, routes to writing mode. If none exist, starts the 7-stage voice-building workflow. Supports multiple named voices — one per author, register, or style.
---

# Write Like Me

A single skill with two modes:

- **Build mode** — no voice profile exists yet. Runs a 7-stage workflow: analyzes your writing corpus using linguistic and psychological measurement methods, mines your style rules, and generates a personalized voice profile saved to `voices/<name>/`.
- **Write mode** — a voice profile exists. Reads it and writes or revises prose in that voice. The universal anti-AI baseline (`references/00-universal-baseline.md`) is always active, on top of whatever the voice profile specifies.

Multiple voices are supported. Each voice is a named subfolder in `voices/`. You can have one for your own writing, one for a different register, one built from an admired author's work.

---

## Session start — mode detection

On every invoke:

1. Check the `voices/` directory.
2. If **empty**: say "No voice profiles found. I can build one from your writing corpus — do you want to start?" then begin Stage 1.
3. If **one voice exists**: say "Found voice: [name]. Write using it, or build a new one?" Wait for choice.
4. If **multiple voices exist**: list them. Ask which to write in, or whether to build a new one. Wait for choice.

---

## Write mode

When a voice is selected:

1. Read `voices/<name>/01-generative.md` — positive patterns, quantitative targets, exemplars.
2. Read `voices/<name>/02-corrective.md` — hard bans, scan checklist.
3. Read `references/00-universal-baseline.md` — always active, applies to every voice.
4. State in one sentence what you will write or revise. Wait for confirmation.

After delivering prose:

- Scan against `voices/<name>/02-corrective.md` and `references/00-universal-baseline.md`.
- Fix any hard ban before sending.

---

## Build mode — 7-stage workflow

### Stage 1 — Discover

Read `references/01-corpus-discovery.md`.

Ask the user three questions in one message:

1. **What is the corpus?** Their own writing: a folder path, a list of files, or a description of what to look for. Or an admired author's published work they want to analyze as an influence layer.
2. **Are there conversation exports to include?** (e.g., Claude.ai exports, ChatGPT history exports) If yes, what marker identifies their turns? (e.g., `## You`, `**User:**`)
3. **Are there existing style notes, corrections, or rule files to incorporate?**

Also confirm: is this writing theirs, or do they have permission to analyze it?

**Corpus type matters:**
- **Own writing** → sets hard rules (what they never do, what they actually do). The floor.
- **Admired author** → sets an influence layer (positive patterns to reach toward). Not hard rules.

State what was found and ask for confirmation before proceeding.

### Stage 2 — Extract and Preview

Read `references/02-author-filtering.md`.

For conversation exports: run `scripts/extract_author_turns.py` with the confirmed author marker. Show 5 random extracted samples and confirm the filter worked. Flag:
- Extracted content < 10% of source file (filter may be wrong)
- Content contains AI-output markers ("I'll help you", "Certainly!", "Here's a")
- Total corpus < 20,000 words after filtering (warn: distributions unreliable below this)

For prose files: confirm file count and approximate word count.

### Stage 3 — Analyze

Run `scripts/stylometry.py` over the full filtered corpus and over each register subset separately (e.g., formal essays, casual writing, conversation).

For each register:
```
python scripts/stylometry.py <path> --register <name> --output voices/<name>/<register>.json
```

Report word counts per register and any warnings.

### Stage 4 — Mine Rules

Read `references/04-rule-mining.md`.

Three sources, in order:

1. **Existing rule files** — read verbatim, extract every stated rule, correction, prohibition.
2. **Extreme statistics** — feature usage at < 0.5% or > 5× general-English baseline → candidate rule.
3. **Negative space** — sentence shapes never used, connective patterns absent, lengths never reached.

Compile candidate rules.

### Stage 5 — Review (STOP — wait for user)

Present mined rules as a numbered checklist. For each: state the rule and its evidence source.

Ask the user to:
- Mark false positives
- Add missing rules
- Confirm register labels

Do not proceed until the user responds.

### Stage 6 — Emit

Read `references/05-exemplar-selection.md` and `references/06-skill-emission.md`.

Using the approved rules and corpus statistics:

1. Select 3–5 exemplar passages from the corpus
2. Write the voice profile to `voices/<name>/` using the templates:
   - `voices/<name>/01-generative.md`
   - `voices/<name>/02-corrective.md`
   - `voices/<name>/03-corpus-source.md`
3. Write the standalone stylometric report to the corpus root
4. Write `voices/<name>/claude-ai-skill.md` using `templates/generated-claude-ai-skill.md`. This file is self-contained: all rules, patterns, and exemplars are inlined directly with no references to external files. It is ready to upload to Claude.ai → Settings → Customize → Skills, or to paste into the Skills instruction field.

Ask if the user wants to inspect any file before verification.

### Stage 7 — Verify

Read `references/07-verification.md`.

Hold out 2–3 corpus samples not used as exemplars. Generate text on the same topics using the new voice. Compare:

| Check | Pass condition |
|-------|---------------|
| Em-dash count | Matches corpus (usually 0) |
| Semicolon count | Matches corpus |
| Sentence length distribution | Within ±20% of corpus mean |
| Hedging density | Within ±30% of corpus rate |
| Hard-ban violations | Zero |

Report pass/fail. Flag any rule that needs sharpening.

---

## Routing table

| Task | Read |
|------|------|
| Writing new prose | `voices/<name>/01-generative.md` + `references/00-universal-baseline.md` |
| Revising prose | `voices/<name>/02-corrective.md` + `references/00-universal-baseline.md` |
| Finding corpus sources | `references/01-corpus-discovery.md` |
| Filtering conversation exports | `references/02-author-filtering.md` |
| Understanding measured features | `references/03-methodology.md` |
| Mining rules | `references/04-rule-mining.md` |
| Selecting exemplars | `references/05-exemplar-selection.md` |
| Emitting the voice profile | `references/06-skill-emission.md` |
| Verifying the generated profile | `references/07-verification.md` |
| Re-running on updated corpus | `references/08-regeneration-and-diff.md` |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/stylometry.py` | Feature extraction — stdlib base, textstat optional, spaCy optional |
| `scripts/extract_author_turns.py` | Extract author-only turns from conversation export markdown |
| `scripts/generate_report_from_json.py` | Combine JSON profiles into a human-readable report |

---

## What this skill does not do

- Does not generate ideas, arguments, or research — it captures and applies how someone writes, not what they write about
- Does not compare against external benchmarks or evaluate quality in the abstract
- Does not handle non-English writing conventions
- Does not invent exemplars — all exemplars come from the actual corpus
