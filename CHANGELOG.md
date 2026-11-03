# Changelog

All notable changes to Write Like Me. Versions are git tags and GitHub Releases.

## 3.1.1 (2026-11-02)

- `compute_readability` in `scripts/stylometry.py` returned `{}` on every textstat release, because it called `textstat.word_count`, which textstat does not have, and one bare `except` discarded all five scores. Each score is now computed on its own, so Flesch-Kincaid grade, Gunning Fog, Flesch reading ease and syllables per word are back. Reported by Michael Wheatland in issue #1.
- `lexical_density` moved from the textstat tier to the spaCy tier under `deep_syntactic`. It is now content words (nouns, proper nouns, verbs, adjectives, adverbs) divided by all alphabetic words. The old formula would have been 1.0 for every text once the missing call was replaced. Both report renderers read the new key.
- New `tests/test_optional_tiers.py` checks that both optional tiers return numbers when their libraries are installed. The checks workflow installs textstat, spaCy and `en_core_web_sm` so these tests run there.

## 3.1.0 (2026-11-02)

- The explanation step can be turned off. It stays on by default. For one prompt, "just write it", "write it directly", "skip the explanation", "without the explanation" or "no explanation first" turns it off, and "explain first", "explain it first" or "with the explanation" turns it on. For a voice, `"explainFirst": false` in `hook.json` turns it off. `WRITE_LIKE_ME_EXPLAIN=off|on` wins over `hook.json`, and the prompt phrase wins over both.
- With the step off, the prompt hook asks for the text written directly from the request and the source, with the same no-additions rule and the checker run.
- `SKILL.md`, `references/09-how-to-write.md`, `references/10-hooks.md` and the README describe the switch. Four hook tests cover it.

## 3.0.1 (2026-10-30)

- `COMPRESSED_ANTITHESIS` now covers "instead of". In a line under 12 words, a heading or a label it flags any "instead of" tail. In longer prose it flags an "instead of X" that ends at punctuation when the negated half has four words or fewer, so "every action the board has instead of a few, so" is flagged and "the small model instead of the large one because" passes.
- Universal goldens `u-antith-002` and `u-antith-003` and a unit test cover both cases. The universal baseline is refreshed.

## 3.0.0 (2026-10-06)

Method layer

- New `references/09-how-to-write.md`. Write a reader text the way the subject would be explained to the author in chat. Explain first, then write the text by cutting the approved explanation. Includes the moves that are never allowed and the rules for working with the author.
- `SKILL.md` gains the section "When this skill applies" and the two-message method as a visible step in write mode.

New checks in `scripts/voice_check.py`

- `CLOSING_CAVEAT`, `BENEFIT_TAIL`, `TAGLINE` and `LENGTH_BAND`, each configurable per register in the profile.
- `COMPRESSED_ANTITHESIS` now covers short lines, headings and labels, and no longer flags `rather than` inside a long sentence.
- `--explanation FILE` reports every number and proper noun that the explanation does not contain as `ADDITION`.
- `--rejected FILE` blocks any phrase from the file, with case and whitespace ignored, as `REPEATED_PHRASE`.
- `TRICOLON` is configurable per register and defaults to `info`, which is reported and leaves the verdict alone.
- New goldens for every new rule in `eval/goldens/reader.goldens.jsonl`, with their own baseline.

Walkthrough fixes

- A feature count of 0 in a corpus under 20,000 words now produces a provisional rule for the author to confirm and never a ban. Below 20,000 words every distribution-based rule is emitted as provisional and listed under `provisional` in `profile.json`.
- Stage 5 now says what a yes and a no change.
- Stage 7 no longer needs the Claude command line tool. It scores paragraphs from files with `python eval/voice_eval.py verify`.
- The hedge tolerance is one profile value, `thresholds.hedge_tolerance`, that the checker and `references/07-verification.md` share.
- Templates and `references/06-skill-emission.md` use the real paths and describe `voices/<name>/`.
- `python scripts/voice_profile.py preflight` prints missing packages and a small corpus before the analysis starts.

Walkthrough fixes, second pass

