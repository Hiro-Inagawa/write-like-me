#!/usr/bin/env python3
"""voice_rules.py - deterministic voice rules for voice_check.py.

Every rule is a function (segments, profile, register) -> list[Hit]. Rules never read
files and never print. Severity and activation come from the resolved register and
the profile bans. Stdlib only.
"""
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from voice_segment import PROSE_KINDS, sentences_of  # noqa: E402

BLOCK = "block"
REVIEW = "review"

STANCE_OPENERS = ("honestly", "frankly", "importantly", "crucially", "interestingly", "surprisingly",
                  "notably", "admittedly", "evidently", "obviously", "clearly", "strikingly")
FILLER_OPENERS = ("it is worth noting that", "it's worth noting that", "it is important to mention",
                  "it should be pointed out that", "in today's rapidly changing world", "in recent years",
                  "since the dawn of", "it goes without saying", "needless to say")
PERFORMATIVE = {
    "delve": "examine", "delves": "examines", "delving": "examining",
    "leverage": "use", "leverages": "uses", "leveraged": "used", "leveraging": "using",
    "foster": "build", "fosters": "builds", "fostering": "building",
    "utilize": "use", "utilizes": "uses", "utilized": "used", "utilizing": "using",
    "elucidate": "explain", "elucidates": "explains", "underscore": "show", "underscores": "shows",
}
SUMMARY_OPENERS = ("in conclusion", "to summarize", "in summary", "to recap", "as we have seen", "as discussed above")
LIST_INTRO_WORDS = {"following", "follows", "these", "those", "two", "three", "four", "five", "six", "seven",
                    "eight", "nine", "ten", "respects", "reasons", "ways", "steps", "things", "parts", "kinds",
                    "types", "categories", "options", "examples", "example", "namely", "include", "includes"}
CONTRACTION = re.compile(
    r"\b(?:[A-Za-z]+n't|I'm|I've|I'll|I'd|you're|you've|you'll|you'd|we're|we've|we'll|we'd|"
    r"they're|they've|they'll|they'd|he's|she's|it's|that's|there's|here's|what's|who's|let's|"
    r"it'll|that'll|there'll)\b", re.IGNORECASE)
TRICOLON = re.compile(r"\b(\w+(?: \w+){0,3}), (\w+(?: \w+){0,3}), (?:and|or) (\w+(?: \w+){0,3})\b")
TRICOLON_ASYNDETIC = re.compile(r"\b(\w+(?: \w+){1,4}), (\w+(?: \w+){1,4}), (\w+(?: \w+){1,4})[.!?]\s*$")
ANTITHESIS_TAG = re.compile(r", not [^,.;:]{1,40}[.!?]|\brather than\b", re.IGNORECASE)
BUILDUP_STORY = re.compile(r"\btells? an? \w+ story\b", re.IGNORECASE)
ANNOUNCEMENT_HEAD_WORDS = 5
MANNER_AFTER = re.compile(r"\s+(marked|labeled|labelled|visible|defined|separated|stated|shown|identified|"
                          r"indicated|delineated|legible|distinguishable|distinguished|written|documented|signposted)\b")
COLON_MID = re.compile(r"(?<=[A-Za-z\)\"'])\s*:\s+(?=[A-Za-z\"'(])")


@dataclass(frozen=True)
class Hit:
    rule: str
    severity: str
    line: int
    excerpt: str
    message: str


QUOTED = re.compile(r'"[^"\n]{1,400}"')


def _in_quotes(text, pos):
    """True when pos falls inside a double-quoted span, so quoted words are someone else's."""
    return any(m.start() < pos < m.end() for m in QUOTED.finditer(text))


