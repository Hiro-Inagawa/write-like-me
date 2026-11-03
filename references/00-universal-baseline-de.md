# 00. Universal Baseline, German

This file is active for every German voice (`"language": "de"` in `profile.json`), in addition to the voice's own rules. It covers standard German (Hochdeutsch). It has two parts. The first part is the English baseline in German words, because AI models carry the same habits into German. The second part covers patterns that only exist in German, because a model trained mostly on English writes English typography, English sentence shapes and literal translations into German text.

The research behind every rule, with sources, is in `__RESEARCH/2026-11-02-GERMAN-AI-WRITING-PATTERNS.md` of the project (not shipped with the skill). The main sources are the German Wikipedia guide "Wikipedia:Anzeichen für KI-generierte Inhalte" and the study by Irrgang et al., KONVENS 2024.

No single pattern proves that a text is AI-written. The checker counts patterns, and the author decides every review hit.

---

## Part 1. The English baseline in German words

**Em dash.** `—` is not German typography at all. Zero in every register.

```
SCHLECHT: Die Gewichte stehen fest — die Ausführung nicht.
GUT:      Die Gewichte stehen fest, die Ausführung nicht.
```

**Stance openers.** Banned as sentence openers: `Bemerkenswerterweise` / `Interessanterweise` / `Erstaunlicherweise` / `Überraschenderweise` / `Bezeichnenderweise` / `Offensichtlich` / `Offenkundig` / `Selbstverständlich` / `Natürlich` / `Freilich` / `Bekanntlich` / `Zweifellos` / `Zweifelsohne` / `Zugegebenermaßen` / `Ehrlicherweise`.

**Filler openers and chatbot residue.** `Es ist wichtig zu beachten, dass` / `Es ist erwähnenswert` / `Erwähnenswert ist` / `Es sei darauf hingewiesen` / `Es ist kein Geheimnis, dass` / `In der heutigen schnelllebigen Welt` / `In der heutigen Zeit` / `In einer Welt, in der` / `Vergessen sind die Zeiten` / `Ehrlich gesagt` / `Stand meines letzten Wissensupdates` / `Basierend auf verfügbaren Informationen` / `Tauchen wir ein`.

**Performative verbs.** `revolutionieren` → verändern, `transformieren` → verändern, `entfesseln` → nutzen, `eintauchen` → sich ansehen, `katapultieren` → bringen, `unterstreichen` → zeigen, `ausschöpfen` → nutzen.

**Nicht nur … sondern auch.** State both things plainly.

**Summary openers.** A paragraph that opens with `Zusammenfassend`, `Abschließend lässt sich`, `Im Großen und Ganzen` or `Alles in allem`.

**Evaluative adjectives.** Block: `innovativ`, `bahnbrechend`, `revolutionär`, `hochmodern`, `wegweisend`, `zukunftsweisend`, `erstklassig`, `branchenführend`. Review: `leistungsstark`, `robust`, `umfassend`, `nahtlos`, `ganzheitlich`, `maßgeschneidert`, `signifikant`, `erheblich`, `einzigartig`, `bemerkenswert`, `beeindruckend`, `faszinierend`, `essenziell`, `facettenreich`. Each entry is a stem and also matches the inflected forms (`innovative`, `innovativen`).

**Empty intensifiers.** `zweifellos`, `zweifelsohne`, `ohne Zweifel`, `fraglos`, `unbestreitbar`, `ungemein`, `überaus`.

**Compressed antithesis.** `Ein Werkzeug, nicht ein Spielzeug.` In long prose only the closing `, nicht X.` tail is checked, because `statt` is ordinary in a long German sentence. In a heading or a short line `statt` and `anstatt` are checked too (`Planung statt Chaos`).

**Closing caveat, benefit tail, tagline.** `Beachten Sie, dass …` as the last sentence, `…, damit Sie mehr Zeit haben.` at the end of a sentence, and lines such as `Qualität, Vertrauen und Erfolg.`

**What the German version does not check.** Contractions (German has few, and the English list does not apply). Proper nouns in the `--explanation` comparison, because German capitalizes every noun, so the German check compares numbers only.

---

## Part 2. Patterns that only exist in German

**Quotation marks (block).** German uses `„ … “` (low 99, high 66). Straight `" "`, the English pair `“ ”`, or a German opening mark with an English closing mark `„ … ”` are blocked. `» … «` is accepted.

**Gedankenstrich (review).** A spaced en dash ` – ` or a spaced hyphen ` - ` used as a dash. Correct German, but AI uses it far more often than people do. A range dash (`2020–2026`) and a compound hyphen (`Software-Aktualisierung`) are never flagged. Register key `en_dash`: off, review or block.

**Number format (review).**

```
SCHLECHT: 50%   10€   z.B.   d.h.   3.5 Prozent   November 2, 2026
GUT:      50 %  10 €  z. B.  d. h.  3,5 Prozent   2. November 2026
```

