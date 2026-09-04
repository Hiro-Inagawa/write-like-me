# Voice eval

`voice_eval.py` scores `voice_check.py` against golden passages and gates regressions before a rule or profile change ships.

## Golden format

Goldens live in `.jsonl` files under `eval/goldens/`. One JSON object per line. A line starting with `#` is a comment and is skipped, as are blank lines.

```json
{"id": "u-em-001", "text": "The weights are fixed — but the execution is not.", "expect": "block", "rules": ["EM_DASH"], "note": "baseline em dash"}
{"id": "u-colon-101", "text": "Two respects: the cost and the time.", "expect": "pass", "note": "colon after a number introduces a list"}
```

Fields:

- `id`: unique within the file. A duplicate id fails to load.
- `text`: the passage to check.
- `expect`: `pass`, `review`, or `block`.
- `rules`: optional. When present, every listed rule id must appear among the hits for the golden to pass.
- `register` and `profile`: optional per-golden overrides. Defaults come from the CLI flags.
- `note`: optional, for the next reader.

## Metrics

`score` reports four numbers plus a per-rule breakdown.

- `block_recall`: share of `block` goldens that returned `BLOCK` with every expected rule present.
- `review_recall`: share of `review` goldens that returned `REVIEW` or `BLOCK` with every expected rule present.
- `false_alarm_rate`: share of `pass` goldens that returned `BLOCK`. This is the number that erodes trust in the checker.
- `review_noise`: share of `pass` goldens that returned `REVIEW`.

The per-rule table lists `expected`, `hit`, `missed`, and `spurious` counts for every rule id that appears in a golden's `rules` list or fires on a `pass` golden.

## Subcommands

```bash
python eval/voice_eval.py score --goldens eval/goldens/universal.goldens.jsonl [--profile FILE] [--register NAME] [--gate BASELINE] [--tolerance 0.0] [--json OUT]
python eval/voice_eval.py baseline --goldens eval/goldens/universal.goldens.jsonl [--profile FILE] [--register NAME] --output eval/baselines/universal.json
python eval/voice_eval.py selftest
```

- `score` runs every golden and prints the metrics table. With `--gate`, it also compares the run against a saved baseline file and fails if `block_recall` or `review_recall` drops below the baseline minus `--tolerance`, or `false_alarm_rate` rises above the baseline plus `--tolerance`. Default tolerance is 0.
- `baseline` runs the same scoring pass and writes the metrics to a JSON file for later gating. Read the written file and confirm the numbers before committing it.
- `selftest` scores the two fixtures in `tests/fixtures/` against the built-in universal profile with no external file.

Exit code is 0 when every golden passes and the gate (if any) holds, 1 when a golden fails or the gate fails, 2 on bad input. The last line of stdout is always `VOICE_EVAL_OK` or `VOICE_EVAL_FAILED`.

## When a golden fails

Read the passage. Decide whether the rule is wrong or the golden is wrong, then fix that one thing.

- If the rule catalogue in the plan says the passage should trip the rule and it did not, or should not and it did, fix the rule in `scripts/voice_rules.py`.
- If the golden's `expect` or `rules` do not match what the rule catalogue actually calls for, fix the golden.

Never edit a golden's expected outcome just to make a failing run pass. That erases the signal the golden exists to give. A golden documents a judgment call about the voice. Changing the judgment without re-reading the passage against the catalogue is not a fix, it is a way to stop looking.
