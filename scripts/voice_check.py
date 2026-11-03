#!/usr/bin/env python3
"""voice_check.py - deterministic voice gate for one draft.

Usage:
    python voice_check.py <draft.md | -> [--profile profile.json] [--register NAME]
                                       [--json] [--strict] [--quiet]
                                       [--explanation FILE] [--rejected FILE]

Verdict: PASS (no hits), REVIEW (review hits only), BLOCK (any block hit).
Exit:    0 PASS or REVIEW | 1 BLOCK | 2 input or profile error
The last stdout line is VOICE_CHECK_PASS, VOICE_CHECK_REVIEW, or VOICE_CHECK_BLOCK.
Without --profile only the universal baseline runs. Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stylometry import (compute_hedging_booster, compute_pronoun_rates, compute_punctuation_rates,  # noqa: E402
                        compute_sentence_stats, split_sentences, tokenize_words)
from voice_lang import LANGUAGES, detect_language, lang_of  # noqa: E402
from voice_profile import default_profile, load_profile, resolve_register, validate_profile  # noqa: E402
from voice_rules import BLOCK, REVIEW, run_rules  # noqa: E402
from voice_segment import prose_text, segment  # noqa: E402

import re  # noqa: E402

CITATION_HEADINGS = re.compile(r"^(sources?|references?|bibliography|further reading|see also|related( articles| reading| links| topics)?|citations?|works cited|footnotes?"
                               r"|quellen|literatur(verzeichnis)?|einzelnachweise|weiterführende|siehe auch|fußnoten|anmerkungen)\b", re.IGNORECASE)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def compute_drift(text: str, profile: dict, reg: dict) -> list:
    targets = reg.get("targets") or {}
    if not targets:
        return []
    words = tokenize_words(text)
    if len(words) < int(profile.get("thresholds", {}).get("min_words_for_drift", 150)):
        return []
    sentences = split_sentences(text)
    stats = compute_sentence_stats(sentences)
    punct = compute_punctuation_rates(text, len(words))
    lang = lang_of(profile)
    hb = compute_hedging_booster(words, text, lang)
    pron = compute_pronoun_rates(words, lang)
    observed = {
        "mean_sentence_words": stats.get("mean_words"),
        "pct_short_le5_max": stats.get("pct_short_le5"),
        "pct_long_ge30": stats.get("pct_long_ge30"),
        "comma_per_sentence": punct.get("comma_per_sentence"),
        "hedge_per_100w_max": hb.get("hedge_per_100w"),
        "hedge_per_100w_mean": hb.get("hedge_per_100w"),
        "boost_per_100w_max": hb.get("boost_per_100w"),
        "first_sg_per_100w_max": pron.get("first_sg_per_100w"),
    }
    tolerance = float(profile.get("thresholds", {}).get("hedge_tolerance", 0.5))
    provisional = (profile.get("provisional") or {}).get("rules", [])
    drift = []
    for key, target in targets.items():
        value = observed.get(key)
        if value is None:
            continue
        if isinstance(target, list):
            out = value < target[0] or value > target[1]
        elif key == "hedge_per_100w_mean":
            out = abs(value - target) > tolerance
        else:
            out = value > target
        if out:
            entry = {"metric": key.replace("_max", ""), "observed": value, "target": target, "severity": REVIEW}
            if "targets" in provisional or key in provisional:
                entry["provisional"] = True
            drift.append(entry)
    return drift


def check_text(text: str, profile: dict, register: str, draft_name: str = "-", skip_citations: bool = True,
               explanation=None, rejected=None) -> dict:
    reg = resolve_register(profile, register)
    segs = segment(text)
    if skip_citations:
        segs = [s for s in segs if not CITATION_HEADINGS.match(s.heading or "")]
    hits = run_rules(segs, profile, reg, {"explanation": explanation, "rejected": rejected or []})
    drift = compute_drift(prose_text(segs), profile, reg)
    counts = {}
    for h in hits:
        counts[h.rule] = counts.get(h.rule, 0) + 1
    if any(h.severity == BLOCK for h in hits):
        verdict = "BLOCK"
    elif any(h.severity == REVIEW for h in hits) or drift:
        verdict = "REVIEW"
    else:
        verdict = "PASS"
    return {
        "draft": draft_name,
        "voice": profile.get("voice", "universal"),
        "register": register,
        "word_count": len(tokenize_words(prose_text(segs))),
        "language": lang_of(profile),
        "verdict": verdict,
        "counts": counts,
        "hits": [h.__dict__ for h in hits],
        "drift": drift,
    }


def render(result: dict, quiet: bool) -> str:
    lines = []
    if not quiet:
        lines.append("voice=%s register=%s language=%s words=%d" % (
            result["voice"], result["register"], result.get("language", "en"), result["word_count"]))
        for h in result["hits"]:
            lines.append("%-6s L%-4d %-24s %s  | %s" % (h["severity"], h["line"], h["rule"], h["message"], h["excerpt"]))
        for d in result["drift"]:
            lines.append("review drift %-22s observed=%s target=%s%s" % (
                d["metric"], d["observed"], d["target"], " (provisional)" if d.get("provisional") else ""))
        lines.append("verdict=%s block=%d review=%d drift=%d" % (
            result["verdict"], sum(1 for h in result["hits"] if h["severity"] == BLOCK),
            sum(1 for h in result["hits"] if h["severity"] == REVIEW), len(result["drift"])))
        info = sum(1 for h in result["hits"] if h["severity"] == "info")
        if info:
            lines.append("info=%d (reported, no effect on the verdict)" % info)
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("draft", help="Path to a Markdown or text file, or - for stdin")
    parser.add_argument("--profile", help="voices/<name>/profile.json (default: universal baseline only)")
    parser.add_argument("--register", help="Register name inside the profile")
    parser.add_argument("--json", action="store_true", help="Print the JSON result instead of the table")
    parser.add_argument("--strict", action="store_true", help="Treat review hits and drift as blocking")
    parser.add_argument("--quiet", action="store_true", help="Print only the final token")
    parser.add_argument("--explanation", help="File with the approved explanation. Every number and name in the draft must appear in it")
    parser.add_argument("--rejected", help="File with one rejected phrase per line. Any of them in the draft blocks")
    parser.add_argument("--language", choices=LANGUAGES,
                        help="Baseline language without --profile: en or de (standard German). "
                             "Default: detected from the draft. A profile sets its own")
    parser.add_argument("--check-citations", action="store_true",
                        help="Also check text under Sources, References, and similar headings (skipped by default)")
    args = parser.parse_args(argv)

    try:
        text = sys.stdin.read() if args.draft == "-" else Path(args.draft).read_text(encoding="utf-8")
    except OSError as exc:
        print("ERROR: cannot read draft: %s" % exc)
        return 2
    profile = default_profile(args.language or detect_language(text))
    if args.profile:
        try:
            profile = load_profile(args.profile)
        except (OSError, ValueError) as exc:
            print("ERROR: cannot read profile: %s" % exc)
            return 2
        errors = validate_profile(profile)
        if errors:
            for err in errors:
                print("ERROR: " + err)
            return 2
    register = args.register or profile.get("default_register", "default")
    explanation, rejected = None, None
    try:
        if args.explanation:
            explanation = Path(args.explanation).read_text(encoding="utf-8")
        if args.rejected:
            rejected = [ln.strip() for ln in Path(args.rejected).read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError as exc:
        print("ERROR: cannot read context file: %s" % exc)
        return 2
    result = check_text(text, profile, register, args.draft, skip_citations=not args.check_citations,
                        explanation=explanation, rejected=rejected)
    if args.strict and result["verdict"] == "REVIEW":
        result["verdict"] = "BLOCK"
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        out = render(result, args.quiet)
        if out:
            print(out)
    print("VOICE_CHECK_" + result["verdict"])
    return 1 if result["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
