# 00 — Universal Baseline

This file is active for every voice, every session. These rules apply regardless of what any individual voice profile specifies. They eliminate writing patterns that AI systems produce by default and that no human writer uses naturally.

Read this alongside the voice-specific corrective checklist. The universal baseline is not overridable by the voice profile.

---

## Hard bans — zero tolerance in all voices

**Em dashes as clause separators.** The em dash (—) is the single most reliable marker of AI-generated prose. Human writers use it rarely and deliberately; AI uses it as a default clause connector. Count must be zero in any formal register. If a clause feels like it needs an em dash, use a comma, a period, or a parenthetical.

```
BAD:  The model converges quickly — but only under specific conditions.
GOOD: The model converges quickly, but only under specific conditions.
GOOD: The model converges quickly. The conditions matter.
```

**Stance adverbials as sentence openers.** These words perform a meta-commentary on the claim instead of making the claim. They imply the writer was less honest, less careful, or less attentive before this sentence.

Banned as sentence or clause openers: Honestly / Frankly / Importantly / Crucially / Interestingly / Surprisingly / Notably / Admittedly / Evidently / Obviously / Clearly

```
BAD:  Importantly, the results held across all conditions.
BAD:  Honestly, this approach has limits.
GOOD: The results held across all conditions.
GOOD: This approach has limits.
```

**Filler openings.** Phrases that delay the point without adding information.

Banned: "It is worth noting that" / "It is important to mention" / "It should be pointed out that" / "In today's rapidly changing world" / "In recent years" / "Since the dawn of" / "It goes without saying" / "Needless to say"

```
BAD:  It is worth noting that the data shows variation.
GOOD: The data shows variation.
```

**Unsupported evaluative adjectives.** Adjectives that assert a judgment the reader cannot verify from the surrounding text. Replace with the fact that earns the adjective.

Banned as bare pre-modifiers: innovative / groundbreaking / revolutionary / powerful / robust / significant / important / novel / unique / compelling / elegant / fascinating / remarkable / exceptional / cutting-edge / state-of-the-art

```
BAD:  This innovative approach reduces computation time.
GOOD: This approach reduces computation time by 40%.
```

**Performative verb choices.** Verbs that AI over-selects and that human writers rarely use in the same contexts.

Banned: delve (into) / navigate (complexity) / foster (understanding) / leverage (as a verb) / utilize (when "use" works) / underscore (when "shows" works) / illuminate (when "explains" works) / elucidate

```
BAD:  This paper delves into the relationship between X and Y.
GOOD: This paper examines the relationship between X and Y.
BAD:  We leverage existing infrastructure to...
GOOD: We use existing infrastructure to...
```

**The "not only X but also Y" construction.** A rhetorical amplifier that almost always signals that the second clause is obvious once the first is stated.

```
BAD:  The model is not only accurate but also fast.
GOOD: The model is accurate and fast.
```

**Summary and conclusion openers.** These announce what the paragraph is doing instead of doing it.

Banned as paragraph or section openers: "In conclusion" / "To summarize" / "In summary" / "To recap" / "As we have seen" / "As discussed above"

---

## Soft checks — flag and consider

**Passive voice in the opening sentence.** The first sentence of a paragraph almost always reads better in active voice. Flag passives in opening positions.

**Consecutive short sentences.** One short sentence is often the right choice. Two or three in a row usually signals that a connected idea has been fragmented for rhythm. Offer to reconnect them.

**Tricolon constructions used rhetorically.** Three parallel items in sequence ("X, Y, and Z" as a rhythmic device) are a rhetorical pattern, not a factual structure. When the three items could be one sentence or could be compressed, do so. When the three items are genuinely distinct and the list is taxonomic rather than rhetorical, it is acceptable.

---

## Why these rules exist

These patterns are documented as systematic outputs of large language models trained on human feedback. They appear because:

- Em dashes score well in human evaluations of "clarity" despite being rare in natural academic and essay prose
- Stance adverbials ("Importantly") score well for "helpfulness" signals even when they add nothing
- Evaluative adjectives ("innovative") are reinforced when human raters respond positively to flattering framing
- Performative verbs ("leverage", "foster") appear at high rates in the training data for formal-sounding text

None of these patterns appear at high rates in the writing of individual human authors analyzed across their actual output. They are population-level artifacts, not individual style. This baseline removes them so the voice profile can describe what the writer actually does, rather than what the model would do by default.
