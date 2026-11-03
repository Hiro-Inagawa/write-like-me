#!/usr/bin/env python3
"""corpus_conflicts.py - find where the author's own writing breaks the universal baseline.

Usage:
    python corpus_conflicts.py <corpus file or folder> [--examples N] [--json]

Runs the universal baseline (no voice profile) over every .md and .txt file of the corpus and lists each
rule that returns a block hit, with a count, the number of files, and a few examples. Files this skill
wrote (_STYLE-PROFILE-*.md and anything under a voices/ folder) are skipped.

Each listed rule is a conflict for the author to decide before the voice is emitted. Either the author
keeps the habit and the rule goes into the profile as an override (rule_overrides), or the author drops
the habit and the rule stays. The script never decides.

The last stdout line is VOICE_CONFLICTS_FOUND or VOICE_CONFLICTS_NONE. Exit 0 in both cases, 2 on bad input.
Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stylometry import is_generated_artifact  # noqa: E402
from voice_check import check_text  # noqa: E402
from voice_lang import detect_language  # noqa: E402
from voice_profile import default_profile  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def corpus_files(path: Path) -> list:
    if path.is_file():
        return [path]
    files = sorted(path.rglob("*.md")) + sorted(path.rglob("*.txt"))
    return [f for f in files if not is_generated_artifact(f, path)]


def find_conflicts(path: Path, examples: int = 3, language: str = None) -> list:
    """Return one entry per rule that blocks somewhere in the corpus, most frequent first.
    Without a language it is detected from the whole corpus."""
    found = {}
    texts = [(f, f.read_text(encoding="utf-8", errors="replace")) for f in corpus_files(path)]
    profile = default_profile(language or detect_language("\n".join(t for _, t in texts)))
    for file, text in texts:
        result = check_text(text, profile, profile["default_register"], str(file))
        for hit in result["hits"]:
            if hit["severity"] != "block":
                continue
            entry = found.setdefault(hit["rule"], {"rule": hit["rule"], "count": 0, "files": set(),
                                                   "message": hit["message"], "examples": []})
            entry["count"] += 1
            entry["files"].add(str(file))
            if len(entry["examples"]) < examples:
                entry["examples"].append({"file": str(file), "line": hit["line"], "excerpt": hit["excerpt"]})
    rows = []
    for entry in found.values():
        rows.append({**entry, "files": len(entry["files"])})
    return sorted(rows, key=lambda r: (-r["count"], r["rule"]))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("corpus", help="A corpus file or folder")
    parser.add_argument("--examples", type=int, default=3, help="Examples to print per rule (default 3)")
    parser.add_argument("--json", action="store_true", help="Print the conflicts as JSON")
    parser.add_argument("--language", choices=("en", "de"), help="Language of the corpus (default: detected)")
    args = parser.parse_args(argv)
    path = Path(args.corpus)
    if not path.exists():
        print("ERROR: %s does not exist" % path)
        return 2
    rows = find_conflicts(path, args.examples, args.language)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            print("CONFLICT %-24s %d hits in %d files. %s" % (row["rule"], row["count"], row["files"], row["message"]))
            for ex in row["examples"]:
                print("    %s:%d  %s" % (ex["file"], ex["line"], ex["excerpt"]))
        if rows:
            print("The author decides each conflict: keep the rule, or set it to off or review in rule_overrides.")
    print("VOICE_CONFLICTS_FOUND" if rows else "VOICE_CONFLICTS_NONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
