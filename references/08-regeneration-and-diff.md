# 08 — Regeneration and Diff

How to update a voice skill when the corpus grows or style changes.

---

## When to regenerate

Re-run the analysis when:
- New substantial writing is added to the primary register corpus (> 5,000 new words)
- The author notices the skill producing incorrect patterns consistently
- More than 6 months have passed since the last analysis (style drifts slowly)
- The author explicitly corrects a rule more than twice (the rule may be wrong)

---

## What to preserve

Before regenerating, snapshot the current skill:

```
<name>-voice/
  _SNAPSHOTS/
    YYYY-MM-DD/
      SKILL.md
      references/
        01-generative.md
        02-corrective.md
        03-corpus-source.md
```

Keep at least the two most recent snapshots. This allows reverting if the new profile is worse.

---

## Running the update

1. Re-run `stylometry.py` on the updated corpus with the same register labels and `--output` paths.
2. Run `generate_report_from_json.py` with the new JSON files alongside the old JSON files from the snapshot directory.
3. Compute the diff between new and old profiles on these key features:

| Feature | Significant change threshold |
|---------|------------------------------|
| Mean sentence length | ± 3 words |
| % long sentences | ± 5 percentage points |
| Em dash rate | Any change from 0 |
| Semicolon rate | Any change from 0 |
| Hedge rate | ± 0.1 per 100 words |
| Booster rate | Any change from 0 |
| First-person rate | ± 0.15 per 100 words |

---

## Presenting the diff

Show the author:
- Features that changed significantly (above threshold)
- Whether any zero-count features became non-zero (potential rule violation in new corpus)
- Whether any rules in `02-corrective.md` are no longer supported by the new corpus data

Ask: is this change an intentional style shift, or is it noise from the new source material?

---

## Updating skill files

Only update the skill files if the author confirms the style change is real:

- **Feature drifted but rules are the same:** Update the quantitative targets table in `01-generative.md`. Update the provenance file.
- **New pattern identified:** Add rule to `01-generative.md` (generative) or `02-corrective.md` (corrective) as appropriate.
- **Existing rule invalidated by new corpus data:** Remove or soften the rule. Record in provenance file which version the rule was active through.

---

## What NOT to change on re-run

Rules derived from explicit corrections ("never use em dashes — I always remove them") are not invalidated by corpus statistics. If the new corpus contains em-dashes and the author has explicitly stated they don't use them, the corpus has pre-edit material — not a style change.

Distinguish between:
- **Measured feature** — what appears in the corpus (may include editing artifacts)
- **Stated preference** — what the author explicitly said (higher authority than measurements)

Stated preferences override measurements when they conflict.
