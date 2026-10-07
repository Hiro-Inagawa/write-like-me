# 07. Verification

How to confirm that the generated voice produces text that matches the corpus.

---

## The problem with "does this sound right?"

Qualitative impressions of style are unreliable. The author may feel the generated text sounds like their writing when it does not match the measured profile, or the other way around. Verification requires checks that can fail.

---

## Held-out samples

During Stage 5 (rule review), set aside 2 or 3 paragraphs from the primary register corpus that were not selected as exemplars. These are the held-out samples. Write down which files they are and keep them out of the exemplars and out of every generation prompt.

Each held-out sample should:
- Be representative of the primary register, not an unusual section
- Be a complete paragraph, not a sentence fragment
- Cover a topic different from any of the selected exemplars

---

## Generation test

Verification does not depend on any particular agent or command line tool. The person building the voice generates the paragraphs with whatever agent they already use and saves them to files. The skill reads the files and scores them.

1. For each held-out sample, write a topic prompt that is similar to the sample but not the same sentence.
2. In a fresh session of the agent that the person uses, with the voice files loaded, ask for one paragraph per prompt. Do not show the agent the held-out sample.
3. Save each generated paragraph to its own file, for example `voices/<name>/verify/sample-1.md`.
4. Score the files:

```
python eval/voice_eval.py verify --strict --profile voices/<name>/profile.json voices/<name>/verify/sample-1.md voices/<name>/verify/sample-2.md
```

The command prints the verdict, the hits and the drift lines for each file. `--strict` is the default for the author's own rules, because a rule the author set to `review` or `forbidden` on purpose should fail the sample. It ends with `VOICE_EVAL_OK` when no sample fails. Without `--strict` only a block hit fails a sample. After the samples, run the goldens gate for the voice:

```
python eval/voice_eval.py score --goldens voices/<name>/goldens.jsonl --profile voices/<name>/profile.json --gate voices/<name>/eval-baseline.json
```

Example of a topic prompt: if the held-out sample is about stochastic individuality in AI, the test prompt might be "Write a paragraph about how small initial differences compound over time in complex systems."

---

## Falsifiable checks

The mechanical half of this comparison is executed by `scripts/voice_check.py` and scored by `eval/voice_eval.py verify`. It covers banned characters, banned tokens, staccato runs, and the drift metrics. The held-out comparison stays as described above.

Compare each generated paragraph with the held-out sample on these metrics.

| Check | Pass condition | Verified by |
|-------|----------------|-------------|
| Em dashes | Generated count matches corpus rule (0 if rule says zero) | Automated, `EM_DASH` in `voice_check.py` |
| Semicolons | Generated count matches corpus rule (0 if rule says zero) | Automated, `SEMICOLON_PROSE` in `voice_check.py` |
| Announcement colons | Generated count matches corpus rule | Automated, `ANNOUNCEMENT_COLON` in `voice_check.py` |
| Mean sentence length | Inside the profile target range, which `init` sets to the corpus mean plus or minus 15 percent | Automated, `mean_sentence_words` drift line |
| Short sentences | No consecutive short sentences if corpus shows none | Automated, `STACCATO_RUN` plus the short-sentence drift line |
| Boosters | Zero if corpus shows zero boosters in primary register | Automated, booster drift line |
| Hedge density | Within `thresholds.hedge_tolerance` of `targets.hedge_per_100w_mean` in `profile.json` (default tolerance 0.5 per 100 words) | Automated, `hedge_per_100w_mean` drift line |
| Concession rate | Generated paragraph has at least one "but/however/though" construction if corpus concession rate > 0.15 | Manual, no detector in the rule catalogue covers concession framing |

The hedge tolerance is one value in the profile. The checker reads it, and this table points to it, so the two cannot disagree. The default is 0.5 per 100 words because one hedge in a 200-word paragraph moves the rate by 0.5, and a tolerance below that fails every paragraph that has a single hedge more or less than the corpus average.

Drift lines marked `(provisional)` come from a corpus under 20,000 words. Treat them as questions for the author and not as failures.

---

## Reporting

Report each check as pass or fail. For failed checks, state:
- What the corpus says (the target)
- What the generated text produced
- Which specific rule needs to be sharpened in `02-corrective.md` to catch this

---

## Iteration

If more than one check fails, revise the relevant file and run one more generation test. Do not iterate more than twice. If the voice fails repeatedly on the same check, the rule may need to be rephrased as a harder constraint rather than a soft guide.

---

## What verification does not test

- Whether the generated text is good writing. That is the author's judgment.
- Whether the voice is indistinguishable from the author. Stylometric methods have detection limits.
- Whether the voice handles unusual registers or edge cases. It is calibrated to the primary register only.
