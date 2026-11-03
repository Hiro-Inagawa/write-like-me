---
name: write-like-me
version: 3.2.0
description: Use when writing or revising prose for a reader (emails, cover letters, form-field answers, profile texts, portfolio pages, listing and README prose), when asked about such a text, or when building a new writing voice from a corpus. On invoke: checks the voices/ folder. If voices exist, routes to writing mode, which follows a two-message method (explain first, then write the text), and the explanation step can be switched off. If none exist, starts the 7-stage voice-building workflow. Supports multiple named voices, in English or German (Hochdeutsch). Includes a deterministic draft checker (scripts/voice_check.py), an eval harness, and Claude Code hooks.
---

# Write Like Me

A single skill with two modes:

- **Build mode.** No voice profile exists yet. Runs a 7-stage workflow: analyzes your writing corpus using linguistic and psychological measurement methods, mines your style rules, and generates a personalized voice profile saved to `voices/<name>/`.
- **Write mode.** A voice profile exists. Reads it and writes or revises prose in that voice, using the two-message method in `references/09-how-to-write.md`. The universal anti-AI baseline (`references/00-universal-baseline.md`) is always active, on top of whatever the voice profile specifies.

Multiple voices are supported. Each voice is a named subfolder in `voices/`. You can have one for your own writing, one for a different register, one built from an admired author's work.

---

## When this skill applies

It applies to every text that someone other than the author will read, and to every judgment about such a text, whether or not the author names the skill. These situations are triggers.

- An answer to a form field, such as a job application question or a registration form.
- A cover letter, or a paragraph of one, including an "additional information" field.
- A profile text, headline, bio, about text or service description for any platform.
- A portfolio page, project overview, summary or case study section.
- An email, reply, message or outreach to another person.
- A listing text, the prose of a README, or the description of a public repository or marketplace entry.
- The author's questions about a text, such as "is this good?", "how does this come across?", "can this be shorter?" or "in your own words". A yes or no question is answered with yes or no first, and nothing is changed until the author says so.

Two Claude Code hooks enforce this. A `UserPromptSubmit` hook recognizes such a request and adds the method to the context. A `PostToolUse` hook runs the checker on every reader text written to a writing path. Setup is in `references/10-hooks.md`. A text written in chat and not to a file is never seen by the post-write hook, so the checker has to be run by hand before the text is shown.

---

## Session start. Mode detection

On every invoke:

1. Check the `voices/` directory. A voice is a subfolder that holds a `profile.json`. A `.gitkeep` or any other loose file does not count as a voice.
2. If **no voice exists**: say "No voice profiles found. I can build one from your writing corpus. Do you want to start?" then begin Stage 1.
3. If **one voice exists**: say "Found voice: [name]. Write using it, or build a new one?" Wait for choice.
4. If **multiple voices exist**: list them. Ask which to write in, or whether to build a new one. Wait for choice.

---

## Languages

A voice is English or German. German means standard German (Hochdeutsch). The language is set once, when the corpus is analyzed, and is stored as `"language": "de"` in `profile.json`. Everything after that follows the profile: the checker uses the German word lists and the German-only rules, and the measurements use German function words, German abbreviations, German readability formulas and the spaCy model `de_core_news_sm`. A profile without `language` is English. In German the skill can be called "Schreib wie ich".

For a German voice:

- Pass `--language de` to `scripts/stylometry.py` in Stage 3 and to `scripts/corpus_conflicts.py` in Stage 4. `voice_profile.py init` takes the language from the stylometry file.
- Read `references/00-universal-baseline-de.md` wherever this file says `references/00-universal-baseline.md`.
- Two register keys exist for German only. `en_dash` (off, review or block) controls the Gedankenstrich check. `gender_characters` (off, allowed, review or forbidden) decides whether the voice uses forms such as Kund*innen. The default is `allowed`, which checks only that one text does not mix forms. Gender forms are the writer's choice, not an AI tell.
- Without a profile, `python scripts/voice_check.py <draft> --language de` runs the German baseline.

---

## Where voices live

The voice folder is `voices/<name>/` inside the folder this skill is installed in. Any other location works when the tools are pointed at it. The checker and the eval harness take `--profile <path>/profile.json`, and the hook takes the environment variable `WRITE_LIKE_ME_PROFILE` or a `profile` entry in `voices/<name>/hook.json`. The hook reads `hook.json` from the folder of the profile it uses. Reports, goldens and the eval baseline are written into the voice folder and never into the corpus folder.

