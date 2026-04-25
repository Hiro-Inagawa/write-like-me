---
name: {{voice_name}}-voice
description: Write and revise prose in {{author_name}}'s established voice. Activate when drafting articles, essays, papers, or other polished prose, or when asked to revise existing text to match this voice.
---

# {{voice_name}}-voice

Voice profile for {{author_name}}, built from corpus analysis of {{total_word_count}} words across {{register_count}} registers on {{analysis_date}}.

---

## How to use this skill

When asked to write or revise prose:

1. Read the quantitative targets and structural patterns below for the appropriate register.
2. Before delivering any draft, scan against the hard bans.
3. Fix every hard-ban violation before sending.

---

## Quantitative targets ({{primary_register}} register)

These numbers describe {{author_name}}'s polished prose. They are not constraints to hit precisely; they are the territory to write into.

| Feature | Target |
|---------|--------|
| Mean sentence length | {{mean_sentence_length}} words |
| Short sentences (≤5 words) | {{pct_short}}% |
| Long sentences (≥30 words) | {{pct_long}}% |
| Commas per sentence | {{comma_per_sentence}} |
| Em dashes per 1000 words | {{em_dash_per_1000w}} |
| Semicolons per 1000 words | {{semicolon_per_1000w}} |
| First-person singular per 100 words | {{first_sg_per_100w}} |
| Hedging tokens per 100 words | {{hedge_per_100w}} |
| Boosting tokens per 100 words | {{boost_per_100w}} |

---

## Structural patterns

### Sentences

{{sentence_patterns}}

### Paragraphs

{{paragraph_patterns}}

### Essay movement

{{essay_movement_patterns}}

### Perspective and stance

{{stance_patterns}}

---

## Discourse connective profile

{{connective_profile}}

---

## Hard bans (zero-tolerance — fix every instance before delivering)

{{hard_bans_inline}}

---

## Soft checks (flag and consider — fix when the pattern dominates)

{{soft_checks_inline}}

---

## Universal anti-AI baseline (always active, regardless of voice)

These patterns appear in AI-generated text at rates far above any individual human writer. Remove every instance.

**Zero tolerance:**
- Em dashes `—` as clause separators (use a period, comma, or parenthetical instead)
- Stance adverbials opening sentences: "Importantly,", "Notably,", "Interestingly,", "Crucially,", "Significantly,"
- Filler openers: "It is worth noting that", "It is important to note that", "It goes without saying that", "Needless to say"
- Unsupported evaluative adjectives before nouns without showing the evidence: "innovative", "robust", "significant", "powerful", "fascinating", "groundbreaking"
- Performative verb choices: "delve", "leverage", "foster", "harness", "underscore", "embark"
- Tricolon as rhetorical device: three-item lists used for rhythm rather than enumeration ("X, Y, and Z" as drama)

---

## Exemplars

Use these to calibrate feel before writing. Do not copy structure.

---

{{exemplar_1_label}}

> {{exemplar_1_text}}

{{exemplar_1_annotation}}

---

{{exemplar_2_label}}

> {{exemplar_2_text}}

{{exemplar_2_annotation}}

---

{{exemplar_3_label}}

> {{exemplar_3_text}}

{{exemplar_3_annotation}}

---

<!-- Add additional exemplars (4, 5) if selected during Stage 6 -->

---

## Register coverage

{{register_notes}}
