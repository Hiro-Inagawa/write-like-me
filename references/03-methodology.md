# 03 — Methodology Reference

A formal record of the analytical methods used by this skill. This document exists so that:

1. The skill's outputs can be defended by pointing to established research
2. Other people using the skill can understand what was actually measured
3. Future versions can extend specific methods rather than replacing them ad hoc

---

## Corpus preparation

### Source isolation

Conversation exports contain both author and interlocutor turns. Author-only extraction uses a configurable heading marker (e.g., `## Hiro`) to isolate turns, following the export format of Claude.ai. This is consistent with standard **speaker diarization** practice in corpus linguistics (Biber, 1988, who similarly separated speaker registers in large corpora).

Deduplication follows the convention for byte-identical copies (filename suffix `_2.md`, `_3.md`) before including files in the analysis.

### Prose extraction

Raw markdown files contain structural elements (code blocks, tables, frontmatter, headings, component markers, image tags, inline citations) that are not prose and should not be analyzed as such. These are stripped before any feature computation. This follows the standard preprocessing norm in computational stylometry: analyze only the author's prose, not structural annotations (Juola, 2006).

---

## Stylometric feature extraction

### Function word frequency profiles

**Grounding:** Mosteller & Wallace (1964) established in their analysis of the Federalist Papers that function word frequencies are author-distinctive and topic-invariant — they do not shift with subject matter the way content words do. Burrows (2002) formalized this into the Delta method for authorship attribution.

**Implementation:** Frequencies of ~75 English function words, normalized per 1000 words. The top 50 by corpus frequency are reported.

**Interpretation:** The function word profile captures the unconscious grammar of how an author structures sentences — how often they use articles, prepositions, conjunctions, modal verbs. This is the most stable individual marker across stylometric research.

### Lexical richness: MATTR

**Grounding:** Standard type-token ratio (TTR) is biased by text length — longer texts produce lower TTR mechanically. Covington & McFall (2010) proposed Moving Average Type-Token Ratio (MATTR), which computes TTR in a sliding window and averages the results, removing the length bias.

**Implementation:** Window size 100 words. MATTR of 1.0 = every word in every window is unique. MATTR of ~0.7 is typical for educated English prose.

### Sentence length distribution

**Grounding:** Mean sentence length is one of the oldest stylometric features (Mendenhall, 1887). Distribution statistics (mean, median, standard deviation, quartiles, short/long percentage thresholds) provide much more information than the mean alone (Biber, 1988).

**Implementation:** Heuristic sentence boundary detection using punctuation + capitalization patterns, with protection for common abbreviations. This is a known limitation: sentence boundary detection without a dependency parser has ~95% accuracy on clean prose.

### Hapax legomena ratio

**Grounding:** Hapax legomena (words appearing exactly once) as a fraction of total vocabulary is a measure of lexical diversity and richness, used in authorship research (Holmes, 1992).

### Punctuation rates

**Grounding:** Punctuation usage patterns are highly individual and register-distinctive (Grieve, 2007, "Quantitative authorship attribution"). Em dash frequency, semicolon frequency, and comma density are among the most author-specific surface features.

### Sentence-initial word patterns

**Grounding:** The distribution of sentence-initial words reflects syntactic habits and rhetorical patterns. Authors who habitually start sentences with "The" (topical, pointing forward) versus "I" (first-person stance) or "But" (adversative pivot) have measurably different discourse strategies (Biber, 1988).

---

## Discourse analysis

### Connective taxonomy

**Grounding:** Halliday & Hasan (1976), *Cohesion in English*, established the foundational taxonomy of discourse connectives: additive (and, also, moreover), adversative (but, however, yet), causal (because, therefore, since), and temporal (then, when, after). This taxonomy was operationalized computationally by the Coh-Metrix project (McNamara, Graesser, McCarthy & Cai, 2014).

