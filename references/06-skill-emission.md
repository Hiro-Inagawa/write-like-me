# 06 — Skill Emission

How to write the generated voice skill files from the approved rules, statistics, and exemplars.

---

## Output structure

The generated skill lives at `~/.claude/skills/<name>-voice/`:

```
<name>-voice/
  SKILL.md                  # Trigger conditions, routing table, hard rules
  references/
    01-generative.md        # Positive patterns + exemplars (read at write-time)
    02-corrective.md        # Hard bans + scan-for list (read after writing)
    03-corpus-source.md     # Provenance
```

Use the templates in `templates/` as skeletons. Fill in the corpus-specific data.

---

## SKILL.md

The SKILL.md contains three things:

1. **YAML frontmatter** with name and description. The description must name the specific triggers that activate the skill: "drafting prose", "revising articles", "checking style". Do not use vague descriptions.

2. **Session start protocol.** Three steps: read 01-generative.md, read 02-corrective.md, state intent in one sentence.

3. **Hard rules.** The 2–4 most important rules from the approved rule list, stated as absolute prohibitions with examples of bad and good. These are the gates that every output must pass. Choose only the rules where violation is frequent enough to warrant automated checking on every output.

4. **Routing table** and register notes if multiple registers are covered.

---

## 01-generative.md

Sections in order:

1. **Quantitative targets table.** The measured values from the primary register profile. These are not targets to hit precisely — they are the territory to write into. Include: mean sentence length, % long sentences, % short sentences, commas per sentence, em dashes per 1000w, semicolons per 1000w, first-person rate, hedging rate, booster rate.

2. **Structural patterns.** Two to four paragraphs on how sentences, paragraphs, and essays are built. Written in interpretive language, not data. "Long, connected sentences built from subordinate clauses" rather than "mean sentence length 33 words."

3. **Discourse connective profile.** Which connective types dominate (causal, adversative, additive, temporal) and which are absent.

4. **Cognitive process markers.** What kind of reasoning the writing reflects: causation-heavy, discrepancy-framing, certainty-flagging.

5. **Exemplars.** The 3–5 selected passages from Stage 6, each with annotation.

---

## 02-corrective.md

Sections in order:

1. **Hard bans** — zero-tolerance rules, with examples of bad and corrected versions. These are scanned automatically before every delivery.

2. **Soft checks** — patterns to flag and consider. Not auto-rejected; user decides in context.

3. **Mechanical scan table** — a grep list. Pattern, target count. The model runs this as a final check before delivering any draft. Only include patterns that are detectable by string matching (em dash `—`, semicolon `;`, specific words like "clearly", "obviously").

---

## 03-corpus-source.md

Record:
- Analysis date
- Source paths per register, with filter description and word count after filtering
- Tool versions used
- Rule derivation sources (which rule files, which statistics, which negative-space observations)
- Key measured values table (primary register only)
- Re-run instructions
- Limitations

---

## What the generated skill does NOT contain

- Qualitative phrases without evidence ("writes in a direct, honest style") — these have near-zero effect and clutter the file
- Quantitative numbers without interpretation ("em-dash rate: 0.000/1000w") — these should be translated to interpretive rules ("never uses em-dashes")
- Rules that were rejected in Stage 5 user review
- Content about topics, arguments, or research — only voice
