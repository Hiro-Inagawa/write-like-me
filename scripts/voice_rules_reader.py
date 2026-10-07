#!/usr/bin/env python3
"""voice_rules_reader.py - reader-text checks added in v3.

Same contract as voice_rules.py. Rules in READER_RULES take (segs, profile, reg).
Rules in CONTEXT_RULES also take a context dict with the optional keys
'explanation' (text of the approved explanation) and 'rejected' (list of phrases).
Stdlib only. Never reads files and never prints.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stylometry import tokenize_words  # noqa: E402
from voice_rules import BLOCK, REVIEW, Hit, _excerpt, _in_quotes  # noqa: E402
from voice_segment import PROSE_KINDS, prose_text, sentences_of  # noqa: E402

PARAGRAPH_OPENERS = ("however", "but note")
LEAD_JUNK = re.compile(r"^[\s\"'(“*_]+")

BENEFIT_COMMA = re.compile(
    r",\s*(?:so you can|so that you|which lets you|which means you|helping you|allowing you|ensuring)\b[^.!?]*[.!?]?\s*$",
    re.IGNORECASE)
BENEFIT_PLAIN = re.compile(r"\s(?:so you can|so that you)\b[^.!?]*[.!?]?\s*$", re.IGNORECASE)

ABSTRACT_NOUNS = {"quality", "clarity", "confidence", "growth", "impact", "power", "simplicity", "speed",
                  "success", "value", "excellence", "innovation", "trust", "freedom", "control", "results"}
FINITE_SIGNALS = {"is", "are", "was", "were", "be", "been", "am", "has", "have", "had", "do", "does", "did",
                  "will", "would", "can", "could", "shall", "should", "may", "might", "must", "not",
                  "i", "you", "he", "she", "it", "we", "they"}
TAGLINE_MAX_WORDS = 8
TAGLINE_STOP = {"and", "or", "for", "of", "with", "the", "a", "an", "every", "your", "our", "more", "less", "in",
                "on", "to", "from", "by", "without", "at", "into", "all", "each", "no", "any", "as", "than"}

NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
CAPITAL = re.compile(r"[A-Z][A-Za-z0-9]*")


def _abstract(word):
    w = word.lower()
    if w in ABSTRACT_NOUNS:
        return True
    if w.endswith("ies") and w[:-3] + "y" in ABSTRACT_NOUNS:
        return True
    return w.endswith("s") and w[:-1] in ABSTRACT_NOUNS


def _starts_with(text, phrase):
    if not text.startswith(phrase):
        return False
    tail = text[len(phrase):len(phrase) + 1]
    return not tail.isalpha()


def rule_closing_caveat(segs, profile, reg):
    level = reg.get("closing_caveat", REVIEW)
    if level == "off":
        return []
    prose = [s for s in segs if s.kind == "prose"]
    if not prose:
        return []
    phrases = [p.lower() for p in profile.get("bans", {}).get("caveat_phrases", [])]
    flat = [(s.line, sent) for s in prose for sent in sentences_of(s.text)]
    candidates = [(line, sent, False) for line, sent in flat[-2:]]
    if len(prose) >= 2:
        first = sentences_of(prose[-1].text)
        if first:
            candidates.append((prose[-1].line, first[0], True))
    hits, seen = [], set()
    for line, sent, opens_paragraph in candidates:
        norm = LEAD_JUNK.sub("", sent).lower()
        found = next((p for p in phrases if _starts_with(norm, p)), None)
        if found is None and opens_paragraph:
            found = next((o for o in PARAGRAPH_OPENERS if _starts_with(norm, o)), None)
        if found and (line, sent) not in seen:
            seen.add((line, sent))
            hits.append(Hit("CLOSING_CAVEAT", level, line, _excerpt(sent, 0, 70),
                            "Closing caveat opens with '%s'. If it changes the decision, lead with it. Otherwise delete it." % found))
    return hits


def rule_benefit_tail(segs, profile, reg):
    level = reg.get("benefit_tail", REVIEW)
    if level == "off":
        return []
    hits = []
    for seg in segs:
        if seg.kind not in PROSE_KINDS:
            continue
        for sent in sentences_of(seg.text):
            m = BENEFIT_COMMA.search(sent) or BENEFIT_PLAIN.search(sent)
            if m and not _in_quotes(sent, m.start()):
                hits.append(Hit("BENEFIT_TAIL", level, seg.line, _excerpt(sent, m.start(), 60),
                                "Benefit tail at the end of the sentence. State what the thing does and stop."))
    return hits


def _is_tagline(text):
    if any(c.isdigit() for c in text) or text.rstrip().endswith(("?", ":")) or '"' in text:
        return False
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    if not 2 <= len(words) <= TAGLINE_MAX_WORDS or len(re.findall(r"\S+", text)) > TAGLINE_MAX_WORDS:
        return False
    lowered = [w.lower() for w in words]
    if not any(_abstract(w) for w in lowered):
        return False
    if any(w in FINITE_SIGNALS for w in lowered):
        return False
    for w in lowered:
        if len(w) > 3 and w.endswith(("s", "ed")) and not _abstract(w) and not w.endswith(("ss", "us", "ous", "ics")):
            return False
    content = [w for w in lowered if w not in TAGLINE_STOP]
    return sum(1 for w in content if _abstract(w)) * 2 >= len(content)


def rule_tagline(segs, profile, reg):
    level = reg.get("tagline", REVIEW)
    if level == "off":
        return []
    return [Hit("TAGLINE", level, s.line, _excerpt(s.text, 0, 60),
                "Short line of abstract nouns with no verb. Write a sentence that says what the thing does.")
            for s in segs if s.kind == "prose" and _is_tagline(s.text)]


def rule_length_band(segs, profile, reg):
    band = reg.get("length")
    if not band:
        return []
    lo, hi = band.get("min"), band.get("max")
    count = len(tokenize_words(prose_text(segs)))
    level = BLOCK if (lo is not None and hi is not None) else REVIEW
    first = next((s.line for s in segs if s.kind in PROSE_KINDS), 1)
    if lo is not None and count < lo:
        return [Hit("LENGTH_BAND", level, first, "%d words" % count,
                    "Draft has %d words. The band for this register starts at %d." % (count, lo))]
    if hi is not None and count > hi:
        return [Hit("LENGTH_BAND", level, first, "%d words" % count,
                    "Draft has %d words. The band for this register ends at %d." % (count, hi))]
    return []


def _numbers(text):
    """Set of (value, is_percent) pairs found in text."""
    found = set()
    for m in NUMBER.finditer(text):
        tail = text[m.end():m.end() + 9].lower()
        pct = tail.startswith("%") or tail.startswith(" percent") or tail.startswith(" per cent")
        found.add((m.group(0).replace(",", "").rstrip("."), pct))
    return found


def rule_additions(segs, profile, reg, ctx):
    explanation = (ctx or {}).get("explanation")
    level = reg.get("additions", REVIEW)
    if explanation is None or level == "off":
        return []
    known_words = {w.lower() for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", explanation)}
    known_numbers = _numbers(explanation)
    known_plain = {v for v, _ in known_numbers}
    hits, seen = [], set()

    def add(item, kind, line, sent):
        if item.lower() in seen:
            return
        seen.add(item.lower())
        hits.append(Hit("ADDITION", level, line, _excerpt(sent, max(sent.find(item), 0), 50),
                        "%s '%s' is not in the explanation. Add it to the explanation first or remove it." % (kind, item)))

    for seg in segs:
        if seg.kind not in PROSE_KINDS:
            continue
        for sent in sentences_of(seg.text):
            for value, pct in _numbers(sent):
                ok = (value, pct) in known_numbers if pct else value in known_plain
                if not ok:
                    add(value + ("%" if pct else ""), "Number", seg.line, sent)
            for m in CAPITAL.finditer(sent):
                if m.start() == 0 or m.group(0) == "I":
                    continue
                before = sent[:m.start()].rstrip()
                if before.endswith(("(", '"', "'")) and len(before) <= 1:
                    continue
                if m.group(0).lower() not in known_words:
                    add(m.group(0), "Name", seg.line, sent)
    return hits


def _normalize(text):
    return re.sub(r"\s+", " ", text.replace("’", "'").replace("‘", "'")).strip().lower()


def rule_repeated_phrase(segs, profile, reg, ctx):
    phrases = [_normalize(p) for p in (ctx or {}).get("rejected") or [] if p.strip()]
    if not phrases:
        return []
    hits = []
    for seg in segs:
        if seg.kind in ("code", "blank", "table"):
            continue
        norm = _normalize(seg.text)
        for phrase in phrases:
            m = re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", norm)
            if m:
                hits.append(Hit("REPEATED_PHRASE", BLOCK, seg.line, _excerpt(norm, m.start(), 60),
                                "The phrase '%s' was rejected earlier. Do not bring it back, not even reworded." % phrase))
    return hits


READER_RULES = (rule_closing_caveat, rule_benefit_tail, rule_tagline, rule_length_band)
CONTEXT_RULES = (rule_additions, rule_repeated_phrase)