German dates (`02.11.2026`), times (`14.30 Uhr`) and thousands (`1.000`) are not flagged.

**Heading case (review).** English title case, such as `Die Wichtigsten Tipps Für Den Alltag`. In German only nouns and the first word are capitalized. The checker flags capitalized function words (`Für`, `Den`, `Und`, `Mit` …) after the first word of a heading.

**Calques (review).** Phrases translated word for word from English: `Sinn machen` (Sinn ergeben), `einmal mehr` (wieder einmal), `am Ende des Tages`, `auf das nächste Level`, `Game-Changer`, `Wandteppich`, `ein Muss für`, `eintauchen in`, `in 2026` (2026 or im Jahr 2026), `realisieren, dass` (merken, erkennen), and `AI` for `KI`.

**Participle tails (review).** A sentence that ends in a present participle comment, copied from the English `…, highlighting its importance`: `…, ihre Bedeutung hervorhebend.` The checker uses a closed list (`hervorhebend`, `betonend`, `unterstreichend`, `widerspiegelnd`, `gewährleistend` …).

**Du and Sie (block).** A text that addresses the reader as both `du` and `Sie`. Quotations are excluded.

**Gender forms.** Whether a text uses `Kund*innen`, `Kund:innen`, `Kund_innen`, `KundInnen`, `Kund(inn)en` or `Kund/-innen` is the writer's choice and not an AI tell. The baseline only checks consistency: `DE_GENDER_MIX` (review) when one text mixes two different gender characters, or a gender form with the plain form of the same word (`Kund*innen` and `Kunden`). The pair form (`Kundinnen und Kunden`) and neutral nouns (`Kundschaft`) are standard German and never flagged. A voice that does not use gender characters sets `gender_characters` to `forbidden` (block on every form) or `review`.

**Mechanical connectives (review).** `darüber hinaus`, `des Weiteren`, `ferner`, `überdies`, `zudem`, `zusätzlich`, `außerdem`, `infolgedessen`, `andererseits`. One of them is normal German. Two or more at one per 150 words or denser is the AI rate.

**ASCII umlauts (block) and ss for ß (review).** `fuer`, `ueber`, `koennen`, `Aenderung` … are blocked. `Strasse`, `ausserdem`, `heisst` … are a review hit, because standard German writes ß.

---

## What is not a tell in German

These look like tells to an English checker. The German baseline leaves them alone.

- Many commas. Subordinate clauses require them, so the comma rate is no sign of anything.
- Long compound nouns (`Donaudampfschifffahrtsgesellschaft`).
- One `außerdem` or `zudem`. Only the density is a tell.
- The passive. Human German uses it. A study of ChatGPT German (Drackert et al. 2025) found too few passives, not too many.
- `statt` inside a long sentence.

---

## What is enforced by code

German voices run every rule of `00-universal-baseline.md` with the German word lists, plus these rules. Severity is the default before any profile override.

| Rule id | Detects | Default severity | Profile knob |
| --- | --- | --- | --- |
| `DE_QUOTES` | Straight or English quotation marks | block | `rule_overrides` |
| `DE_DASH` | Spaced en dash or spaced hyphen used as a dash | review | `register.en_dash` = off, review or block |
| `DE_NUMBER_FORMAT` | Number without space before a unit, abbreviation without space, English decimal point, English date | review | `rule_overrides` |
| `DE_HEADING_CASE` | Capitalized function word after the first word of a heading | review | `rule_overrides` |
| `DE_CALQUE` | Word-for-word translation from English, `in` before a year, `realisieren, dass`, `AI` | review | `rule_overrides` |
| `DE_PARTICIPLE_TAIL` | Sentence ending in a present participle comment from the closed list | review | `rule_overrides` |
| `DE_ADDRESS_MIX` | Both du and Sie address the reader | block | `rule_overrides` |
| `DE_GENDER_MIX` | Two different gender characters, or a gender form next to the plain form of the same word | review | `register.gender_characters` = off |
| `DE_GENDER_FORM` | Any gender character, only when the voice sets `gender_characters` to review or forbidden | review or block | `register.gender_characters` |
| `DE_CONNECTIVE_DENSITY` | Two or more mechanical connectives at one per 150 words or denser | review | `rule_overrides` |
| `DE_ASCII_UMLAUT` | Umlaut written as two letters | block | `rule_overrides` |
| `DE_SS_SPELLING` | ss where standard German writes ß | review | `rule_overrides` |

The German goldens are `eval/goldens/universal-de.goldens.jsonl` with the baseline `eval/baselines/universal-de.json`. Run them with `python eval/voice_eval.py score --goldens eval/goldens/universal-de.goldens.jsonl --language de --gate eval/baselines/universal-de.json`.
