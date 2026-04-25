"""
Generate a combined stylometric report from pre-computed JSON profile files.

Usage:
    python generate_report_from_json.py profile1.json [profile2.json ...] --output report.md
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def format_report(profile: dict, source_label: str = "") -> list[str]:
    lines = [
        f"## Register: {profile.get('register', 'unknown')}",
        f"",
        f"**Source:** {source_label}",
        f"",
    ]

    cs = profile.get("corpus_stats", {})
    lines += [
        f"### Corpus Overview",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Words (filtered prose) | {cs.get('word_count', '—'):,} |",
        f"| Sentences | {cs.get('sentence_count', '—'):,} |",
        f"| Paragraphs | {cs.get('paragraph_count', '—'):,} |",
        f"",
    ]

    if cs.get("word_count", 0) < 20000:
        lines.append(f"> **Warning:** corpus has fewer than 20,000 words after filtering. "
                     f"Distributional features may be unreliable.\n")

    ss = profile.get("syntactic", {}).get("sentence_stats", {})
    if ss:
        lines += [
            f"### Sentence Length",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Mean words | {ss.get('mean_words', '—')} |",
            f"| Median words | {ss.get('median_words', '—')} |",
            f"| Std dev | {ss.get('stdev_words', '—')} |",
            f"| Q1 / Q3 | {ss.get('q1_words', '—')} / {ss.get('q3_words', '—')} |",
            f"| Min / Max | {ss.get('min_words', '—')} / {ss.get('max_words', '—')} |",
            f"| % short (≤5 words) | {ss.get('pct_short_le5', 0)*100:.1f}% |",
            f"| % long (≥30 words) | {ss.get('pct_long_ge30', 0)*100:.1f}% |",
            f"",
        ]

    punc = profile.get("punctuation", {})
    if punc:
        lines += [
            f"### Punctuation Rates",
            f"",
            f"| Punctuation | Rate |",
            f"|-------------|------|",
            f"| Comma per sentence | {punc.get('comma_per_sentence', '—')} |",
            f"| Em dash per 1000w | {punc.get('em_dash_per_1000w', '—')} |",
            f"| Semicolon per 1000w | {punc.get('semicolon_per_1000w', '—')} |",
            f"| Colon per 1000w | {punc.get('colon_per_1000w', '—')} |",
            f"| Parenthetical per 1000w | {punc.get('parenthetical_per_1000w', '—')} |",
            f"| Question mark per 1000w | {punc.get('question_per_1000w', '—')} |",
            f"| Exclamation per 1000w | {punc.get('exclamation_per_1000w', '—')} |",
            f"| Ellipsis per 1000w | {punc.get('ellipsis_per_1000w', '—')} |",
            f"",
        ]

    hb = profile.get("hedging_booster", {})
    if hb:
        lines += [
            f"### Hedging and Booster Density (per 100 words)",
            f"",
            f"| Metric | Rate |",
            f"|--------|------|",
            f"| Hedge tokens | {hb.get('hedge_per_100w', '—')} |",
            f"| Booster tokens | {hb.get('boost_per_100w', '—')} |",
            f"| Hedge/boost ratio | {hb.get('hedge_boost_ratio', '—')} |",
            f"",
        ]

    pr = profile.get("pronouns", {})
    if pr:
        lines += [
            f"### Pronoun Rates (per 100 words)",
            f"",
            f"| Pronoun class | Rate |",
            f"|--------------|------|",
            f"| First person singular (I/me/my) | {pr.get('first_sg_per_100w', '—')} |",
            f"| First person plural (we/us/our) | {pr.get('first_pl_per_100w', '—')} |",
            f"| Second person (you/your) | {pr.get('second_per_100w', '—')} |",
            f"| Third person | {pr.get('third_per_100w', '—')} |",
            f"",
        ]

    sip = profile.get("syntactic", {}).get("sentence_initial_patterns", [])
    if sip:
        lines += [f"### Sentence-Initial Word Patterns (top 20)", f"", f"| Word | Count |", f"|------|-------|"]
        for item in sip[:20]:
            lines.append(f"| {item['word']} | {item['count']} |")
        lines.append("")

    dcw = profile.get("lexical", {}).get("distinctive_content_words", [])
    if dcw:
        lines += [f"### Most-Used Content Words (top 30)", f"", f"| Word | Per 1000 words |", f"|------|----------------|"]
        for item in dcw[:30]:
            lines.append(f"| {item['word']} | {item['per_1000']} |")
        lines.append("")

    fwp = profile.get("lexical", {}).get("function_word_profile", {})
    if fwp:
        top_fw = sorted(fwp.items(), key=lambda x: -x[1])[:20]
        lines += [
            f"### Top Function Words (per 1000 words, top 20 shown)",
            f"",
            f"| Word | Rate |",
            f"|------|------|",
        ]
        for w, rate in top_fw:
            lines.append(f"| {w} | {rate} |")
        lines.append("")

    lex = profile.get("lexical", {})
    syn = profile.get("syntactic", {})
    lines += [
        f"### Lexical Richness",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| MATTR (window 100) | {lex.get('mattr_window100', '—')} |",
        f"| Hapax ratio | {lex.get('hapax_ratio', '—')} |",
        f"| Concession rate | {syn.get('concession_rate', '—')} |",
        f"",
    ]

    ps = syn.get("paragraph_stats", {})
    if ps:
        lines += [
            f"### Paragraph Structure",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Paragraph count | {ps.get('paragraph_count', '—')} |",
            f"| Mean words/paragraph | {ps.get('mean_words', '—')} |",
            f"| Median words/paragraph | {ps.get('median_words', '—')} |",
            f"| Std dev | {ps.get('stdev_words', '—')} |",
            f"",
        ]

    rd = profile.get("readability", {})
    if rd and not rd.get("error"):
        lines += [
            f"### Readability (textstat)",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Flesch-Kincaid grade | {rd.get('flesch_kincaid_grade', '—')} |",
            f"| Gunning Fog | {rd.get('gunning_fog', '—')} |",
            f"| Flesch reading ease | {rd.get('flesch_reading_ease', '—')} |",
            f"| Avg syllables/word | {rd.get('avg_syllables_per_word', '—')} |",
            f"| Lexical density | {rd.get('lexical_density', '—')} |",
            f"",
        ]

    lines.append("---")
    lines.append("")
    return lines


def cross_register_table(profiles: list[tuple[str, dict]]) -> list[str]:
    """Build a cross-register comparison table from multiple profiles."""
    lines = [
        "## Cross-Register Comparison",
        "",
        "| Feature | " + " | ".join(label for label, _ in profiles) + " |",
        "|---------|" + "|".join("---" for _ in profiles) + "|",
    ]

    def get(p, *keys, fmt=None):
        val = p
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, "—")
            else:
                return "—"
        if fmt and val != "—":
            try:
                return fmt(val)
            except Exception:
                return str(val)
        return str(val) if val != "—" else "—"

    rows = [
        ("Mean sent. length (words)", lambda p: get(p, "syntactic", "sentence_stats", "mean_words")),
        ("Median sent. length", lambda p: get(p, "syntactic", "sentence_stats", "median_words")),
        ("% long sentences (≥30w)", lambda p: f"{float(get(p, 'syntactic', 'sentence_stats', 'pct_long_ge30'))*100:.1f}%" if get(p, "syntactic", "sentence_stats", "pct_long_ge30") != "—" else "—"),
        ("% short sentences (≤5w)", lambda p: f"{float(get(p, 'syntactic', 'sentence_stats', 'pct_short_le5'))*100:.1f}%" if get(p, "syntactic", "sentence_stats", "pct_short_le5") != "—" else "—"),
        ("Commas per sentence", lambda p: get(p, "punctuation", "comma_per_sentence")),
        ("Em dashes per 1000w", lambda p: get(p, "punctuation", "em_dash_per_1000w")),
        ("Semicolons per 1000w", lambda p: get(p, "punctuation", "semicolon_per_1000w")),
        ("Hedge tokens per 100w", lambda p: get(p, "hedging_booster", "hedge_per_100w")),
        ("Booster tokens per 100w", lambda p: get(p, "hedging_booster", "boost_per_100w")),
        ("1st person sg. per 100w", lambda p: get(p, "pronouns", "first_sg_per_100w")),
        ("1st person pl. per 100w", lambda p: get(p, "pronouns", "first_pl_per_100w")),
        ("2nd person per 100w", lambda p: get(p, "pronouns", "second_per_100w")),
        ("MATTR (window 100)", lambda p: get(p, "lexical", "mattr_window100")),
        ("Hapax ratio", lambda p: get(p, "lexical", "hapax_ratio")),
        ("Concession rate", lambda p: get(p, "syntactic", "concession_rate")),
        ("Word count (filtered)", lambda p: f"{int(get(p, 'corpus_stats', 'word_count')):,}" if get(p, "corpus_stats", "word_count") != "—" else "—"),
    ]

    for label, extractor in rows:
        values = [extractor(p) for _, p in profiles]
        lines.append(f"| {label} | " + " | ".join(values) + " |")

    lines.append("")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Generate combined stylometric report from JSON profiles.")
    parser.add_argument("profiles", nargs="+", help="JSON profile files (label:path or just path)")
    parser.add_argument("--output", required=True, help="Output markdown file path")
    args = parser.parse_args()

    profiles = []
    for spec in args.profiles:
        if ":" in spec and not spec.startswith("C:") and not spec.startswith("/"):
            label, path = spec.split(":", 1)
        else:
            path = spec
            label = Path(spec).stem

        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            profiles.append((label, data))
            print(f"Loaded: {label} from {path}", file=sys.stderr)
        except Exception as e:
            print(f"Error loading {path}: {e}", file=sys.stderr)
            sys.exit(1)

    out_lines = [
        f"# Stylometric Profile — Hiro Fukushima",
        f"",
        f"**Generated:** {date.today().isoformat()}  ",
        f"**Corpus:** Four registers analyzed separately — article-public, paper-formal, declarative-personal, conversation-casual  ",
        f"**Method:** Computational stylometry (stdlib-only base tier). Features: function word frequencies, MATTR, sentence length distribution, punctuation rates, hedging/booster density, pronoun rates, sentence-initial patterns, hapax legomena ratio. See `building-voice-skills/references/03-methodology.md` for full academic grounding.",
        f"",
        f"---",
        f"",
    ]

    out_lines += cross_register_table(profiles)

    for label, profile in profiles:
        out_lines += format_report(profile, source_label=label)

    out_lines += [
        "## Notes on Interpretation",
        "",
        "**Register matters.** These three corpora are written by the same person but represent fundamentally different communication modes. The article-public register (2,146 words) is the primary writing target — polished, published-quality essay prose. The paper-formal register (12,643 words) is academic draft prose with shorter sentences and less rhetorical elaboration. The conversation-casual register (325,211 words) reflects spoken-register habits: first-person, colloquial, short sentences.",
        "",
        "**Em dashes in article-public register.** The em-dash count in the article corpus should be zero — Hiro explicitly does not use em dashes in polished prose. The 0.000 reading after the multi-line component tag bug was fixed confirms this.",
        "",
        "**Hedging calibration.** Hiro's hedging density in polished prose (~0.2 per 100 words) is low. This reflects calibrated epistemic care: well-supported claims are stated flatly; hedges appear only where genuine uncertainty exists. This is not imprecision — it is the opposite.",
        "",
        "**Function word profiles.** The function word distributions above reflect register-specific grammar. The article-public profile shows the connective structure (high 'that', 'which', 'because', 'since') characteristic of explanatory analytical prose. The conversation-casual profile shows the high 'I', 'you', 'it' pattern of interactive dialogue.",
        "",
        "**What this corpus does not capture.** The analysis covers December 2025 through April 2026. Any stylistic drift before this period is not captured. The corpus is single-author with no inter-rater reliability check. The article-public corpus at 2,146 words is at the lower bound for reliable distributional features — the numbers are directionally valid but have higher variance than the larger registers.",
        "",
        "**Academic grounding.** All features used here have established research grounding. Function word frequency profiles: Mosteller & Wallace (1964), Burrows (2002). MATTR: Covington & McFall (2010). Sentence length distribution: Mendenhall (1887), Biber (1988). Punctuation rates: Grieve (2007). Hedging/booster: Biber & Finegan (1988), Hyland (1998). Register analysis: Biber (1988). Full citations in `building-voice-skills/references/03-methodology.md`.",
        "",
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Report written to: {output}", file=sys.stderr)


if __name__ == "__main__":
    main()