def _excerpt(text, pos, width=40):
    lo, hi = max(0, pos - width // 2), min(len(text), pos + width // 2)
    return text[lo:hi].strip()


def _phrase_hits(segs, phrases, rule, severity, message, kinds=PROSE_KINDS):
    hits = []
    for seg in segs:
        if seg.kind not in kinds:
            continue
        low = seg.text.lower()
        for phrase in phrases:
            for m in re.finditer(r"(?<![A-Za-z])" + re.escape(phrase.lower()) + r"(?![A-Za-z])", low):
                if _in_quotes(seg.text, m.start()):
                    continue
                if rule == "EMPTY_INTENSIFIER" and MANNER_AFTER.match(low, m.end()):
                    continue
                hits.append(Hit(rule, severity, seg.line, _excerpt(seg.text, m.start()), message % phrase))
    return hits


def _sentence_hits(segs, predicate, rule, severity, message, kinds=PROSE_KINDS):
    hits = []
    for seg in segs:
        if seg.kind not in kinds:
            continue
        for sent in sentences_of(seg.text):
            found = predicate(sent)
            if found:
                hits.append(Hit(rule, severity, seg.line, _excerpt(sent, 0, 60), message))
    return hits


def rule_em_dash(segs, profile, reg):
    hits = []
    for seg in segs:
        if seg.kind not in PROSE_KINDS + ("heading",):
            continue
        for m in re.finditer(r"—|(?<=\S) -- (?=\S)", seg.text):
            hits.append(Hit("EM_DASH", BLOCK, seg.line, _excerpt(seg.text, m.start()),
                            "Em dash in prose. Use a comma or a period."))
    return hits


def rule_stance_opener(segs, profile, reg):
    def pred(sent):
        first = re.sub(r"^[\"'(\s]+", "", sent).split(" ", 1)[0].strip(",.;:!?").lower()
        return first in STANCE_OPENERS
    return _sentence_hits(segs, pred, "STANCE_OPENER", BLOCK, "Stance adverbial opens the sentence. Delete it.")


def rule_filler_opener(segs, profile, reg):
    return _phrase_hits(segs, FILLER_OPENERS, "FILLER_OPENER", BLOCK, "Filler opener '%s'. Start with the claim.")


def rule_performative_verb(segs, profile, reg):
    hits = []
    for seg in segs:
        if seg.kind not in PROSE_KINDS:
            continue
        for m in re.finditer(r"\b([A-Za-z]+)\b", seg.text):
            word = m.group(1).lower()
            if word in PERFORMATIVE:
                hits.append(Hit("PERFORMATIVE_VERB", BLOCK, seg.line, _excerpt(seg.text, m.start()),
                                "'%s' is a performative verb. Use '%s'." % (word, PERFORMATIVE[word])))
    return hits


def rule_not_only(segs, profile, reg):
    pred = lambda s: re.search(r"\bnot only\b.*\bbut also\b", s, re.IGNORECASE) is not None
    return _sentence_hits(segs, pred, "NOT_ONLY_BUT_ALSO", BLOCK, "'not only ... but also'. State both plainly.")


def rule_summary_opener(segs, profile, reg):
    hits = []
    for seg in segs:
        if seg.kind != "prose":
            continue
        low = seg.text.lower()
        for phrase in SUMMARY_OPENERS:
            if low.startswith(phrase):
                hits.append(Hit("SUMMARY_OPENER", BLOCK, seg.line, _excerpt(seg.text, 0, 50),
                                "Paragraph opens with '%s'. Do the summarizing, do not announce it." % phrase))
    return hits


def _adjective_hits(segs, words, rule, severity):
    hits = []
    for seg in segs:
        if seg.kind not in PROSE_KINDS + ("heading",):
            continue
        for word in words:
            for m in re.finditer(r"\b" + re.escape(word) + r"\s+(?=[A-Za-z])", seg.text, re.IGNORECASE):
                before = seg.text[max(0, m.start() - 14):m.start()].lower()
                if word == "significant" and "statistically" in before:
                    continue
                if _in_quotes(seg.text, m.start()):
                    continue
                hits.append(Hit(rule, severity, seg.line, _excerpt(seg.text, m.start()),
                                "'%s' asserts a judgment. Replace it with the fact that earns it." % word))
    return hits


def rule_evaluative_adjective(segs, profile, reg):
    bans = profile.get("bans", {})
    return (_adjective_hits(segs, bans.get("evaluative_block", []), "EVALUATIVE_ADJECTIVE", BLOCK)
            + _adjective_hits(segs, bans.get("evaluative_review", []), "EVALUATIVE_ADJECTIVE_SOFT", REVIEW))


def rule_buildup_before_data(segs, profile, reg):
    def pred(sent):
        if BUILDUP_STORY.search(sent):
            return True
        m = re.search(r"[A-Za-z]:\s+\d", sent)
        if m is None:
            return False
        return not _is_label_line(sent, m.start() + 1)
    return _sentence_hits(segs, pred, "BUILDUP_BEFORE_DATA", BLOCK, "Buildup before a number. State the number directly.")


def rule_empty_intensifier(segs, profile, reg):
    level = reg.get("empty_intensifiers", BLOCK)
    if level == "off":
        return []
    return _phrase_hits(segs, profile.get("bans", {}).get("intensifiers", []), "EMPTY_INTENSIFIER", level,
                        "Empty intensifier '%s'. Remove it.")


def rule_hedge_connective(segs, profile, reg):
    level = reg.get("hedge_connectives", REVIEW)
    if level == "off":
        return []
    return _phrase_hits(segs, profile.get("bans", {}).get("hedge_connectives", []), "HEDGE_CONNECTIVE", level,
                        "Hedge connective '%s'. Either the caveat is the answer or it goes.")


def rule_semicolon(segs, profile, reg):
    if reg.get("semicolons") not in ("forbidden", "review"):
        return []
    severity = BLOCK if reg["semicolons"] == "forbidden" else REVIEW
    hits = []
    for seg in segs:
        if seg.kind != "prose":
            continue
        for m in re.finditer(";", seg.text):
            hits.append(Hit("SEMICOLON_PROSE", severity, seg.line, _excerpt(seg.text, m.start()),
                            "Semicolon in prose. Make two sentences."))
    return hits


LABEL_HEAD_DETERMINERS = {"the", "this", "that", "these", "those", "a", "an", "our", "my", "its",
                          "their", "his", "her", "your", "one", "every", "each"}


def _is_label_line(text, pos):
    head = text[:pos].split()
    if not head or len(head) > 3:
        return False
    if head[0].lower() in LABEL_HEAD_DETERMINERS:
        return False
    return text[:pos].strip() == text[:pos].strip().rstrip(":")


def rule_announcement_colon(segs, profile, reg):
    level = reg.get("announcement_colon", REVIEW)
    if level == "off":
        return []
    hits = []
    for seg in segs:
        if seg.kind != "prose":
            continue
        for sent in sentences_of(seg.text):
            if "://" in sent:
                continue
            for m in COLON_MID.finditer(sent):
                pos = m.start()
                head = sent[:pos].rstrip()
                if _is_label_line(sent, pos):
                    continue
                head_words = re.findall(r"[A-Za-z]+|\d+", head.lower())
                if not head_words:
                    continue
                if head_words[-1].isdigit() or any(w in LIST_INTRO_WORDS for w in head_words[-3:]):
                    continue
                if re.search(r"\d$", head):
                    continue
                short_head = len(head_words) <= ANNOUNCEMENT_HEAD_WORDS
                severity = level if (short_head or level != BLOCK) else REVIEW
                message = ("Announcement colon after a short head. Write the sentence instead." if short_head
                           else "Colon introduces an elaboration. Keep it only if the sentence needs it.")
                hits.append(Hit("ANNOUNCEMENT_COLON", severity, seg.line, _excerpt(sent, pos), message))
    return hits


def rule_staccato_run(segs, profile, reg):
    th = profile.get("thresholds", {})
    short = int(th.get("short_sentence_words", 8))
    run_len = int(th.get("staccato_run", 3))
    severity = BLOCK if reg.get("targets", {}).get("pct_short_le5_max", None) == 0 else REVIEW
    hits = []
    for seg in segs:
        if seg.kind != "prose":
            continue
        sents = sentences_of(seg.text)
        run = 0
        for i, sent in enumerate(sents):
            words = len(re.findall(r"[A-Za-z']+", sent))
            run = run + 1 if words <= short else 0
            if run == run_len:
                hits.append(Hit("STACCATO_RUN", severity, seg.line, _excerpt(" ".join(sents[i - run_len + 1:i + 1]), 0, 70),
                                "%d consecutive short sentences. Join the connected thoughts." % run_len))
    return hits


def rule_tricolon(segs, profile, reg):
    level = reg.get("tricolon", REVIEW)
    if level == "off":
        return []
    pred = lambda s: TRICOLON.search(s) is not None or TRICOLON_ASYNDETIC.search(s) is not None
    return _sentence_hits(segs, pred, "TRICOLON", level, "Three parallel items. Keep only if the list is taxonomic.", kinds=("prose",))


def rule_compressed_antithesis(segs, profile, reg):
    level = reg.get("compressed_antithesis", REVIEW)
    if level == "off":
        return []
    pred = lambda s: ANTITHESIS_TAG.search(s) is not None
    return _sentence_hits(segs, pred, "COMPRESSED_ANTITHESIS", level,
                          "'X, not Y' or 'rather than' tag. Delete the tail if it adds nothing.", kinds=("prose",))


def rule_protest_framing(segs, profile, reg):
    return _phrase_hits(segs, profile.get("bans", {}).get("protest_framing", []), "PROTEST_FRAMING", REVIEW,
                        "Protest framing '%s'. State the positive claim.", kinds=("prose",))


def rule_contractions(segs, profile, reg):
    if reg.get("contractions") != "forbidden":
        return []
    hits = []
    for seg in segs:
        if seg.kind not in PROSE_KINDS:
            continue
        for m in CONTRACTION.finditer(seg.text):
            hits.append(Hit("CONTRACTION", BLOCK, seg.line, _excerpt(seg.text, m.start()),
                            "Contraction '%s'. Write it out." % m.group(0)))
    return hits


def rule_questions(segs, profile, reg):
    if reg.get("questions") != "forbidden":
        return []
    pred = lambda s: s.rstrip().endswith("?")
    return _sentence_hits(segs, pred, "RHETORICAL_QUESTION", REVIEW, "Question in prose. Resolve the tension instead of staging it.", kinds=("prose",))


def rule_exclamation(segs, profile, reg):
    level = reg.get("exclamations", "off")
    if level == "off":
        return []
    pred = lambda s: s.rstrip().endswith("!")
    return _sentence_hits(segs, pred, "EXCLAMATION", level, "Exclamation mark in prose. End the sentence with a period.", kinds=("prose",))


def rule_meta_commentary(segs, profile, reg):
    level = reg.get("meta_commentary", "off")
    if level == "off":
        return []
    return _phrase_hits(segs, profile.get("bans", {}).get("meta_commentary", []), "META_COMMENTARY", level,
                        "Meta commentary '%s'. Answer, do not narrate.")


def rule_extra_phrases(segs, profile, reg):
    return _phrase_hits(segs, profile.get("bans", {}).get("extra_phrases", []), "EXTRA_PHRASE", BLOCK,
                        "Banned phrase '%s' from the voice profile.")


RULES = (
    rule_em_dash, rule_stance_opener, rule_filler_opener, rule_performative_verb, rule_not_only,
    rule_summary_opener, rule_evaluative_adjective, rule_buildup_before_data, rule_empty_intensifier,
    rule_hedge_connective, rule_semicolon, rule_announcement_colon, rule_staccato_run, rule_tricolon,
    rule_compressed_antithesis, rule_protest_framing, rule_contractions, rule_questions,
    rule_exclamation, rule_meta_commentary, rule_extra_phrases,
)


def apply_overrides(hits, profile):
    """profile.rule_overrides maps a rule id to off, review, or block for this voice."""
    overrides = profile.get("rule_overrides") or {}
    if not overrides:
        return hits
    out = []
    for h in hits:
        level = overrides.get(h.rule)
        if level == "off":
            continue
        if level in (REVIEW, BLOCK) and level != h.severity:
            h = replace(h, severity=level)
        out.append(h)
    return out


def run_rules(segs, profile, reg):
    hits = []
    for rule in RULES:
        hits.extend(rule(segs, profile, reg))
    hits = apply_overrides(hits, profile)
    return sorted(hits, key=lambda h: (h.line, h.rule))
