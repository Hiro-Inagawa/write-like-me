# Write Like Me

A Claude Code skill that analyzes how you write and generates a personalized voice profile for writing and revising prose. Uses linguistic and psychological measurement methods — not subjective descriptions — to capture your actual style from a corpus of your own writing.

The same skill supports multiple voices. One profile for your own writing, another for a different register, another built from an author whose style you want to study. You switch between them within the same skill.

## How it works

Two modes, one skill:

**No voice built yet** — the skill runs a 7-stage analysis: it discovers your corpus, extracts and filters the text, measures approximately 50 stylometric features per register, mines rules from the measurements and any existing style notes, pauses for your review, generates the voice profile, and runs a held-out verification test.

**Voice already built** — the skill reads your profile and writes or revises prose in that voice. The universal anti-AI baseline (`references/00-universal-baseline.md`) is always active, on top of whatever your profile specifies.

## What gets measured

The analysis covers approximately 50 features across four categories:

**Lexical** — type-token ratio (MATTR, window 100), function word frequencies, hapax legomena ratio, distinctive content words against a general-English baseline.

**Syntactic** — sentence length distribution (mean, median, standard deviation, quartiles), comma rate per sentence, em-dash / semicolon / colon / parenthetical rates per 1,000 words, concession rate, sentence-initial word patterns.

**Hedging and stance** — hedging token density (might, perhaps, possibly, roughly, appears to), booster token density (clearly, certainly, definitely, very), first-person singular and plural rates, second-person rate.

**Structural** — paragraph length distribution, heading density, bullet ratio.

Optional tiers: readability scores (Flesch-Kincaid, Gunning Fog) with `textstat`; POS-rhythm, dependency depth, passive voice rate with `spaCy`.

Academic grounding for all features is in `references/03-methodology.md`.

## What you need

- [Claude Code](https://claude.ai/code)
- Python 3.8+
- A writing corpus — 20,000 words minimum; 50,000+ recommended for reliable distributions

**Sources the skill accepts:**

| Source | What it provides |
|--------|-----------------|
| Your own essays, articles, papers | Primary corpus — sets hard rules |
| Claude.ai or ChatGPT conversation exports | Conversational register — your turns only, filtered by author marker |
| Notes, journals, emails | Informal register |
| A published author's work you admire | Influence layer — sets positive patterns, not hard rules |
| Existing style rule files or correction logs | Incorporated directly into rule mining |

## Installation

Copy the `write-like-me/` folder into your Claude Code skills directory:

```
~/.claude/skills/write-like-me/
```

Invoke in any Claude Code session:

```
/write-like-me
```

## Exporting your conversations

**Claude.ai:** Go to Settings → Data Controls → Export Data. You receive a zip file containing your conversation history. The extraction script accepts the exported JSON directly with `--format claude`.

**ChatGPT:** Go to Settings → Data Controls → Export Data. Use `--format chatgpt`.

The script `scripts/extract_author_turns.py` filters to your turns only using a configurable author marker. The skill shows you 5 random samples and waits for your confirmation before analysis proceeds.

## Python dependencies

The base analysis runs on Python stdlib only — no installs required.

Optional (install via `pip install -r scripts/requirements.txt`):

| Package | Adds |
|---------|------|
| `textstat` | Readability scores |
| `spacy` + `en_core_web_sm` | POS-rhythm, dependency depth, passive voice rate |

## Output

Running the analysis produces:

```
voices/<your-name>/
  01-generative.md      # Quantitative targets, structural patterns, exemplars — read when writing
  02-corrective.md      # Hard bans, soft checks, mechanical scan table — read after writing
  03-corpus-source.md   # Provenance: what was analyzed, when, with what filters

_STYLE-PROFILE-<DATE>.md   # Human-readable stylometric report (place this wherever you like)
```

**Report structure:**
- Cross-register comparison table (all measured features across all registers)
- Per-register breakdown (sentence length distribution, function word frequencies, punctuation rates, hedging/booster density, pronoun rates)
- Notes on interpretation (which register is the primary target, what zero counts mean, corpus limitations)
- Provenance and re-run instructions

## Universal baseline

Every voice inherits a set of zero-tolerance rules for patterns that AI systems produce by default and that human writers do not. These are in `references/00-universal-baseline.md` and are active regardless of what any individual voice profile specifies.

The baseline covers: em dashes as clause separators, stance adverbials ("Importantly,", "Notably,"), filler openers ("It is worth noting that"), unsupported evaluative adjectives ("innovative", "robust"), and performative verb choices ("delve", "leverage", "foster"). These patterns appear in AI-generated text at rates far above any individual human writer's baseline. Removing them is a prerequisite for the voice profile to be meaningful.

## File structure

```
write-like-me/
  README.md
  SKILL.md                          # Mode detection, routing, 7-stage workflow
  references/
    00-universal-baseline.md        # Anti-AI-tell rules — always active
    01-corpus-discovery.md          # What makes a good corpus; consent guardrail
    02-author-filtering.md          # Filtering exports; preview/confirm step
    03-methodology.md               # Full academic grounding for all features
    04-rule-mining.md               # Three rule sources: files, stats, negative space
    05-exemplar-selection.md        # How to select and annotate exemplars
    06-skill-emission.md            # What goes in each generated file
    07-verification.md              # Held-out generation test protocol
    08-regeneration-and-diff.md     # Re-run protocol when corpus grows
  scripts/
    stylometry.py                   # Feature extraction
    extract_author_turns.py         # Author-turn filter for conversation exports
    generate_report_from_json.py    # Report generator from JSON profiles
    requirements.txt                # Optional Python dependencies
  templates/
    generated-01-generative.md      # Skeleton for write-time guidance
    generated-02-corrective.md      # Skeleton for post-write checklist
    generated-03-corpus-source.md   # Skeleton for provenance file
    style-profile-report.md         # Skeleton for the standalone report
  voices/                           # Your voice profiles live here (not committed to git)
```

## License

MIT
