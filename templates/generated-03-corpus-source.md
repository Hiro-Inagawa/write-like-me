# 03 — Corpus Source and Provenance

---

## Analysis date

{{analysis_date}}

---

## Corpus sources

| Register | Source path | Filter | Words after filtering |
|----------|-------------|--------|----------------------|
{{corpus_sources_table}}

**Total analyzed:** ~{{total_words}} words across all registers.

---

## Tool versions

- `building-voice-skills/scripts/stylometry.py` — {{stylometry_version}}
- `building-voice-skills/scripts/extract_author_turns.py` — {{extraction_version}}
- Python {{python_version}}

---

## Rule derivation

Rules in `01-generative.md` and `02-corrective.md` were derived from:

1. **Existing feedback records** — {{rule_source_files}}
2. **Corpus statistics** — {{derived_rules_summary}}
3. **Qualitative observation** — {{qualitative_sources}}

---

## Primary register: key measured values

| Feature | Value |
|---------|-------|
| Mean sentence length | {{primary_mean_sentence_length}} words |
| % long sentences (≥30w) | {{primary_pct_long}}% |
| % short sentences (≤5w) | {{primary_pct_short}}% |
| Commas per sentence | {{primary_comma_per_sentence}} |
| Em dashes per 1000w | {{primary_em_dash}} |
| Semicolons per 1000w | {{primary_semicolon}} |
| Hedge tokens per 100w | {{primary_hedge}} |
| Booster tokens per 100w | {{primary_boost}} |
| 1st person singular per 100w | {{primary_first_sg}} |
| MATTR (window 100) | {{primary_mattr}} |
| Hapax ratio | {{primary_hapax}} |
| Concession rate | {{primary_concession}} |

---

## Re-run instructions

1. Run `stylometry.py` on each source with the appropriate `--register` flag and `--output <register>.json`
2. Run `generate_report_from_json.py` on all JSON files with `--output _STYLE-PROFILE-<DATE>.md`
3. Compare new profile against stored snapshot using `references/08-regeneration-and-diff.md`
4. Update quantitative targets in `01-generative.md` if primary register corpus grew substantially
5. Update this file with new date and word counts

---

## Limitations

{{limitations_list}}
