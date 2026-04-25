#!/usr/bin/env python3
"""
extract_author_turns.py - Extract author-only content from conversation exports.

Usage:
    python extract_author_turns.py <input_dir> [options]

Options:
    --marker TEXT        The heading that marks the author's turns.
                         Default: "## Hiro"
                         Examples: "## User", "**You:**", "### Human"
    --output PATH        Write extracted text to this file (default: stdout)
    --preview N          Show N random extracted samples and exit (default: 5)
    --min-file-bytes N   Skip files smaller than N bytes (default: 500)
    --no-dedup           Include duplicate files (_2.md, _3.md suffixes)
    --warn-threshold F   Warn if extraction yield < F fraction of source (default: 0.05)

The script strips from extracted turns:
    - Code fences
    - Inline code
    - Frontmatter
    - Markdown image tags
    - Component markers
    - Citation inline markers
    - HTML tags
    - Lines that look like Claude responses that leaked through

Output is plain prose text, suitable for stylometry.py input.
"""

import sys
import re
import os
import json
import random
import argparse
import collections
from pathlib import Path

# Patterns to strip from extracted turns
_RE_CODE_FENCE    = re.compile(r'```.*?```', re.DOTALL)
_RE_INLINE_CODE   = re.compile(r'`[^`\n]+`')
_RE_FRONTMATTER   = re.compile(r'^\s*---.*?---\s*', re.DOTALL)
_RE_COMPONENT_TAG = re.compile(r'\[.*?—.*?\]')
_RE_CITATION      = re.compile(r'\\\[\d+\\\]|\[(\d+)\]')
_RE_IMAGE         = re.compile(r'!\[.*?\]\(.*?\)')
_RE_HTML          = re.compile(r'<[^>]+>')
_RE_DEVICE_NOTE   = re.compile(r'This block is not supported on your current device yet\.?', re.IGNORECASE)
_RE_TRAILING_WS   = re.compile(r'[ \t]+$', re.MULTILINE)

# Claude-tell phrases — lines likely to be leaked assistant content
CLAUDE_TELLS = [
    "as an ai", "as a language model", "i'm an ai", "i am an ai",
    "i don't have personal", "i cannot have opinions",
    "claude here", "i'm claude",
]


def is_dedup_file(path: Path) -> bool:
    """Return True if filename ends with _2.md, _3.md, etc. (byte-identical duplicates)."""
    stem = path.stem
    return bool(re.search(r'_\d+$', stem))