---

## Write mode

When a voice is selected:

1. Read `references/09-how-to-write.md`. It describes how the writing is done, and everything below checks the result. Choose the register first. A profile with one register uses it by default, and `--register` can be left out. With several registers, pass the one that matches the text (a letter, a post, an essay), and ask the author when the text fits none of them.
2. Read `voices/<name>/01-generative.md`. Positive patterns, quantitative targets, exemplars.
3. Read `voices/<name>/02-corrective.md`. Hard bans, scan checklist.
4. Read `references/00-universal-baseline.md`, or `references/00-universal-baseline-de.md` for a German voice. Always active, applies to every voice.
5. State in one sentence what you will write or revise. Wait for confirmation.

### The two messages

For every text that a reader will see, the work has two steps and they are never merged.

1. **Message one is the explanation.** Read the real source first. Then explain the subject to the author in chat, in plain paragraphs, as the answer to "What is this, and why does it exist?" Include the actual feature, the actual number and one example made for this text. Wait for the author to approve it.
2. **Message two is the text.** After approval, cut the explanation down to the target and change the point of view where needed. The approved wording stays. A sentence that is in the text and not in the explanation is a defect. Add nothing the request, the source or the explanation did not contain, and never add a caveat, a disclaimer or a closing note.

### Turning the explanation off

The explanation step can be turned off, and it is on by default. For one text, the author says "just write it" or "skip the explanation", and "explain first" turns it back on. For a voice, `"explainFirst": false` in `voices/<name>/hook.json` turns it off, and the environment variable `WRITE_LIKE_ME_EXPLAIN` set to `off` or `on` wins over that file. With the step off, the text is written directly from the request and the real source. The other rules stay. Nothing is added that the request or the source did not contain, and the checker runs before the text is shown, without `--explanation`.

When the author asks a question about a text, the reply is the answer and nothing else. After a rejection, state what was understood, name the rule that was broken, and start again from the source. The full method, the moves that are never allowed and the rules for working with the author are in `references/09-how-to-write.md`.

After delivering prose:

1. Save the draft to a file (or pipe it). Save the approved explanation to a second file, and the phrases the author rejected so far to a third file with one phrase per line. Run the checker:
   `python scripts/voice_check.py <draft.md> --profile voices/<name>/profile.json --register <register> --explanation <explanation.md> --rejected <rejected.txt>`
   The last two flags are optional. `--explanation` reports every number and proper noun in the draft that the explanation does not contain as `ADDITION`. `--rejected` blocks a draft that contains a rejected phrase.
2. Fix every `block` hit and run again until the last line is `VOICE_CHECK_PASS` or `VOICE_CHECK_REVIEW`.
3. Read each `review` hit. Fix it or say in one line why it stays. Lines marked `info` are reported and leave the verdict alone.
   Drift lines are different when the text was cut from an approved explanation. The approved wording stays, so a drift line is a report and not an edit order. Do not change the wording to move a number. Report each drift line to the author in one line with the observed and the target value, and let the author decide. On a text that was not cut from an approved explanation, fix drift lines like any other review hit.
4. Then scan for the judgment rules in `voices/<name>/02-corrective.md` that no command can check.

---

## Build mode. 7-stage workflow

### Stage 1. Discover

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

### Stage 2. Extract and Preview

Read `references/02-author-filtering.md`.

For conversation exports: run `scripts/extract_author_turns.py` with the confirmed author marker. Show 5 random extracted samples and confirm the filter worked. Flag:
- Extracted content < 10% of source file (filter may be wrong)
- Content contains AI-output markers ("I'll help you", "Certainly!", "Here's a")
- Total corpus size after filtering. Reliable distributions need 20,000 words. Below 5,000 words the build stops. Between 5,000 and 20,000 words the build continues and every distribution rule is provisional. Say which case applies now (see Stage 4)

For prose files: confirm file count and approximate word count. Files named `_STYLE-PROFILE-*.md` and anything under a folder named `voices/` are generated by this skill. Stage 2 and the analysis skip them when they sit inside the corpus.

### Stage 3. Analyze

First run the preflight, so that every warning appears before the analysis starts:

```
python scripts/voice_profile.py preflight --corpus-words <approximate word count>
```

It lists optional packages that are missing (`textstat`, `spaCy`) and states when the corpus is below 20,000 words (provisional) or below 5,000 words (the build stops). Install the packages if you want the extended features, or continue without them.

Run `scripts/stylometry.py` over the full filtered corpus and over each register subset separately (e.g., formal essays, casual writing, conversation).

