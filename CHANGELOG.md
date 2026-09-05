# Changelog

All notable changes to Write Like Me. Versions are git tags and GitHub Releases.

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