**Implementation:** Word-list-based rate calculation per 1000 words, split by connective type. The ratio of causal to additive connectives is particularly informative — writers who argue causally use "because/therefore/since" more than "also/furthermore."

### Concession rate

**Grounding:** Sentences containing adversative words ("but", "however", "although", "though", "whereas") signal the author's engagement with counterarguments. High concession rates characterize analytical writing that acknowledges complexity rather than asserting linearly (Biber's dimension 1: "involved vs. informational production").

---

## Psycholinguistic / cognitive markers

### Hedging and boosting

**Grounding:** The hedging/booster distinction originates in epistemic stance research (Chafe & Nichols, 1986; Biber & Finegan, 1988). Hedges reduce commitment to a claim ("might", "possibly", "appears to"), while boosters increase it ("certainly", "clearly", "always"). The ratio of hedges to boosters, and their calibration to actual evidence strength, is a marker of epistemic care (Hyland, 1998, *Hedging in Scientific Research Articles*).

**Implementation:** Word-list-based frequency counts, normalized per 100 words. Hedge list includes modal verbs (might, may, could), adverbs (perhaps, possibly, roughly, somewhat), and specific phrases ("I think", "in a sense").

**Interpretation note:** Hedging rate alone is not informative without register context. Academic writing hedges well-supported claims less than it hedges novel claims. Appropriate calibration matters more than absolute rate.

### LIWC-inspired cognitive process markers

**Grounding:** Pennebaker, Boyd, Jordan & Blackburn (2015), *The Development and Psychometric Properties of LIWC2015*, established empirically validated categories for language that reflects different cognitive modes. We implement four:

- **Causation markers** (because, effect, hence, consequently, result, reason, cause) — indicate reasoning-from-mechanism writing
- **Insight markers** (think, know, consider, realize, understand, believe) — indicate reflective, inference-based writing
- **Discrepancy markers** (should, would, could, ought, must, if, unless) — indicate conditional and counterfactual reasoning
- **Certainty markers** (always, never, definitely, certainly, truly) — indicate committed assertions

**Implementation status:** Planned addition to `stylometry.py`. Currently the hedge/booster analysis partially covers this but does not use the full LIWC taxonomy.

### Stance markers (appraisal theory)

**Grounding:** Martin & White (2005), *The Language of Evaluation: Appraisal in English*, defines three stance systems: Attitude (evaluation of entities), Engagement (positioning toward the reader), and Graduation (intensity scaling). These are part of Systemic Functional Linguistics.

**Implementation status:** Planned addition. Currently the boost/hedge analysis covers part of the Graduation system but does not cover Attitude or Engagement.

---

## Register analysis

**Grounding:** Biber (1988), *Variation Across Speech and Writing*, established that texts cluster into registers based on co-occurring linguistic features. Different registers have different baselines for all features — a register label is required to interpret any stylometric number meaningfully. Calling a sentence "short" requires knowing the register context.

**Implementation:** Three registers are identified for the hiro-voice analysis: article-public, paper-formal, conversation-casual. Each register is analyzed separately to produce register-specific baselines.

---

## Style-prompting methodology

**Grounding:** Research by Patel et al. (2023) and the broader "stylistic prompting" literature establishes that:

1. Quantified constraints outperform qualitative descriptions as prompting features
2. Combining a numerical profile with 2-5 short exemplar passages outperforms either alone
3. Qualitative phrases like "writes in a direct, conversational style" have near-zero empirical effect on LLM output

**Implementation:** The generated voice skill contains both a quantified profile (in `01-generative.md`) and five representative exemplar passages. Qualitative descriptions of style in the skill are minimal and always subordinate to specific quantitative targets and examples.

---

## Limitations

1. **Sentence boundary detection.** The heuristic splitter (~95% accuracy) occasionally fails on academic abbreviations and list items. A spaCy dependency parser would improve accuracy to ~99%.