For each register:
```
python scripts/stylometry.py <path> --register <name> --output voices/<name>/<register>.stylometry.json
```

For a German corpus, add `--language de`. Install the German spaCy model first if spaCy is used: `python -m spacy download de_core_news_sm`.

The script creates the output folder when it is missing. Add `--report` to write the Markdown report next to the JSON file. The report goes into the voice folder and never into the corpus folder. Report word counts per register and any warnings. The JSON of an English corpus carries a contraction count and a rate per 100 words. A German corpus has none, because German has few contractions.

### Stage 4. Mine Rules

Read `references/04-rule-mining.md`.

Three sources, in order:

1. **Existing rule files.** Read verbatim, extract every stated rule, correction, prohibition.
2. **Extreme statistics.** Feature usage at < 0.5% or > 5× general-English baseline → candidate rule.
3. **Negative space.** Sentence shapes never used, connective patterns absent, lengths never reached.

4. **Conflicts with the universal baseline.** Run the checker over the author's own corpus with the universal baseline:
   `python scripts/corpus_conflicts.py <corpus folder or filtered text file>` (add `--language de` for a German corpus)
   Every rule that blocks somewhere in the author's own writing (for example `NOT_ONLY_BUT_ALSO`) is reported with a count and examples. Each one is a conflict that the author decides in Stage 5. Keeping the habit means an entry in `rule_overrides` in `profile.json`, and dropping it means the rule stays. Do not decide for the author. The step ends with `VOICE_CONFLICTS_FOUND` or `VOICE_CONFLICTS_NONE`.

Compile candidate rules. The statistics table in `references/04-rule-mining.md` includes the contraction rate. A count of 0 contractions in the primary register is the candidate rule "no contractions".

An absence in a small sample is not a ban. A feature count of 0 in a corpus under 20,000 words produces a provisional rule that is marked for the author's confirmation. `voice_profile.py init` applies the same rule: below 20,000 words it writes semicolons as `review`, does not let a zero short-sentence target block, and records every such rule under `provisional` in `profile.json`. A rule leaves that list only when the author confirms it against a new text.

### Stage 5. Review (STOP, wait for user)

Present mined rules as a numbered checklist. For each: state the rule and its evidence source.

Tell the user what an answer changes before asking. A yes makes the rule a checker rule with the severity shown in the list, and a no drops the rule so that the checker never applies it.

List every conflict from the corpus scan next to the rules and ask for a decision on each.

Ask the user to:
- Mark false positives
- Add missing rules
- Decide each conflict with the universal baseline
- Confirm register labels
- Set aside 2 or 3 corpus samples for Stage 7. Each is a complete paragraph from the primary register that is not an exemplar and covers a topic no exemplar covers. Write down which files they are, and keep them out of the exemplars and out of any prompt used for generation.

Do not proceed until the user responds.

### Stage 6. Emit

Read `references/05-exemplar-selection.md` and `references/06-skill-emission.md`.

Using the approved rules and corpus statistics:

1. Select 3–5 exemplar passages from the corpus
2. Write the voice profile to `voices/<name>/` using the templates:
   - `voices/<name>/01-generative.md`
   - `voices/<name>/02-corrective.md`
   - `voices/<name>/03-corpus-source.md`
3. Write the standalone stylometric report into the voice folder, next to the profile. Never write it into the corpus folder, because a report in the corpus is counted as corpus on the next run:
   `python scripts/generate_report_from_json.py voices/<name>/<register>.stylometry.json --author "<Name>" --output voices/<name>/_STYLE-PROFILE-<date>.md`
   Without `--output` the script writes into the folder of the first JSON file.
4. Initialize the machine-readable profile and validate it:
   `python scripts/voice_profile.py init --voice <name> --register <primary-register> --from-stylometry voices/<name>/<primary-register>.stylometry.json --output voices/<name>/profile.json`
   Then edit `bans` and the per-register policies to match the approved rules from Stage 5, and run
   `python scripts/voice_profile.py validate voices/<name>/profile.json`.
   The allowed policy values are in `templates/profile.schema.json`. In one line: `semicolons`, `contractions` and `questions` take off, allowed, review or forbidden (review gives a review hit and forbidden gives a block hit), `tricolon` takes off, info, review or block, and every other per-register rule takes off, review or block. `init` starts `contractions` and `questions` as off and says so.
