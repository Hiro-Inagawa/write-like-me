#!/usr/bin/env python3
"""voice_profile.py - load, validate, and initialize a voice profile.json.

Subcommands:
  validate <profile.json>                          exit 0 and print VOICE_PROFILE_VALID
  preflight [--corpus-words N]                     print dependency and corpus-size notes before analysis
  init --voice NAME --register NAME --from-stylometry FILE --output FILE
                                                   build a profile from a stylometry register JSON

Stdlib only. Exit codes: 0 ok | 2 invalid input.
"""
import argparse
import copy
import json
import sys
from datetime import date
from pathlib import Path

SCHEMA_VERSION = 1
TRISTATE = ("off", "review", "block")
LEVELS = ("off", "info", "review", "block")
POLICY = ("off", "allowed", "review", "forbidden")
MIN_CORPUS_WORDS = 20000

DEFAULT_REGISTER = {
    "semicolons": "off",
    "announcement_colon": "review",
    "contractions": "off",
    "questions": "off",
    "hedge_connectives": "review",
    "meta_commentary": "off",
    "tricolon": "info",
    "compressed_antithesis": "review",
    "closing_caveat": "review",
    "benefit_tail": "review",
    "tagline": "review",
    "additions": "review",
    "empty_intensifiers": "block",
    "exclamations": "off",
    "targets": {},
}

DEFAULT_PROFILE = {
    "schema_version": SCHEMA_VERSION,
    "voice": "universal",
    "generated": "",
    "source": "references/00-universal-baseline.md",
    "default_register": "default",
    "thresholds": {"short_sentence_words": 8, "staccato_run": 3, "min_words_for_drift": 150,
                   "hedge_tolerance": 0.5},
    "bans": {
        "intensifiers": ["clearly", "obviously", "genuine", "genuinely", "fascinating",
                          "striking", "strikingly", "real and structured"],
        "hedge_connectives": ["that said", "to be fair", "worth knowing", "one thing to note",
                               "for what it's worth", "with one nuance", "one honest nuance",
                               "just so you are not surprised"],
        "protest_framing": ["none of this is", "this is not a", "it is not a gimmick", "is not theoretical"],
        "meta_commentary": ["great question", "i'd be happy to", "i would be happy to", "let me think",
                             "i want to make sure i understand", "that's a really interesting",
                             "hope this helps", "let me know if"],
        "evaluative_block": ["innovative", "groundbreaking", "revolutionary", "cutting-edge",
                              "state-of-the-art", "game-changing"],
        "evaluative_review": ["powerful", "robust", "significant", "important", "novel", "unique",
                               "compelling", "elegant", "fascinating", "remarkable", "exceptional"],
        "caveat_phrases": ["one thing to note", "that said", "worth knowing", "keep in mind", "to be fair",
                            "one caveat", "a small caveat", "note that", "just so you"],
        "extra_phrases": [],
    },
    "registers": {},
}

RANGE_KEYS = ("mean_sentence_words", "pct_long_ge30", "comma_per_sentence")
MAX_KEYS = ("pct_short_le5_max", "hedge_per_100w_max", "boost_per_100w_max", "first_sg_per_100w_max",
            "hedge_per_100w_mean")


