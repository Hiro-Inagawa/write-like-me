![Write Like Me. Rows of robots writing at desks under a neon sign reading WRITE LIKE ME](docs/write-like-me.webp)

[![checks](https://github.com/Hiro-Inagawa/write-like-me/actions/workflows/checks.yml/badge.svg)](https://github.com/Hiro-Inagawa/write-like-me/actions/workflows/checks.yml)

**Try it in ten seconds.** Clone the repo and run the checker on any Markdown or text file. No profile, no installs, Python 3.8+ only:

    python scripts/voice_check.py your-draft.md

It prints every em dash, filler phrase, hedge, and AI tell with a line number and a fix, then a verdict. Building your own voice profile comes after, if you want it.

A Claude Code skill that analyzes how you write and generates a personalized voice profile for writing and revising prose. It uses linguistic and psychological measurement methods rather than subjective descriptions to capture your actual style from a corpus of your own writing.

**New in v3 (October 2026).** The skill now teaches the method as well as measuring the result. For every text that a reader will see, it works in two messages. The first explains the subject to the author in plain paragraphs. The second, sent after approval, is the text, cut from that explanation. The checker gained six reader-text rules, a check that the text contains no number or name that the explanation lacked, and a check that a rejected phrase does not return. Claude Code hooks run the method and the checker without a reminder. Details are in the sections "The two messages", "New checks in v3", "Hooks for Claude Code" and "Provisional rules", and in [CHANGELOG.md](CHANGELOG.md).

**New in v2 (September 2026).** The skill now ships a deterministic checker. After a draft is written, `python scripts/voice_check.py draft.md --profile voices/<name>/profile.json` reports every violation with a line number and a fix, and exits non-zero on a hard rule, so the voice is enforced by code instead of by asking the model to be careful. Each voice also gets a machine-readable `profile.json` and a golden test set, and an eval harness gates every rule change. Details are in the sections "Checking a draft" and "Evaluating the checker" below, and in [CHANGELOG.md](CHANGELOG.md).

The same skill supports multiple voices. You can build one from your primary writing register, another from a different register, and another from an author whose style you want to study, and switch between them within the same skill.

---

## HOW IT WORKS

The skill has two modes.

When no voice is built yet, it runs a 7-stage analysis that discovers your corpus, extracts and filters the text, measures approximately 50 stylometric features per register, mines rules from the measurements and any existing style notes, pauses for your review, generates the voice profile, and runs a held-out verification test.

When a voice is already built, it reads your profile and writes or revises prose in that voice. The universal anti-AI baseline (`references/00-universal-baseline.md`) is always active, on top of whatever your profile specifies.

---

## GETTING STARTED

**Step 1. Gather your writing corpus.**

Create a folder and put your writing in it. Good sources:
- Export your Claude conversation history: Settings → Data Controls → Export Data, then unzip the file into the folder
- Emails you have written
- Essays, articles, blog posts, papers
- Notes, journals, or any other text in your own voice

Reliable distributions need 20,000 words. Below 5,000 words the build stops. Between 5,000 and 20,000 words the build continues and every distribution rule is provisional. 50,000 words or more gives more reliable results.

**Step 2. Run the skill.**

Open any Claude Code session and run `/write-like-me`. The skill will ask where your corpus lives, run the analysis, and show you the mined rules for your review before writing anything. Once you confirm, it writes your voice profile and a standalone report to the folder you specify.

**Step 3. Write.**

From this point on, run `/write-like-me` whenever you want to write or revise prose. The skill detects that a voice is already built and goes straight to writing mode.

**Optional: Build more profiles.**

You can have as many profiles as you want, each stored under its own name in the `voices/` folder. Some ideas:
- A profile for professional writing
- A profile for email
- A profile for social media
- A profile built from a published author whose style you want to study (the skill treats their patterns as an influence layer, not hard rules)

Name the profile when you invoke the skill and it switches automatically.

---

## THE TWO MESSAGES

A text written straight to a format, such as "portfolio copy" or "cover letter", sounds like the format. A text that is cut from an explanation to the author sounds like the author. `references/09-how-to-write.md` describes the method, and write mode follows it.

1. **Message one.** Read the real source. Explain the subject to the author in chat, in plain paragraphs, with the actual feature, the actual number and one example. The author approves it or corrects it.
2. **Message two.** Cut the approved explanation down to the target. A sentence in the text that was not in the explanation is a defect.

The explanation step can be turned off, and it is on by default. For one text, the author says "just write it" or "skip the explanation", and "explain first" turns it back on. For a voice, `"explainFirst": false` in `voices/<name>/hook.json` turns it off, and the environment variable `WRITE_LIKE_ME_EXPLAIN` set to `off` or `on` wins over that file. With the step off, the text is written directly from the request and the real source. The other rules stay. Nothing is added that the request or the source did not contain, and the checker runs before the text is shown, without `--explanation`.

The file also lists the moves that are never allowed and the rules for working with the author: one piece at a time, the author's text as the base, a question answered without action, and a review against every earlier correction before the draft is shown.

## NEW CHECKS IN V3

| Rule id | Flags | Default |
|---------|-------|---------|
| `CLOSING_CAVEAT` | A final paragraph or last sentences that open with a caveat phrase such as keep in mind or note that | review |
| `COMPRESSED_ANTITHESIS` | A ", not X" or "rather than" tail in a short line, a heading or a label, and a short closing ", not X." | review |
| `BENEFIT_TAIL` | A sentence ending in so you can, which lets you, helping you, allowing you, or ensuring | review |
| `TAGLINE` | A short prose line of abstract nouns with no verb | review |
| `LENGTH_BAND` | Word count outside `register.length` (`min`, `max`) | block when both are set |
| `ADDITION` | A number or name in the draft that the file passed with `--explanation` lacks | review |
| `REPEATED_PHRASE` | A phrase from the file passed with `--rejected` | block |
| `TRICOLON` | Three parallel items, now reported only | info |

The severity of each rule is set per register in `profile.json`. `info` hits appear in the output and leave the verdict alone.

    python scripts/voice_check.py draft.md --profile voices/<name>/profile.json --explanation explanation.md --rejected rejected.txt

## HOOKS FOR CLAUDE CODE

`scripts/writing-gate-hook.mjs` runs in two modes. The `prompt` mode adds the method to the context when a prompt asks for a text that a reader will see. The `post-write` mode runs the checker on every reader text that was just written and blocks on `VOICE_CHECK_BLOCK`. It needs Node and no packages. When `hook.json` names `explanationFile` and `rejectedFile`, or the environment variables `WRITE_LIKE_ME_EXPLANATION` and `WRITE_LIKE_ME_REJECTED` are set, the hook passes both files to the checker, and a REVIEW verdict prints the drift lines next to the review hits. The voice folder is `voices/<name>/` inside the skill folder, and any other location works through `WRITE_LIKE_ME_PROFILE`. The exact `settings.json` entries and the `hook.json` options are in `references/10-hooks.md`. Run `node --test tests/*.test.mjs` to test the hook.

## PROVISIONAL RULES

A count of 0 in a small corpus is weak evidence. Reliable distributions need 20,000 words and the floor is 5,000 words, below which the build stops. Between 5,000 and 20,000 words the build still runs and every rule that rests on a distribution is written as provisional. `profile.json` lists them under `provisional`, `02-corrective.md` has a section for them, and drift lines that come from them are labelled. A zero semicolon count becomes `review` and no longer `forbidden`. A rule stops being provisional when the author confirms it against a new text and removes its name from the list. Run `python scripts/voice_profile.py preflight --corpus-words N` before the analysis to see this and the missing optional packages up front.

## VERIFYING A VOICE

Stage 7 no longer needs any particular agent. Generate a paragraph per held-out topic with the agent you already use, save each to a file, and run:

    python eval/voice_eval.py verify --strict --profile voices/<name>/profile.json sample-1.md sample-2.md

`--strict` is the default for your own rules, because it fails a sample on a review hit as well as on a block hit. Before the voice is emitted, `python scripts/corpus_conflicts.py <corpus>` runs the universal baseline over your own writing and lists every rule that blocks, so that you decide each conflict.

The hedge tolerance that this step applies is one value in the profile, `thresholds.hedge_tolerance`.

---

## WHAT GETS MEASURED

The analysis covers approximately 50 features across four categories.

**Lexical:**<br>
Type-token ratio (MATTR, window 100), function word frequencies, hapax legomena ratio, distinctive content words against a general-English baseline.

**Syntactic:**<br>
Sentence length distribution (mean, median, standard deviation, quartiles), comma rate per sentence, em-dash / semicolon / colon / parenthetical rates per 1,000 words, concession rate, sentence-initial word patterns.

**Hedging and stance:**<br>
Hedging token density (might, perhaps, possibly, roughly, appears to), booster token density (`clearly`, certainly, definitely, very), first-person singular and plural rates, second-person rate.

**Structural:**<br>
Paragraph length distribution, heading density, bullet ratio.

Two optional tiers add readability scores (Flesch-Kincaid, Gunning Fog) via `textstat`, and POS-rhythm, dependency depth, and passive voice rate via `spaCy`. Academic grounding for all features is in `references/03-methodology.md`.

---

## WHAT YOU NEED

- [Claude Code](https://claude.ai/code)
- Python 3.8+
- A writing corpus of at least 20,000 words for reliable distributions (5,000 words is the floor below which the build stops, and 50,000 words or more gives more reliable results)

The draft checker (`voice_check.py`) needs only Python 3.8+. It has no installs and no dependencies of its own.

The skill accepts writing from any of these sources:

| Source | What it provides |
|--------|-----------------|
| Your own essays, articles, papers | Primary corpus. Drives the hard rules. |
| Claude.ai or ChatGPT conversation exports | Conversational register, extracted to your turns only using a configurable author marker |
| Notes, journals, emails | Informal register |
| A published author's work you admire | Influence layer. Sets positive patterns rather than hard rules. |
| Existing style rule files or correction logs | Incorporated directly into rule mining |

---

## INSTALLATION

Copy the `write-like-me/` folder into your Claude Code skills directory:

```
~/.claude/skills/write-like-me/
```

Invoke in any Claude Code session:

```
/write-like-me
```

---

## EXPORTING YOUR CONVERSATIONS

**Claude.ai.** Go to Settings → Data Controls → Export Data. You receive a zip file containing your conversation history. The extraction script accepts the exported JSON directly with `--format claude`.

**ChatGPT.** Go to Settings → Data Controls → Export Data. Use `--format chatgpt`.

The script `scripts/extract_author_turns.py` filters to your turns only using a configurable author marker. The skill shows you 5 random samples and waits for your confirmation before analysis proceeds.

---

## PYTHON DEPENDENCIES

The base analysis runs on Python stdlib only, with no installs required.

Two optional packages add extended features (install via `pip install -r scripts/requirements.txt`):

| Package | Adds |
|---------|------|
| `textstat` | Readability scores |
| `spacy` + `en_core_web_sm` | POS-rhythm, dependency depth, passive voice rate |

---

## OUTPUT

Running the analysis produces seven files per voice profile, plus a standalone report:

```
voices/<your-name>/
  01-generative.md       # Quantitative targets, structural patterns, exemplars, useful when writing
  02-corrective.md       # Hard bans, soft checks, mechanical scan table, useful after writing
  03-corpus-source.md    # Provenance, what was analyzed, when, with what filters
  claude-ai-skill.md     # Self-contained export for Claude.ai Skills upload
  profile.json            # Rules for the draft checker, in machine-readable form
  goldens.jsonl            # Golden examples for evaluating the checker against this voice
  eval-baseline.json       # Recorded metrics the checker is graded against on future changes

  _STYLE-PROFILE-<DATE>.md # Human-readable stylometric report, written next to the profile
```

The `claude-ai-skill.md` file is ready to use in Claude.ai immediately after the build completes. To add it:

1. Go to Claude.ai → Settings → Customize → Skills
2. Either upload `claude-ai-skill.md` directly, or open the file and paste its contents into the instruction field
3. Save. Claude.ai will apply your voice rules in every conversation where the skill is active.

Unlike the Claude Code skill files, `claude-ai-skill.md` has no external dependencies. All rules, patterns, and exemplars are inlined in a single file.

The standalone report includes:
- Cross-register comparison table (all measured features across all registers)
- Per-register breakdown (sentence length distribution, function word frequencies, punctuation rates, hedging and booster density, pronoun rates)
- Notes on interpretation (which register is the primary target, what zero counts mean, corpus limitations)
- Provenance and re-run instructions

---

## CHECKING A DRAFT

Every voice now ships with a deterministic checker. Run it on any draft:

    python scripts/voice_check.py draft.md --profile voices/<your-name>/profile.json

It prints every hit with a line number and a fix, then a verdict. `block` hits are zero-tolerance rules from your profile and the universal baseline. `review` hits are patterns with documented exceptions, so you decide. The exit code is 1 on a block, which makes the checker usable as a gate in scripts, hooks, and CI. Without `--profile` it runs the universal anti-AI baseline only, which works on any text.

## EVALUATING THE CHECKER

The checker is itself tested against golden passages, so a rule change cannot silently loosen or over-flag:

    python eval/voice_eval.py score --goldens eval/goldens/universal.goldens.jsonl --gate eval/baselines/universal.json

The reader-text rules have their own goldens and baseline:

    python eval/voice_eval.py score --goldens eval/goldens/reader.goldens.jsonl --gate eval/baselines/reader.json

Each voice gets its own `goldens.jsonl` built from the rule examples you approved during the build. The metrics that matter are `block_recall` (does it catch what it must) and `false_alarm_rate` (does it flag what it must not).

---

## UNIVERSAL BASELINE

Every voice inherits a set of zero-tolerance rules for patterns that AI systems produce by default and that human writers do not. These are in `references/00-universal-baseline.md` and are active regardless of what any individual voice profile specifies.

The baseline removes em dashes as clause separators, stance adverbials (`Importantly,`, `Notably,`), filler openers (`It is worth noting that`), unsupported evaluative adjectives (`innovative`, `robust`), and performative verb choices (`delve`, `leverage`, `foster`). These patterns appear in AI-generated text at rates far above any individual human writer's baseline, and removing them is a prerequisite for the voice profile to be meaningful.

---

## FILE STRUCTURE

```
write-like-me/
  README.md
  SKILL.md                          # Mode detection, routing, 7-stage workflow
  references/
    00-universal-baseline.md        # Anti-AI-tell rules, always active
    01-corpus-discovery.md          # What makes a good corpus; consent guardrail
    02-author-filtering.md          # Filtering exports; preview/confirm step
    03-methodology.md               # Full academic grounding for all features
    04-rule-mining.md               # Three rule sources: files, stats, negative space
    05-exemplar-selection.md        # How to select and annotate exemplars
    06-skill-emission.md            # What goes in each generated file
    07-verification.md              # Held-out generation test protocol
    08-regeneration-and-diff.md     # Re-run protocol when corpus grows
    09-how-to-write.md              # The two-message method for any text a reader will see
    10-hooks.md                     # Claude Code hook setup
  scripts/
    stylometry.py                   # Feature extraction
    extract_author_turns.py         # Author-turn filter for conversation exports
    generate_report_from_json.py    # Report generator from JSON profiles, writes into the voice folder
    corpus_conflicts.py             # Lists where the author's own writing breaks the universal baseline
    voice_segment.py                # Markdown draft to prose segments, with line numbers
    voice_rules.py                  # Deterministic detectors, parameterized by profile
    voice_profile.py                # Load, validate, and initialize profile.json
    voice_rules_reader.py           # Reader-text rules added in v3
    voice_check.py                  # CLI checker, prints hits and a verdict, sets exit code
    writing-gate-hook.mjs           # Claude Code hooks, prompt and post-write
    requirements.txt                # Optional Python dependencies
  eval/
    voice_eval.py                   # Scores goldens, saves baselines, runs the regression gate
    README.md                       # Golden format and metrics
    goldens/
      universal.goldens.jsonl       # Ships with the repo
      reader.goldens.jsonl          # Reader-text rule goldens, made-up passages
    baselines/
      universal.json                # Ships with the repo
      reader.json                   # Ships with the repo
  tests/                            # Unit tests, fixtures, and a negative control for the checker
  templates/
    generated-01-generative.md      # Skeleton for write-time guidance
    generated-02-corrective.md      # Skeleton for post-write checklist
    generated-03-corpus-source.md   # Skeleton for provenance file
    generated-claude-ai-skill.md    # Skeleton for the Claude.ai Skills export
    generated-goldens.jsonl         # Skeleton for a voice's goldens file
    profile.schema.json             # Documented shape of profile.json
    style-profile-report.md         # Skeleton for the standalone report
  voices/                           # Your voice profiles live here (not committed to git)
    <your-name>/
      01-generative.md              # Write-time guidance (Claude Code)
      02-corrective.md              # Post-write checklist (Claude Code)
      03-corpus-source.md           # Provenance (Claude Code)
      claude-ai-skill.md            # Self-contained export for Claude.ai Skills
      profile.json                  # Rules for the draft checker
      goldens.jsonl                 # Golden examples for evaluating the checker
      eval-baseline.json            # Recorded metrics for the regression gate
      hook.json                     # Optional path rules for the Claude Code hooks
```

---

## LICENSE

MIT