5. Write `voices/<name>/goldens.jsonl` from every approved BAD and GOOD example in `02-corrective.md` (BAD becomes `block` or `review`, GOOD becomes `pass`), then save the baseline:
   `python eval/voice_eval.py baseline --goldens voices/<name>/goldens.jsonl --profile voices/<name>/profile.json --output voices/<name>/eval-baseline.json`
6. Write `voices/<name>/claude-ai-skill.md` using `templates/generated-claude-ai-skill.md`. This file is self-contained: all rules, patterns, and exemplars are inlined directly with no references to external files. It is ready to upload to Claude.ai → Settings → Customize → Skills, or to paste into the Skills instruction field.

Ask if the user wants to inspect any file before verification.

### Stage 7. Verify

Read `references/07-verification.md`.

Use the 2 or 3 corpus samples that were set aside in Stage 5. Ask the user to generate one paragraph per sample topic with whatever agent they already use, and to save each paragraph to its own file. No particular command line tool is needed. Then score the files. `--strict` is the default for the author's own rules, because it fails a sample on a review hit as well as on a block hit:

```
python eval/voice_eval.py verify --strict --profile voices/<name>/profile.json voices/<name>/verify/sample-1.md voices/<name>/verify/sample-2.md
```

Require `VOICE_EVAL_OK`. Run `voice_check.py` on any failing sample to see the hits and the drift lines. Then run the goldens gate for the voice and require `VOICE_EVAL_OK` there as well:

```
python eval/voice_eval.py score --goldens voices/<name>/goldens.jsonl --profile voices/<name>/profile.json --gate voices/<name>/eval-baseline.json
```

Compare the drift lines with the held-out samples as described in `references/07-verification.md`.

Report pass or fail per sample. Flag any rule that needs sharpening.

---

## Routing table

| Task | Read |
|------|------|
| Any text a reader will see | `references/09-how-to-write.md` |
| Setting up the Claude Code hooks | `references/10-hooks.md` |
| Writing new prose | `voices/<name>/01-generative.md` + `references/00-universal-baseline.md` |
| Revising prose | `voices/<name>/02-corrective.md` + `references/00-universal-baseline.md` |
| A German voice | `references/00-universal-baseline-de.md` in place of `references/00-universal-baseline.md` |
| Finding corpus sources | `references/01-corpus-discovery.md` |
| Filtering conversation exports | `references/02-author-filtering.md` |
| Understanding measured features | `references/03-methodology.md` |
| Mining rules | `references/04-rule-mining.md` |
| Selecting exemplars | `references/05-exemplar-selection.md` |
| Emitting the voice profile | `references/06-skill-emission.md` |
| Verifying the generated profile | `references/07-verification.md` |
| Re-running on updated corpus | `references/08-regeneration-and-diff.md` |
| Finding where the author breaks the baseline | `scripts/corpus_conflicts.py` |
| Checking a draft mechanically | `scripts/voice_check.py` |
| Scoring the checker | `eval/voice_eval.py` |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/stylometry.py` | Feature extraction, stdlib base, textstat optional, spaCy optional |
| `scripts/extract_author_turns.py` | Extract author-only turns from conversation export markdown |
| `scripts/generate_report_from_json.py` | Combine JSON profiles into a human-readable report, written into the voice folder by default |
| `scripts/corpus_conflicts.py` | Run the universal baseline over the author's own corpus and list every rule that blocks, for the author to decide |
| `scripts/voice_check.py` | Deterministic draft checker. Reports hits, drift, a verdict, and an exit code |
| `scripts/voice_profile.py` | Load, validate, and initialize a voice `profile.json`. `preflight` reports missing packages and a small corpus |
| `scripts/voice_lang.py` | Language data: German word lists for the measurements and the rules |
| `scripts/voice_rules_de.py` | The German-only rules: quotation marks, dashes, number format, heading case, calques, participle tails, du and Sie, gender forms, connectives, umlauts |
| `scripts/voice_rules_reader.py` | The reader-text rules: closing caveat, benefit tail, tagline, length band, additions, repeated phrase |
| `scripts/writing-gate-hook.mjs` | Claude Code hooks for prompts and for files that were just written |
| `eval/voice_eval.py` | Score `voice_check.py` against golden passages, gate regressions, and `verify` generated samples |

---

## What this skill does not do

- Does not generate ideas, arguments, or research. It captures and applies how someone writes, not what they write about
- Does not compare against external benchmarks or evaluate quality in the abstract
- Does not handle non-English writing conventions
- Does not invent exemplars. All exemplars come from the actual corpus