def load_profile(path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def resolve_register(profile: dict, name: str) -> dict:
    reg = copy.deepcopy(DEFAULT_REGISTER)
    override = (profile.get("registers") or {}).get(name) or {}
    for key, value in override.items():
        if key == "targets":
            reg["targets"] = dict(value)
        else:
            reg[key] = value
    return reg


def validate_profile(profile: dict) -> list:
    errors = []
    if profile.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be %d" % SCHEMA_VERSION)
    for key in ("voice", "bans", "registers", "thresholds"):
        if key not in profile:
            errors.append("missing key: %s" % key)
    for key, value in (profile.get("bans") or {}).items():
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            errors.append("bans.%s must be a list of strings" % key)
    for key, value in (profile.get("thresholds") or {}).items():
        if not isinstance(value, (int, float)) or value < 0:
            errors.append("thresholds.%s must be a non-negative number" % key)
    for rule, level in (profile.get("rule_overrides") or {}).items():
        if level not in LEVELS:
            errors.append("rule_overrides.%s must be one of %s" % (rule, ", ".join(LEVELS)))
    prov = profile.get("provisional")
    if prov is not None and not (isinstance(prov, dict) and isinstance(prov.get("rules", []), list)
                                 and all(isinstance(r, str) for r in prov.get("rules", []))):
        errors.append("provisional must be an object with a list of rule names in 'rules'")
    for name, reg in (profile.get("registers") or {}).items():
        for key, value in reg.items():
            if key == "length":
                ok = (isinstance(value, dict) and set(value) <= {"min", "max"}
                      and all(isinstance(v, (int, float)) and v >= 0 for v in value.values()))
                if ok and "min" in value and "max" in value and value["min"] > value["max"]:
                    ok = False
                if not ok:
                    errors.append("registers.%s.length must be {min, max} with min <= max" % name)
                continue
            if key == "targets":
                for tkey, tval in value.items():
                    if tkey in RANGE_KEYS and not (isinstance(tval, list) and len(tval) == 2 and tval[0] <= tval[1]):
                        errors.append("registers.%s.targets.%s must be [low, high]" % (name, tkey))
                    elif tkey in MAX_KEYS and not isinstance(tval, (int, float)):
                        errors.append("registers.%s.targets.%s must be a number" % (name, tkey))
                    elif tkey not in RANGE_KEYS + MAX_KEYS:
                        errors.append("registers.%s.targets.%s is not a known target" % (name, tkey))
            elif key in ("semicolons", "contractions", "questions"):
                if value not in POLICY:
                    errors.append("registers.%s.%s must be one of %s" % (name, key, ", ".join(POLICY)))
            elif key == "tricolon":
                if value not in LEVELS:
                    errors.append("registers.%s.tricolon must be one of %s" % (name, ", ".join(LEVELS)))
            elif key in ("announcement_colon", "hedge_connectives", "meta_commentary", "compressed_antithesis",
                         "closing_caveat", "benefit_tail", "tagline", "additions",
                         "empty_intensifiers", "exclamations"):
                if value not in TRISTATE:
                    errors.append("registers.%s.%s must be one of %s" % (name, key, ", ".join(TRISTATE)))
            else:
                errors.append("registers.%s.%s is not a known key" % (name, key))
    return errors


def _rng(value, spread, lo=0, digits=0):
    low = max(lo, round(value * (1 - spread), digits))
    high = round(value * (1 + spread), digits)
    if digits == 0:
        low, high = int(low), int(high)
    return [low, high]


def init_from_stylometry(voice: str, register: str, stylo: dict) -> dict:
    sent = stylo["syntactic"]["sentence_stats"]
    punct = stylo["punctuation"]
    hb = stylo["hedging_booster"]
    pron = stylo["pronouns"]
    words = (stylo.get("corpus_stats") or {}).get("word_count")
    small = isinstance(words, (int, float)) and words < MIN_CORPUS_WORDS
    profile = copy.deepcopy(DEFAULT_PROFILE)
    profile["voice"] = voice
    profile["generated"] = date.today().isoformat()
    profile["source"] = "03-corpus-source.md"
    profile["default_register"] = register
    targets = {
        "mean_sentence_words": _rng(sent["mean_words"], 0.15),
        "pct_short_le5_max": round(max(sent["pct_short_le5"] * 1.5, sent["pct_short_le5"]), 3),
        "pct_long_ge30": [round(max(0.0, sent["pct_long_ge30"] - 0.05), 2), round(min(1.0, sent["pct_long_ge30"] + 0.05), 2)],
        "comma_per_sentence": _rng(punct["comma_per_sentence"], 0.15, digits=1),
        "hedge_per_100w_mean": round(hb["hedge_per_100w"], 3),
        "boost_per_100w_max": round(hb["boost_per_100w"], 2),
        "first_sg_per_100w_max": round(max(0.5, pron["first_sg_per_100w"] * 1.5), 2),
    }
    zero_semicolons = punct.get("semicolon_per_1000w", 1) == 0
    reg = {
        "semicolons": "forbidden" if (zero_semicolons and not small) else "review",
        "announcement_colon": "review",
        "contractions": "off",
        "questions": "off",
        "hedge_connectives": "review",
        "tricolon": "info",
        "compressed_antithesis": "review",
        "targets": targets,
    }
    profile["registers"] = {register: reg}
    if small:
        profile["provisional"] = provisional_entry(words, zero_semicolons, sent["pct_short_le5"] == 0)
    return profile


def provisional_entry(words, zero_semicolons: bool, zero_short: bool) -> dict:
    """Rules that rest on a corpus below MIN_CORPUS_WORDS. The author confirms or removes each one."""
    rules = ["targets"]
    if zero_semicolons:
        rules.append("semicolons")
    if zero_short:
        rules.append("pct_short_le5_max")
    return {
        "words": int(words),
        "min_words": MIN_CORPUS_WORDS,
        "rules": rules,
        "note": "The corpus is below %d words. Each listed rule is a candidate. Remove its name from this list "
                "once the author has confirmed it against a new text." % MIN_CORPUS_WORDS,
    }


def preflight(corpus_words=None) -> list:
    """Return one line per missing optional package and one for a small corpus."""
    lines = []
    for module, extra in (("textstat", "readability scores"),
                          ("spacy", "POS rhythm, dependency depth, passive voice")):
        try:
            __import__(module)
        except ImportError:
            lines.append("optional package %s is not installed, so %s will be skipped. pip install %s"
                         % (module, extra, module))
    if corpus_words is not None and corpus_words < MIN_CORPUS_WORDS:
        lines.append("corpus has %d words, below %d. Every distribution-based rule will be emitted as provisional."
                     % (corpus_words, MIN_CORPUS_WORDS))
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("profile")
    i = sub.add_parser("init")
    i.add_argument("--voice", required=True)
    i.add_argument("--register", required=True)
    i.add_argument("--from-stylometry", required=True)
    i.add_argument("--output", required=True)
    pf = sub.add_parser("preflight", help="report missing optional packages and a small corpus before analysis")
    pf.add_argument("--corpus-words", type=int)
    args = parser.parse_args(argv)

    if args.cmd == "preflight":
        for line in preflight(args.corpus_words):
            print("NOTE: " + line)
        print("VOICE_PREFLIGHT_DONE")
        return 0

    if args.cmd == "validate":
        try:
            profile = load_profile(args.profile)
        except (OSError, ValueError) as exc:
            print("ERROR: cannot read profile: %s" % exc)
            return 2
        errors = validate_profile(profile)
        for err in errors:
            print("ERROR: " + err)
        if errors:
            return 2
        print("VOICE_PROFILE_VALID")
        return 0

    stylo = load_profile(args.from_stylometry)
    profile = init_from_stylometry(args.voice, args.register, stylo)
    out = Path(args.output)
    if out.exists():
        print("ERROR: refusing to overwrite %s" % out)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print("wrote %s" % out)
    print("VOICE_PROFILE_VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