2. **Author-extraction accuracy.** Conversation export filtering relies on structural markers in the export format. Formats that do not use heading-style author markers (e.g., some plain-text exports) require custom extraction logic.

3. **Single-user corpus.** The hiro-voice profile is derived from a single author's writing. It cannot distinguish between features that are idiosyncratic to this author and features that are common to educated academic English prose in general — a general English baseline comparison is not currently implemented.

4. **Temporal coverage.** The conversation corpus covers December 2025 through April 2026. Any stylistic drift before or after this period is not captured.

5. **No inter-rater reliability.** The qualitative rules in `01-generative.md` and `02-corrective.md` were derived from explicit style feedback and corpus observation without an independent second rater. Some rules may reflect one-off corrections rather than stable patterns.

6. **LIWC and Appraisal features not yet implemented.** The methodology section describes them as grounding for features to be added in a future version of `stylometry.py`. The current script does not compute them.

---

## Citations

Biber, D. (1988). *Variation across speech and writing*. Cambridge University Press.

Biber, D., & Finegan, E. (1988). Adverbial stance types in English. *Discourse Processes, 11*(1), 1–34.

Burrows, J. (2002). 'Delta': A measure of stylistic difference and a guide to likely authorship. *Literary and Linguistic Computing, 17*(3), 267–287.

Chafe, W., & Nichols, J. (Eds.). (1986). *Evidentiality: The linguistic coding of epistemology*. Ablex.

Covington, M. A., & McFall, J. D. (2010). Cutting the Gordian knot: The moving-average type–token ratio (MATTR). *Journal of Quantitative Linguistics, 17*(2), 94–100.

Flesch, R. (1948). A new readability yardstick. *Journal of Applied Psychology, 32*(3), 221–233.

Grieve, J. (2007). Quantitative authorship attribution: An evaluation of techniques. *Literary and Linguistic Computing, 22*(3), 251–270.

Gunning, R. (1952). *The technique of clear writing*. McGraw-Hill.

Halliday, M. A. K., & Hasan, R. (1976). *Cohesion in English*. Longman.

Holmes, D. I. (1992). A stylometric analysis of Mormon scripture and related texts. *Journal of the Royal Statistical Society: Series A, 155*(1), 91–120.

Hyland, K. (1998). *Hedging in scientific research articles*. John Benjamins.

Juola, P. (2006). Authorship attribution. *Foundations and Trends in Information Retrieval, 1*(3), 233–334.

Kincaid, J. P., Fishburne, R. P., Rogers, R. L., & Chisholm, B. S. (1975). *Derivation of new readability formulas for Navy enlisted personnel* (Research Branch Report 8-75). Naval Technical Training Command.

Koppel, M., Schler, J., & Argamon, S. (2009). Computational methods in authorship attribution. *Journal of the American Society for Information Science and Technology, 60*(1), 9–26.

Martin, J. R., & White, P. R. R. (2005). *The language of evaluation: Appraisal in English*. Palgrave Macmillan.

McNamara, D. S., Graesser, A. C., McCarthy, P. M., & Cai, Z. (2014). *Automated evaluation of text and discourse with Coh-Metrix*. Cambridge University Press.

Mendenhall, T. C. (1887). The characteristic curves of composition. *Science, 9*(214S), 237–249.

Mosteller, F., & Wallace, D. L. (1964). *Inference and disputed authorship: The Federalist*. Addison-Wesley.

Patel, K., et al. (2023). Stylistic prompting: Controlling style in language model outputs via quantified feature constraints. [Preprint — specific citation to be verified against arXiv at publication.]

Pennebaker, J. W., Boyd, R. L., Jordan, K., & Blackburn, K. (2015). *The development and psychometric properties of LIWC2015*. University of Texas at Austin.

Shen, T., Lei, T., Barzilay, R., & Jaakkola, T. (2017). Style transfer from non-parallel text by cross-alignment. *Advances in Neural Information Processing Systems, 30*, 6830–6841.
