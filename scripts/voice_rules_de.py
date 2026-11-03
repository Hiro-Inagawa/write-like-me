#!/usr/bin/env python3
"""voice_rules_de.py - checks that only exist in German.

Same contract as voice_rules.py: (segments, profile, register) -> list[Hit]. They run only for a
profile with "language": "de". Standard German (Hochdeutsch) only. The research behind each rule is
in __RESEARCH/2026-11-02-GERMAN-AI-WRITING-PATTERNS.md next to the skill. Stdlib only.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lang as L  # noqa: E402
from voice_rules import BLOCK, REVIEW, Hit, _excerpt, _in_quotes, _phrase_hits  # noqa: E402
from voice_segment import PROSE_KINDS, sentences_of  # noqa: E402

INLINE_CODE = re.compile(r"`[^`\n]*`")
URL = re.compile(r"https?://\S+")
# Straight double quotes, the English closing mark, or an English opening mark at the start of a word
ENGLISH_QUOTE = re.compile(r'"|”|(?:(?<=^)|(?<=[\s(\[]))“(?=\S)')
SPACED_DASH = re.compile(r"(?<=\S) [–-] (?=\S)")
UNIT_NO_SPACE = re.compile(r"\d(?:%|€|\$|Euro\b|Prozent\b|km\b|kg\b|cm\b|mm\b)")
ABBREV_NO_SPACE = re.compile(r"\b(?:z\.B|d\.h|u\.a|o\.ä|u\.U|s\.o|s\.u|v\.a)\.")
ENGLISH_DECIMAL = re.compile(r"(?<![\d.,])\d+\.\d{1,2}(?![\d.])(?! Uhr)")
ENGLISH_DATE = re.compile(r"\b(?:%s) \d{1,2}, \d{4}\b" % L.MONTHS)
IN_YEAR = re.compile(r"\bin (?:19|20)\d\d\b", re.IGNORECASE)
REALIZE = re.compile(r"\brealisier\w*,? dass\b", re.IGNORECASE)
AI_TOKEN = re.compile(r"(?<![\w-])AI(?![\w-])")
PARTICIPLE_TAIL = re.compile(r",\s+(?:[^,.;:!?]*\s)?(%s)\s*[.!?]?\s*$" % "|".join(L.DE_PARTICIPLE_TAILS), re.IGNORECASE)
ASCII_UMLAUT = re.compile(r"\b(?:%s)\b" % "|".join(L.DE_ASCII_UMLAUT_WORDS), re.IGNORECASE)
SS_SPELLING = re.compile(r"\b(?:%s)\b" % "|".join(L.DE_SS_WORDS), re.IGNORECASE)
DU_FORMS = re.compile(r"\b(?:du|dich|dir|dein|deine|deinen|deinem|deiner|deines)\b", re.IGNORECASE)
# Formal address: "Ihnen" anywhere, and a capitalized Sie or Ihr form after a lowercase word or a comma
SIE_FORMS = re.compile(r"\bIhnen\b|(?<=[a-zäöüß,] )(?:Sie|Ihr|Ihre|Ihren|Ihrem|Ihrer|Ihres)\b")
DE_CONNECTIVE_WORDS = 150
GENDER_FORM = re.compile(r"\b([A-ZÄÖÜ][a-zäöüß]+)(?:(\*|:|_|/-?)(?:innen|in)|(I)(?:nnen|n)|(\(inn\))en)\b")


def _prose(segs, kinds=PROSE_KINDS):
    for seg in segs:
        if seg.kind in kinds:
            yield seg, URL.sub(" ", INLINE_CODE.sub(" ", seg.text))


def rule_de_quotes(segs, profile, reg):
    hits = []
    for seg, text in _prose(segs, PROSE_KINDS + ("heading",)):
        for m in ENGLISH_QUOTE.finditer(text):
            hits.append(Hit("DE_QUOTES", BLOCK, seg.line, _excerpt(text, m.start()),
                            "English quotation mark. German uses „ … “."))
    return hits


def rule_de_en_dash(segs, profile, reg):
    level = reg.get("en_dash", REVIEW)
    if level == "off":
        return []
    hits = []
    for seg, text in _prose(segs):
        for m in SPACED_DASH.finditer(text):
            hits.append(Hit("DE_DASH", level, seg.line, _excerpt(text, m.start()),
                            "Gedankenstrich. Use a comma or a period unless the sentence needs the dash."))
    return hits


def rule_de_number_format(segs, profile, reg):
    checks = ((UNIT_NO_SPACE, "Number and unit need a space, as in 10 € or 50 %."),
              (ABBREV_NO_SPACE, "German abbreviations take a space, as in z. B. and d. h."),
              (ENGLISH_DECIMAL, "English decimal point. German writes 3,5."),
              (ENGLISH_DATE, "English date. German writes 2. November 2026."))
    hits = []
    for seg, text in _prose(segs, PROSE_KINDS + ("heading",)):
        for pattern, message in checks:
            for m in pattern.finditer(text):
                hits.append(Hit("DE_NUMBER_FORMAT", REVIEW, seg.line, _excerpt(text, m.start()), message))
    return hits


def rule_de_heading_case(segs, profile, reg):
    hits = []
    for seg in segs:
        if seg.kind != "heading":
            continue
        words = seg.text.lstrip("# ").split()
        for i, word in enumerate(words[1:], 1):
            if words[i - 1].endswith(":"):
                continue
            if word.strip(",.!?") in L.DE_HEADING_FUNCTION_WORDS:
                hits.append(Hit("DE_HEADING_CASE", REVIEW, seg.line, _excerpt(seg.text, 0, 60),
                                "English title case in a heading. In German only nouns and the first word are capitalized."))
                break
    return hits


def rule_de_calque(segs, profile, reg):
    hits = _phrase_hits(segs, L.DE_CALQUES, "DE_CALQUE", REVIEW, "Translated from English: '%s'. Write it the German way.")
    for seg, text in _prose(segs):
        for pattern, message in ((IN_YEAR, "'in' before a year is English. Write the year alone or 'im Jahr'."),
                                 (REALIZE, "'realisieren, dass' is English 'realize'. Write 'merken' or 'erkennen'."),
                                 (AI_TOKEN, "'AI' in German text. Write 'KI'.")):
            for m in pattern.finditer(text):
                if not _in_quotes(text, m.start()):
                    hits.append(Hit("DE_CALQUE", REVIEW, seg.line, _excerpt(text, m.start()), message))
    return hits


def rule_de_participle_tail(segs, profile, reg):
    hits = []
    for seg, text in _prose(segs):
        for sent in sentences_of(text):
            m = PARTICIPLE_TAIL.search(sent)
            if m:
                hits.append(Hit("DE_PARTICIPLE_TAIL", REVIEW, seg.line, _excerpt(sent, m.start(), 60),
                                "Participle tail '%s' copies the English -ing comment. Say it in its own sentence or cut it." % m.group(1)))
    return hits


def _first_unquoted(pattern, text):
    return next((m for m in pattern.finditer(text) if not _in_quotes(text, m.start())), None)


def rule_de_address_mix(segs, profile, reg):
    du, sie = None, None
    for seg, text in _prose(segs):
        du = du or ((seg.line, text, m) if (m := _first_unquoted(DU_FORMS, text)) else None)
        sie = sie or ((seg.line, text, m) if (m := _first_unquoted(SIE_FORMS, text)) else None)
    if not (du and sie):
        return []
    line, text, m = max(du, sie, key=lambda x: x[0])
    return [Hit("DE_ADDRESS_MIX", BLOCK, line, _excerpt(text, m.start()),
                "The text addresses the reader as both du and Sie. Use one form throughout.")]


def rule_de_gender_forms(segs, profile, reg):
    policy = reg.get("gender_characters", "allowed")
    if policy == "off":
        return []
    found, words = [], set()
    for seg, text in _prose(segs, PROSE_KINDS + ("heading",)):
        words.update(w.lower() for w in re.findall(r"[^\W\d_]+", GENDER_FORM.sub(" ", text)))
        found.extend((seg.line, text, m) for m in GENDER_FORM.finditer(text))
    if not found:
        return []
    if policy in ("forbidden", "review"):
        severity = BLOCK if policy == "forbidden" else REVIEW
        return [Hit("DE_GENDER_FORM", severity, line, _excerpt(text, m.start()),
                    "Gender form '%s'. This voice does not use gender characters." % m.group(0))
                for line, text, m in found]
    marks = {m.group(2) or m.group(3) or m.group(4) for _, _, m in found}
    stems = {m.group(1).lower() for _, _, m in found}
    plain = sorted(st + end for st in stems for end in ("", "e", "en", "n", "s") if st + end in words)
    if len(marks) < 2 and not plain:
        return []
    line, text, m = found[0]
    detail = ("plain form '%s'" % plain[0]) if plain else "different gender characters"
    return [Hit("DE_GENDER_MIX", REVIEW, line, _excerpt(text, m.start()),
                "Gender forms are mixed (%s). Keep one form throughout the text." % detail)]


def rule_de_connective_density(segs, profile, reg):
    """Mechanical connectives are normal German one at a time. Two or more at one per 150 words or denser is the AI rate."""
    found, words = [], 0
    for seg, text in _prose(segs):
        words += len(re.findall(r"[^\W\d_]+", text))
        low = text.lower()
        for phrase in L.DE_MECHANICAL_CONNECTIVES:
            found.extend((seg.line, text, m.start()) for m in re.finditer(r"(?<![^\W\d_])%s(?![^\W\d_])" % re.escape(phrase), low))
    if len(found) < 2 or len(found) * DE_CONNECTIVE_WORDS < words:
        return []
    line, text, pos = found[1]
    return [Hit("DE_CONNECTIVE_DENSITY", REVIEW, line, _excerpt(text, pos),
                "%d mechanical connectives in %d words (darüber hinaus, zudem, außerdem ...). Keep only the ones that link." % (len(found), words))]


def rule_de_ascii_umlaut(segs, profile, reg):
    hits = []
    for seg, text in _prose(segs, PROSE_KINDS + ("heading",)):
        for m in ASCII_UMLAUT.finditer(text):
            hits.append(Hit("DE_ASCII_UMLAUT", BLOCK, seg.line, _excerpt(text, m.start()),
                            "'%s' spells the umlaut as two letters. Write ä, ö or ü." % m.group(0)))
        for m in SS_SPELLING.finditer(text):
            hits.append(Hit("DE_SS_SPELLING", REVIEW, seg.line, _excerpt(text, m.start()),
                            "'%s' writes ss where standard German has ß." % m.group(0)))
    return hits


GERMAN_RULES = (
    rule_de_quotes, rule_de_en_dash, rule_de_number_format, rule_de_heading_case, rule_de_calque,
    rule_de_participle_tail, rule_de_address_mix, rule_de_gender_forms, rule_de_connective_density,
    rule_de_ascii_umlaut,
)
