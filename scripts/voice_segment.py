#!/usr/bin/env python3
"""voice_segment.py - turn a Markdown draft into prose segments with line numbers.

Stdlib only. Never prints. Reuses the sentence splitter from stylometry.py so the
checker and the corpus analyzer agree on what a sentence is.
"""
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stylometry import split_sentences  # noqa: E402

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABLE = re.compile(r"^\s*\|")
RULE = re.compile(r"^\s*(?:[-*_]\s*){3,}$")
INLINE_CODE = re.compile(r"`[^`\n]+`")
LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
HTML = re.compile(r"<[^>]+>")
EMPHASIS = re.compile(r"(\*{1,3}|_{1,3})(\S.*?\S|\S)\1")

PROSE_KINDS = ("prose", "bullet")


@dataclass(frozen=True)
class Segment:
    line: int
    kind: str
    text: str
    heading: str = ""


def normalize_inline(line: str) -> str:
    """Remove inline markup while keeping the prose and the punctuation that rules inspect."""
    line = IMAGE.sub(" ", line)
    line = INLINE_CODE.sub("code", line)
    line = LINK.sub(r"\1", line)
    line = HTML.sub(" ", line)
    line = EMPHASIS.sub(r"\2", line)
    line = line.replace("’", "'").replace("‘", "'")
    return re.sub(r"[ \t]+", " ", line).strip()


def segment(text: str) -> list:
    """Return Segment objects covering every line of the draft, in order."""
    lines = text.split("\n")
    segs = []
    start = 0
    if lines and lines[0].strip() == "---":
        end = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), None)
        if end is not None:
            for k in range(0, end + 1):
                segs.append(Segment(k + 1, "code", lines[k]))
            start = end + 1
    para, para_start, in_code = [], None, False
    current_heading = ""

    def flush():
        nonlocal para, para_start
        if para:
            segs.append(Segment(para_start, "prose", " ".join(para), current_heading))
        para, para_start = [], None

    for idx in range(start, len(lines)):
        raw = lines[idx]
        n = idx + 1
        if FENCE.match(raw):
            flush()
            in_code = not in_code
            segs.append(Segment(n, "code", raw))
            continue
        if in_code:
            segs.append(Segment(n, "code", raw))
            continue
        if not raw.strip():
            flush()
            segs.append(Segment(n, "blank", ""))
            continue
        if HEADING.match(raw):
            flush()
            current_heading = normalize_inline(HEADING.sub("", raw))
            segs.append(Segment(n, "heading", current_heading, current_heading))
            continue
        if TABLE.match(raw) or RULE.match(raw):
            flush()
            segs.append(Segment(n, "table", raw))
            continue
        if BULLET.match(raw):
            flush()
            segs.append(Segment(n, "bullet", normalize_inline(BULLET.sub("", raw)), current_heading))
            continue
        if not para:
            para_start = n
        para.append(normalize_inline(raw))
    flush()
    return segs


def sentences_of(text: str) -> list:
    """Sentence list for one segment, using the shared stylometry splitter."""
    return split_sentences(text)


def prose_text(segs: list) -> str:
    """All prose and bullet text joined with blank lines, for whole-draft metrics."""
    return "\n\n".join(s.text for s in segs if s.kind in PROSE_KINDS)
