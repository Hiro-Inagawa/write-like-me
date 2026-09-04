#!/usr/bin/env python3
"""voice_eval.py - score voice_check.py against golden passages and gate regressions.

Subcommands:
  score    --goldens FILE [--profile FILE] [--register NAME] [--gate BASELINE] [--tolerance 0.0] [--json OUT]
  baseline --goldens FILE [--profile FILE] [--register NAME] --output BASELINE
  selftest

Metrics: block_recall, review_recall, false_alarm_rate, review_noise, per-rule counts.
Exit: 0 ok | 1 a golden failed or the gate failed | 2 bad input
The last stdout line is VOICE_EVAL_OK or VOICE_EVAL_FAILED. Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from voice_check import check_text  # noqa: E402
from voice_profile import DEFAULT_PROFILE, load_profile  # noqa: E402

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
        result = check_text(g["text"], profile, g.get("register", register), g["id"])
        hit_rules = set(result["counts"])
        expected = set(g.get("rules", []))
        verdict = result["verdict"]
        if g["expect"] == "block":
            ok = verdict == "BLOCK" and expected <= hit_rules
        elif g["expect"] == "review":
            ok = verdict in ("REVIEW", "BLOCK") and expected <= hit_rules
        else:
            ok = verdict != "BLOCK"
        rows.append({"id": g["id"], "expect": g["expect"], "verdict": verdict, "hits": sorted(hit_rules), "ok": ok})
        for rule in expected:
            b = _bucket(per_rule, rule)
            b["expected"] += 1
            b["hit" if rule in hit_rules else "missed"] += 1
        if g["expect"] == "pass":
            for rule in hit_rules:
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
        if name == "score":
            p.add_argument("--gate")
            p.add_argument("--tolerance", type=float, default=0.0)
            p.add_argument("--json")
        else:
            p.add_argument("--output", required=True)
    sub.add_parser("selftest")
    args = parser.parse_args(argv)
    if args.cmd == "selftest":
        return _selftest()
    try:
        goldens = load_goldens(args.goldens)
        profile = load_profile(args.profile) if args.profile else DEFAULT_PROFILE
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
