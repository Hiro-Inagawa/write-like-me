#!/usr/bin/env python3
"""
extract_author_turns.py - Extract author-only content from conversation exports.

Usage:
    python extract_author_turns.py <input> [options]

Options:
    --format FORMAT      Export format: markdown (default), claude, chatgpt
                         - markdown: .md files split on heading markers
                         - claude:   Claude.ai conversations.json export
                         - chatgpt:  ChatGPT conversations.json export
    --marker TEXT        Heading that marks the author's turns (markdown format only).
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
    - Lines that look like AI responses that leaked through

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

# AI-tell phrases — lines likely to be leaked assistant content
CLAUDE_TELLS = [
    "as an ai", "as a language model", "i'm an ai", "i am an ai",
    "i don't have personal", "i cannot have opinions",
    "claude here", "i'm claude",
    "i'll help you", "i'd be happy to", "let me know if you",
    "certainly!", "certainly,",
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
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def contains_claude_tell(text: str) -> bool:
    text_lower = text.lower()
    return any(tell in text_lower for tell in CLAUDE_TELLS)


def _make_stats(file_name: str, raw_bytes: int, combined: str, warn_threshold: float) -> dict:
    extracted_bytes = len(combined.encode("utf-8"))
    yield_fraction = extracted_bytes / max(raw_bytes, 1)
    return {
        "file": file_name,
        "raw_bytes": raw_bytes,
        "extracted_bytes": extracted_bytes,
        "turns_extracted": len([p for p in combined.split("\n\n") if p.strip()]),
        "yield_fraction": round(yield_fraction, 3),
        "low_yield": yield_fraction < warn_threshold,
    }


# --- Markdown extraction ---

def extract_turns_from_file(
    path: Path,
    author_marker: str,
    warn_threshold: float = 0.05,
) -> tuple:
    """Extract author-only turns from one markdown file."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw_len = len(raw)
    marker_clean = author_marker.strip().lower()

    section_pattern = re.compile(r'^(#+\s+.+)$', re.MULTILINE)
    parts = section_pattern.split(raw)

    turns = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if section_pattern.match(part):
            heading = part.strip()
            if heading.lower().startswith(marker_clean) or heading.lower() == marker_clean:
                if i + 1 < len(parts):
                    body = parts[i + 1]
                    cleaned = clean_turn(body)
                    if cleaned and len(cleaned) > 20:
                        if not contains_claude_tell(cleaned):
                            turns.append(cleaned)
                i += 2
                continue
        i += 1

    combined = "\n\n".join(turns)
    stats = _make_stats(path.name, raw_len, combined, warn_threshold)
    return combined, stats


def load_corpus_markdown(
    input_dir: Path,
    author_marker: str = "## Hiro",
    min_file_bytes: int = 500,
    include_duplicates: bool = False,
    warn_threshold: float = 0.05,
) -> tuple:
    """Process all markdown files in a directory."""
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


# --- Claude.ai JSON extraction ---

def extract_from_claude_json(json_path: Path, warn_threshold: float = 0.05) -> tuple:
    """Extract human turns from a Claude.ai conversations.json export."""
    raw_bytes = json_path.stat().st_size
    data = json.loads(json_path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(data, list):
        data = [data]

    turns = []
    for conv in data:
        for msg in conv.get("chat_messages", []):
            if msg.get("sender") != "human":
                continue
            text = msg.get("text", "").strip()
            if not text or len(text) <= 20:
                continue
            cleaned = clean_turn(text)
            if cleaned and not contains_claude_tell(cleaned):
                turns.append(cleaned)

    combined = "\n\n".join(turns)
    stats = _make_stats(json_path.name, raw_bytes, combined, warn_threshold)
    return combined, stats


# --- ChatGPT JSON extraction ---

def extract_from_chatgpt_json(json_path: Path, warn_threshold: float = 0.05) -> tuple:
    """Extract user turns from a ChatGPT conversations.json export."""
    raw_bytes = json_path.stat().st_size
    data = json.loads(json_path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(data, list):
        data = [data]

    turns = []
    for conv in data:
        for node in conv.get("mapping", {}).values():
            msg = node.get("message")
            if not msg:
                continue
            if msg.get("author", {}).get("role") != "user":
                continue
            parts = msg.get("content", {}).get("parts", [])
            text = " ".join(str(p) for p in parts if isinstance(p, str)).strip()
            if not text or len(text) <= 20:
                continue
            cleaned = clean_turn(text)
            if cleaned and not contains_claude_tell(cleaned):
                turns.append(cleaned)

    combined = "\n\n".join(turns)
    stats = _make_stats(json_path.name, raw_bytes, combined, warn_threshold)
    return combined, stats


def load_corpus_json(
    input_path: Path,
    fmt: str,
    warn_threshold: float = 0.05,
) -> tuple:
    """Process Claude.ai or ChatGPT JSON conversation exports."""
    extractor = extract_from_claude_json if fmt == "claude" else extract_from_chatgpt_json

    if input_path.is_file() and input_path.suffix == ".json":
        json_files = [input_path]
    elif input_path.is_dir():
        conv_json = input_path / "conversations.json"
        json_files = [conv_json] if conv_json.exists() else sorted(input_path.rglob("*.json"))
    else:
        return "", [], [f"Error: {input_path} is not a JSON file or directory."]

    all_turns = []
    per_file_stats = []
    warnings = []

    for path in json_files:
        try:
            extracted, stats = extractor(path, warn_threshold)
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


# --- Shared utilities ---

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
    print(f"\n{'='*60}\n")


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
    parser.add_argument("input", help="Directory or file containing conversation exports")
    parser.add_argument("--format", choices=["markdown", "claude", "chatgpt"], default="markdown",
                        help="Export format: markdown (default), claude (Claude.ai JSON), chatgpt (ChatGPT JSON)")
    parser.add_argument("--marker", default="## Hiro",
                        help="Heading that marks the author's turns (markdown format only, default: '## Hiro')")
    parser.add_argument("--output", help="Write extracted text to this file (default: stdout)")
    parser.add_argument("--preview", type=int, default=0,
                        help="Show N random samples and exit (0 = disabled)")
    parser.add_argument("--min-file-bytes", type=int, default=500)
    parser.add_argument("--no-dedup", action="store_true",
                        help="Include duplicate files (_2.md, _3.md suffixes)")
    parser.add_argument("--warn-threshold", type=float, default=0.05)
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.format in ("claude", "chatgpt"):
        all_text, stats_list, warnings = load_corpus_json(
            input_path,
            fmt=args.format,
            warn_threshold=args.warn_threshold,
        )
    else:
        if not input_path.is_dir():
            print(f"Error: {input_path} is not a directory (required for markdown format).", file=sys.stderr)
            sys.exit(1)
        all_text, stats_list, warnings = load_corpus_markdown(
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
        print("Error: no content extracted. Check --format and --marker settings.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(all_text, encoding="utf-8")
        print(f"Extracted text written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(all_text.encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