- `stylometry.py --output` creates the output folder. `--report` and `generate_report_from_json.py` write into the voice folder by default and never into the corpus folder. The analysis and the author-turn extraction skip `_STYLE-PROFILE-*.md` files and any `voices/` folder inside the corpus.
- `stylometry.py` reports a contraction count and a rate per 100 words. `references/04-rule-mining.md` turns a zero count into the candidate rule "no contractions", provisional under 20,000 words.
- The `contractions`, `questions` and `semicolons` policies behave the same way. `review` gives a review hit and `forbidden` gives a block hit, and `references/00-universal-baseline.md` states it. Questions under `forbidden` used to give review and now give block. `voice_profile.py init` tells the author that `contractions` and `questions` start as off.
- New `scripts/corpus_conflicts.py` runs the universal baseline over the author's own corpus and lists every rule that blocks, for the author to decide before emission.
- `eval/voice_eval.py verify --strict` is the documented default in Stage 7 for the author's own rules. Stage 5 sets aside the held-out samples, and Stage 7 gives the exact verify and goldens gate commands.
- One corpus size statement everywhere. 20,000 words for reliable distributions, 5,000 words as the floor below which the build stops, and provisional rules between them.
- SKILL.md states where voices live, how the register is chosen, and that drift lines on a text cut from an approved explanation are reported to the author and not fixed silently. A `.gitkeep` no longer counts as a voice.
- The hook passes `--explanation` and `--rejected` when `hook.json` names `explanationFile` and `rejectedFile` or when `WRITE_LIKE_ME_EXPLANATION` and `WRITE_LIKE_ME_REJECTED` are set. A REVIEW with drift lines prints the drift lines. `WRITE_LIKE_ME_PROFILE` or a `profile` entry in `hook.json` moves the voice folder anywhere.
- `references/10-hooks.md` no longer hardcodes the install path.
- The Claude.ai export template lists tricolon as `info`. The dangling plan references are gone. Console notes are ASCII. "results may vary" and "your mileage may vary" are closing-caveat phrases.

Hooks

- `scripts/writing-gate-hook.mjs` adds a `prompt` mode and a `post-write` mode for Claude Code. The voice comes from `--voice` or `WRITE_LIKE_ME_VOICE`, and the path rules from `voices/<name>/hook.json`. Setup is in `references/10-hooks.md`.

## 2.0.10 (2026-09-04)

- New rule `EXCLAMATION` flags an exclamation mark that ends a prose sentence. Off by default, turned on per register with `exclamations` set to review or block.

## 2.0.9 (2026-09-04)

- A line that ends in a colon closes its own segment, so a lead-in colon before a list is not read as an announcement colon.

## 2.0.8 (2026-09-04)

- Label detection no longer treats a line whose head starts with a determiner as a label, so `The result: variation increases.` is caught again.

## 2.0.7 (2026-09-04)

- Label lines such as `**Date:** March 20, 2026` and fully bold lines are segmented as labels, never as prose.
- `clearly` before a visibility participle such as marked, visible, or labeled is a manner adverb and no longer an empty intensifier.
- New register key `empty_intensifiers` (off, review, block) sets the severity of the empty intensifier rule per register.

## 2.0.6 (2026-09-04)

- The announcement colon rule blocks only when the text before the colon is five words or fewer. A colon after a full clause that introduces an elaboration scores as review.
- New profile key `rule_overrides` maps a rule id to off, review, or block for one voice.

## 2.0.5 (2026-09-04)

- Sections headed Related, Related articles, Related reading, and similar are skipped like citation sections.

## 2.0.4 (2026-09-04)

- Citation sections (Sources, References, Bibliography, Further reading, See also, Footnotes) are skipped by default. Pass `--check-citations` to include them.
- Banned words inside double-quoted spans no longer hit, since quoted words belong to the quoted author.

## 2.0.3 (2026-09-04)

- Every reference and template file passes the repository's own checker. Gate G4 covers all Markdown in the repository.

## 2.0.2 (2026-09-04)

- Label lines such as `Last verified: 2026-09-04` are no longer flagged as buildup before data.

## 2.0.1 (2026-09-04)

- Asyndetic tricolon (three parallel items without a conjunction) is detected as review.

## 2.0.0 (2026-09-04)

The voice engine. Version 1 built a profile and asked the model to follow it. Version 2 adds code that checks the output.

- `scripts/voice_check.py`, a deterministic draft checker with PASS, REVIEW, and BLOCK verdicts, exit code 1 on BLOCK, JSON output, stdin support, and drift metrics against profile targets.
- `scripts/voice_profile.py`, a loader, validator, and initializer for the new `profile.json` per voice.
- `scripts/voice_rules.py` and `scripts/voice_segment.py`, the rule library and the Markdown segmenter that skips code, tables, and frontmatter.
- `eval/voice_eval.py`, a scorer with block recall, review recall, false alarm rate, and a regression gate against a saved baseline. Ships with universal goldens and their baseline.
- `tests/`, 48 unit tests at release plus a negative control.
- Build mode Stage 6 emits `profile.json`, `goldens.jsonl`, and `eval-baseline.json`. Write mode runs the checker after every draft. Stage 7 verification is automated for the mechanical half.
- `.gitignore` no longer ignores every JSON file.

## 1.0.0 (2026-04-25)

- Initial release. Corpus analysis, rule mining, exemplar selection, voice profile emission, Claude.ai export, and a manual verification protocol.
