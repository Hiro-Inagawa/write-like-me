#!/usr/bin/env python3
"""voice_eval.py - score voice_check.py against golden passages and gate regressions.

Subcommands:
  score    --goldens FILE [--profile FILE] [--register NAME] [--gate BASELINE] [--tolerance 0.0] [--json OUT]
  baseline --goldens FILE [--profile FILE] [--register NAME] --output BASELINE
  verify   --profile FILE [--register NAME] [--strict] SAMPLE...
  selftest

Metrics: block_recall, review_recall, false_alarm_rate, review_noise, per-rule counts.
Exit: 0 ok | 1 a golden failed or the gate failed | 2 bad input
The last stdout line is VOICE_EVAL_OK or VOICE_EVAL_FAILED. Stdlib only.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from voice_check import check_text  # noqa: E402
from voice_profile import DEFAULT_PROFILE, default_profile, load_profile  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

EXPECTS = ("pass", "review", "block")


def load_goldens(path) -> list:
    items = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            item = json.loads(line)
            for key in ("id", "text", "expect"):
                if key not in item:
                    raise ValueError("golden line %d is missing '%s'" % (n, key))
            if item["expect"] not in EXPECTS:
                raise ValueError("golden %s has expect=%r" % (item["id"], item["expect"]))
            items.append(item)
    ids = [i["id"] for i in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate golden ids")
    return items


def _bucket(per_rule, rule):
    return per_rule.setdefault(rule, {"expected": 0, "hit": 0, "missed": 0, "spurious": 0})


def score(goldens: list, profile: dict, register: str) -> dict:
    rows, per_rule = [], {}
    for g in goldens:
        reg_name = g.get("register", register)
        prof = profile
        if g.get("register_overrides"):
            prof = copy.deepcopy(profile)
            prof.setdefault("registers", {}).setdefault(reg_name, {}).update(g["register_overrides"])
        result = check_text(g["text"], prof, reg_name, g["id"],
                            explanation=g.get("explanation"), rejected=g.get("rejected"))
        hit_rules = set(result["counts"])
        expected = set(g.get("rules", []))
        verdict = result["verdict"]
        if g["expect"] == "block":
            ok = verdict == "BLOCK" and expected <= hit_rules
        elif g["expect"] == "review":
            ok = verdict in ("REVIEW", "BLOCK") and expected <= hit_rules
        else:
            ok = verdict != "BLOCK" and expected <= hit_rules
        rows.append({"id": g["id"], "expect": g["expect"], "verdict": verdict, "hits": sorted(hit_rules), "ok": ok})
        for rule in expected:
            b = _bucket(per_rule, rule)
            b["expected"] += 1
            b["hit" if rule in hit_rules else "missed"] += 1
        if g["expect"] == "pass":
            for rule in hit_rules - expected:
                _bucket(per_rule, rule)["spurious"] += 1

    def share(kind, pred):
        subset = [r for r in rows if r["expect"] == kind]
        return round(sum(1 for r in subset if pred(r)) / len(subset), 4) if subset else None

    metrics = {
        "n": len(rows),
        "block_recall": share("block", lambda r: r["ok"]),
        "review_recall": share("review", lambda r: r["ok"]),
        "false_alarm_rate": share("pass", lambda r: r["verdict"] == "BLOCK"),
        "review_noise": share("pass", lambda r: r["verdict"] == "REVIEW"),
        "failures": [r["id"] for r in rows if not r["ok"]],
    }
    return {"metrics": metrics, "per_rule": per_rule, "rows": rows}


def gate(metrics: dict, baseline: dict, tol: float) -> list:
    problems = []
    for key, direction in (("block_recall", -1), ("review_recall", -1), ("false_alarm_rate", 1)):
        cur, base = metrics.get(key), baseline.get(key)
        if cur is None or base is None:
            continue
        if direction < 0 and cur < base - tol:
            problems.append("%s fell from %.4f to %.4f" % (key, base, cur))
        if direction > 0 and cur > base + tol:
            problems.append("%s rose from %.4f to %.4f" % (key, base, cur))
    return problems


def _report(result: dict) -> None:
    m = result["metrics"]
    print("goldens=%d block_recall=%s review_recall=%s false_alarm_rate=%s review_noise=%s" % (
        m["n"], m["block_recall"], m["review_recall"], m["false_alarm_rate"], m["review_noise"]))
    print("%-26s %8s %5s %6s %8s" % ("rule", "expected", "hit", "missed", "spurious"))
    for rule, b in sorted(result["per_rule"].items()):
        print("%-26s %8d %5d %6d %8d" % (rule, b["expected"], b["hit"], b["missed"], b["spurious"]))
    for row in result["rows"]:
        if not row["ok"]:
            print("FAIL %s expect=%s verdict=%s hits=%s" % (row["id"], row["expect"], row["verdict"], ",".join(row["hits"])))


def verify_files(paths: list, profile: dict, register: str, strict: bool = False) -> dict:
    """Score paragraphs a person generated with any agent. Each file is one sample.
    A sample fails on BLOCK, and with strict on REVIEW or drift as well."""
    rows = []
    for path in paths:
        text = Path(path).read_text(encoding="utf-8")
        result = check_text(text, profile, register, str(path))
        bad = result["verdict"] == "BLOCK" or (strict and result["verdict"] == "REVIEW")
        rows.append({"file": str(path), "verdict": result["verdict"], "ok": not bad,
                     "hits": result["hits"], "drift": result["drift"]})
    return {"rows": rows, "ok": bool(rows) and all(r["ok"] for r in rows)}


def _selftest() -> int:
    fix = ROOT / "tests" / "fixtures"
    goldens = [
        {"id": "bad", "text": (fix / "ai_tells.md").read_text(encoding="utf-8"), "expect": "block", "rules": ["EM_DASH"]},
        {"id": "good", "text": (fix / "clean.md").read_text(encoding="utf-8"), "expect": "pass"},
    ]
    result = score(goldens, DEFAULT_PROFILE, "default")
    ok = result["metrics"]["failures"] == []
    print("VOICE_EVAL_OK" if ok else "VOICE_EVAL_FAILED")
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("score", "baseline"):
        p = sub.add_parser(name)
        p.add_argument("--goldens", required=True)
        p.add_argument("--profile")
        p.add_argument("--register")
        p.add_argument("--language", choices=("en", "de"), default="en",
                       help="Baseline language when no --profile is given")
        if name == "score":
            p.add_argument("--gate")
            p.add_argument("--tolerance", type=float, default=0.0)
            p.add_argument("--json")
        else:
            p.add_argument("--output", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--profile", required=True)
    v.add_argument("--register")
    v.add_argument("--strict", action="store_true")
    v.add_argument("samples", nargs="+")
    sub.add_parser("selftest")
    args = parser.parse_args(argv)
    if args.cmd == "selftest":
        return _selftest()
    if args.cmd == "verify":
        try:
            profile = load_profile(args.profile)
            register = args.register or profile.get("default_register", "default")
            outcome = verify_files(args.samples, profile, register, args.strict)
        except (OSError, ValueError) as exc:
            print("ERROR: %s" % exc)
            return 2
        for row in outcome["rows"]:
            print("%s %s" % ("ok  " if row["ok"] else "FAIL", row["file"]))
            print("     verdict=%s hits=%d drift=%d" % (row["verdict"], len(row["hits"]), len(row["drift"])))
            for h in row["hits"]:
                if h["severity"] != "info":
                    print("     %-6s L%-4d %-22s %s" % (h["severity"], h["line"], h["rule"], h["message"]))
            for d in row["drift"]:
                print("     drift  %-22s observed=%s target=%s%s" % (
                    d["metric"], d["observed"], d["target"], " (provisional)" if d.get("provisional") else ""))
        print("VOICE_EVAL_OK" if outcome["ok"] else "VOICE_EVAL_FAILED")
        return 0 if outcome["ok"] else 1
    try:
        goldens = load_goldens(args.goldens)
        profile = load_profile(args.profile) if args.profile else default_profile(args.language)
    except (OSError, ValueError) as exc:
        print("ERROR: %s" % exc)
        return 2
    register = args.register or profile.get("default_register", "default")
    result = score(goldens, profile, register)
    _report(result)
    if args.cmd == "baseline":
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result["metrics"], indent=2) + "\n", encoding="utf-8")
        print("wrote %s" % out)
        ok = not result["metrics"]["failures"]
        print("VOICE_EVAL_OK" if ok else "VOICE_EVAL_FAILED")
        return 0 if ok else 1
    problems = []
    if args.gate:
        try:
            problems = gate(result["metrics"], load_profile(args.gate), args.tolerance)
        except (OSError, ValueError) as exc:
            print("ERROR: cannot read baseline: %s" % exc)
            return 2
        for p in problems:
            print("GATE " + p)
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ok = not result["metrics"]["failures"] and not problems
    print("VOICE_EVAL_OK" if ok else "VOICE_EVAL_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
