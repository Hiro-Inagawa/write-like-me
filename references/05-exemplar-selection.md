# 05 — Exemplar Selection

How to choose the 3–5 passages that go into the generated skill's `01-generative.md`.

---

## Why exemplars matter

Style-prompting research (Patel et al., 2023) shows that combining a quantitative profile with 2–5 short exemplar passages outperforms either approach alone. Qualitative descriptions ("writes in a direct, conversational style") have near-zero empirical effect on LLM output. The exemplars do the heavy lifting that descriptions cannot.

---

## Selection criteria

Choose passages that together cover:

1. **The densest concentration of the author's distinctive features.** A passage where sentence length, connective structure, and punctuation patterns are all typical of the author's style — not an outlier.

2. **Different paragraph types.** If the author makes arguments, includes concrete evidence, and draws implications, choose one passage from each category. The exemplar set should not be all the same kind of move.

3. **Clean prose only.** No headings, bullet lists, code, or citations inside the exemplar. The passage should read as continuous prose.

4. **Complete thoughts.** Each exemplar should be a complete paragraph or short sequence of paragraphs. Partial sentences at the start or end look like truncation.

5. **Hold-out discipline.** Reserve 2–3 passages for Stage 7 verification. Do not use the same passages as both exemplars and verification samples.

---

## Exemplar length

Target 60–150 words per exemplar. Short enough to fit in context without dominating it; long enough to show connective rhythm, sentence variety, and structural patterns.

---

## Exemplar annotation

After selecting each passage, write 2–3 sentences of annotation explaining what to notice about it: what specific feature is visible, what the passage demonstrates that a rule statement alone wouldn't capture.

**Example annotation format:**

> What to notice: The "but" pivot in sentence 2 carries the whole contrast. The third sentence raises and then dismisses the natural objection. No drama. The observation accumulates across all three sentences without separate punchy lines for each beat.

The annotation teaches the pattern, not just labels it.

---

## What makes a bad exemplar

- **Too short:** A single sentence shows nothing about rhythm or structure.
- **Atypical of the register:** If the author only uses short sentences in casual conversations but the target register is formal, do not pick casual-register examples.
- **All from the same section:** If all exemplars come from the same paragraph, they may reflect one local argument style rather than general habits.
- **Heavy with topic-specific vocabulary:** An exemplar about quantum physics may teach "use physics words" rather than sentence structure. Prefer passages that could be about anything.

---

## How to present exemplars in the skill

In `01-generative.md`, each exemplar should be:
1. Quoted in a blockquote
2. Followed by the annotation paragraph
3. Labeled with what structural type it demonstrates ("Parallel observation across domains", "Mechanism explanation", "Analytical implication", etc.)

The label helps Claude route to the right exemplar when writing a specific kind of passage.