def clean_turn(text: str) -> str:
    """Strip non-prose markers from a single author turn."""
    text = _RE_FRONTMATTER.sub('', text)
    text = _RE_CODE_FENCE.sub('', text)
    text = _RE_INLINE_CODE.sub('', text)
    text = _RE_COMPONENT_TAG.sub('', text)
    text = _RE_CITATION.sub('', text)
    text = _RE_IMAGE.sub('', text)
    text = _RE_HTML.sub('', text)
    text = _RE_DEVICE_NOTE.sub('', text)
    text = _RE_TRAILING_WS.sub('', text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def contains_claude_tell(text: str) -> bool:
    text_lower = text.lower()
    return any(tell in text_lower for tell in CLAUDE_TELLS)


def extract_turns_from_file(
    path: Path,
    author_marker: str,
    warn_threshold: float = 0.05,
) -> tuple:
    """
    Extract author-only turns from one markdown file.

    Returns:
        (extracted_text: str, stats: dict)
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw_len = len(raw)

    # Build a header pattern: match the exact marker line
    # We split on any '## ...' heading and check if it matches the author marker
    # Handle both '## Hiro' style (exact) and partial-match patterns
    marker_clean = author_marker.strip().lower()

    # Split file into sections on any ## heading
    section_pattern = re.compile(r'^(#+\s+.+)$', re.MULTILINE)
    parts = section_pattern.split(raw)
    # parts = [text_before_first_heading, heading1, text1, heading2, text2, ...]

    turns = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if section_pattern.match(part):
            # This is a heading
            heading = part.strip()
            if heading.lower().startswith(marker_clean) or heading.lower() == marker_clean:
                # Next part is the body of this author turn
                if i + 1 < len(parts):
                    body = parts[i + 1]
                    cleaned = clean_turn(body)
                    if cleaned and len(cleaned) > 20:
                        if not contains_claude_tell(cleaned):
                            turns.append(cleaned)
                        else:
                            pass  # silently skip likely leaked assistant content
                i += 2
                continue
        i += 1

    combined = "\n\n".join(turns)
    extracted_len = len(combined)
    yield_fraction = extracted_len / max(raw_len, 1)

    stats = {
        "file": str(path.name),
        "raw_bytes": raw_len,
        "extracted_bytes": extracted_len,
        "turns_extracted": len(turns),
        "yield_fraction": round(yield_fraction, 3),
        "low_yield": yield_fraction < warn_threshold,
    }

    return combined, stats


def load_corpus(
    input_dir: Path,
    author_marker: str = "## Hiro",
    min_file_bytes: int = 500,
    include_duplicates: bool = False,
    warn_threshold: float = 0.05,
) -> tuple:
    """
    Process all markdown files in a directory.

    Returns:
        (all_text: str, per_file_stats: list, warnings: list)
    """
    md_files = sorted(input_dir.rglob("*.md"))

    all_turns = []
    per_file_stats = []
    warnings = []

    for path in md_files:
        if path.stat().st_size < min_file_bytes:
            continue
        if not include_duplicates and is_dedup_file(path):
            continue

        try:
            extracted, stats = extract_turns_from_file(path, author_marker, warn_threshold)
        except Exception as e:
            warnings.append(f"Error reading {path.name}: {e}")
            continue

        per_file_stats.append(stats)

        if stats["low_yield"] and stats["raw_bytes"] > 5000:
            warnings.append(
                f"Low extraction yield in {path.name}: "
                f"{stats['yield_fraction']*100:.1f}% "
                f"({stats['turns_extracted']} turns extracted)"
            )

        if extracted:
            all_turns.append(extracted)

    return "\n\n".join(all_turns), per_file_stats, warnings


def show_preview(all_text: str, n: int = 5) -> None:
    """Print N random paragraph-length samples from extracted text."""
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', all_text) if len(p.strip()) > 100]
    if not paragraphs:
        print("No substantive paragraphs found in extracted content.")
        return

    sample = random.sample(paragraphs, min(n, len(paragraphs)))
    print(f"\n{'='*60}")
    print(f"EXTRACTED AUTHOR CONTENT — {n} RANDOM SAMPLES")
    print(f"{'='*60}")
    for i, para in enumerate(sample, 1):
        print(f"\n[Sample {i}]\n{para[:500]}{'...' if len(para) > 500 else ''}")
    print(f"\n{'='*60}")
    print("Do these look like the author's own prose? (y/n)")


def print_stats_summary(stats_list: list, warnings: list) -> None:
    total_files = len(stats_list)
    total_bytes = sum(s["raw_bytes"] for s in stats_list)
    extracted_bytes = sum(s["extracted_bytes"] for s in stats_list)
    total_turns = sum(s["turns_extracted"] for s in stats_list)
    low_yield_files = sum(1 for s in stats_list if s["low_yield"])

    print(f"\nExtraction summary:", file=sys.stderr)
    print(f"  Files processed:   {total_files}", file=sys.stderr)
    print(f"  Source bytes:      {total_bytes:,}", file=sys.stderr)
    print(f"  Extracted bytes:   {extracted_bytes:,}", file=sys.stderr)
    print(f"  Overall yield:     {extracted_bytes/max(total_bytes,1)*100:.1f}%", file=sys.stderr)
    print(f"  Total turns:       {total_turns:,}", file=sys.stderr)
    if low_yield_files:
        print(f"  Low-yield files:   {low_yield_files} (check --marker setting)", file=sys.stderr)

    for w in warnings[:10]:
        print(f"  WARNING: {w}", file=sys.stderr)
    if len(warnings) > 10:
        print(f"  ... and {len(warnings)-10} more warnings.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Extract author-only turns from conversation export files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="Directory containing conversation export .md files")
    parser.add_argument("--marker", default="## Hiro",
                        help="Heading that marks the author's turns (default: '## Hiro')")
    parser.add_argument("--output", help="Write extracted text to this file (default: stdout)")
    parser.add_argument("--preview", type=int, default=0,
                        help="Show N random samples and exit (0 = disabled)")
    parser.add_argument("--min-file-bytes", type=int, default=500)
    parser.add_argument("--no-dedup", action="store_true",
                        help="Include duplicate files (_2.md, _3.md suffixes)")
    parser.add_argument("--warn-threshold", type=float, default=0.05)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_dir():
        print(f"Error: {input_path} is not a directory.", file=sys.stderr)
        sys.exit(1)

    all_text, stats_list, warnings = load_corpus(
        input_path,
        author_marker=args.marker,
        min_file_bytes=args.min_file_bytes,
        include_duplicates=args.no_dedup,
        warn_threshold=args.warn_threshold,
    )

    print_stats_summary(stats_list, warnings)

    if args.preview > 0:
        show_preview(all_text, args.preview)
        return

    if not all_text.strip():
        print("Error: no content extracted. Check --marker setting.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(all_text, encoding="utf-8")
        print(f"Extracted text written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(all_text.encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
