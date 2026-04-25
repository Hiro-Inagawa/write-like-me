#!/usr/bin/env python3
"""
stylometry.py — Extract stylometric features from a writing corpus.

Usage:
    python stylometry.py <input> [options]

    <input>  A single .md/.txt file, or a directory (processes all .md/.txt files).

Options:
    --register NAME      Tag this corpus with a register name (default: "default")
    --output PATH        Write JSON profile to this path (default: prints to stdout)
    --report PATH        Write a markdown report to this path
    --no-textstat        Skip textstat features even if the package is installed
    --no-spacy           Skip spaCy features even if the package is installed
    --min-words N        Warn if filtered corpus has fewer than N words (default: 20000)

Optional dependencies (install for additional features):
    pip install textstat       Readability metrics (Flesch-Kincaid, Gunning Fog, etc.)
    pip install spacy          POS rhythm, dependency depth, passive voice, nominalization
    python -m spacy download en_core_web_sm

Tier 1 features (stdlib only): sentence length, function words, punctuation rates,
    hedging/booster density, pronoun rates, distinctive content words, MATTR,
    paragraph structure, sentence-initial patterns, structural markers.

Tier 2 features (textstat): readability scores, syllable stats, lexical density.

Tier 3 features (spaCy): POS bigram frequencies, avg dependency tree depth,
    passive voice ratio, nominalization rate.
"""

import sys
import os
import re
import json
import math
import statistics
import collections
import argparse
import random
from pathlib import Path
from datetime import date

# --- Optional dependencies ---

try:
    import textstat as _textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False

try:
    import spacy as _spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

# --- Constants ---

FUNCTION_WORDS = frozenset({
    "a", "about", "above", "after", "again", "ago", "all", "also", "although",
    "am", "an", "and", "any", "are", "as", "at", "be", "because", "been",
    "before", "being", "between", "but", "by", "can", "could", "did", "do",
    "does", "doing", "down", "during", "each", "either", "else", "even",
    "every", "except", "few", "for", "from", "further", "get", "got", "had",
    "has", "have", "having", "he", "her", "here", "him", "his", "how", "however",
    "i", "if", "in", "into", "is", "it", "its", "itself", "just", "like",
    "made", "make", "many", "may", "me", "might", "more", "most", "much",
    "must", "my", "myself", "neither", "no", "nor", "not", "now", "of", "off",
    "often", "on", "once", "only", "or", "other", "our", "out", "over", "own",
    "perhaps", "quite", "rather", "she", "should", "since", "so", "some",
    "something", "still", "such", "than", "that", "the", "their", "them",
    "then", "there", "these", "they", "this", "those", "though", "through",
    "to", "too", "under", "until", "up", "us", "very", "was", "we", "well",
    "were", "what", "when", "where", "whether", "which", "while", "who",
    "whom", "whose", "will", "with", "within", "without", "would", "yet",
    "you", "your", "yourself",
})

HEDGE_TOKENS = frozenset({
    "might", "maybe", "perhaps", "somewhat", "roughly", "possibly", "could",
    "would", "may", "likely", "unlikely", "apparently", "presumably",
    "generally", "often", "sometimes", "occasionally", "tend", "tends",
    "suggest", "suggests", "suggest", "appear", "appears", "seem", "seems",
    "indicate", "indicates",
})
HEDGE_PHRASES = ["i think", "i believe", "i suspect", "in some sense",
                 "in a sense", "to some degree", "to some extent", "in many ways"]

BOOSTER_TOKENS = frozenset({
    "clearly", "obviously", "certainly", "definitely", "undoubtedly",
    "absolutely", "always", "never", "impossible", "inevitably",
    "necessarily", "must", "invariably", "unambiguously",
})

PRONOUN_FIRST_SG  = frozenset({"i", "me", "my", "myself", "mine"})
PRONOUN_FIRST_PL  = frozenset({"we", "us", "our", "ourselves", "ours"})
PRONOUN_SECOND    = frozenset({"you", "your", "yourself", "yourselves", "yours"})
PRONOUN_THIRD     = frozenset({
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "they", "them", "their", "themselves", "theirs",
    "it", "its", "itself",
})

CONCESSION_WORDS  = frozenset({"but", "however", "though", "although", "whereas",
                                "while", "yet", "nonetheless", "nevertheless",
                                "despite", "notwithstanding"})

# Abbreviations that should not trigger sentence splits
ABBREVIATIONS = re.compile(r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e|fig|al|cf)\.')

# --- Markdown stripping ---

_RE_FRONTMATTER     = re.compile(r'^\s*---.*?---\s*', re.DOTALL)
_RE_CODE_FENCE      = re.compile(r'```.*?```', re.DOTALL)
_RE_INLINE_CODE     = re.compile(r'`[^`\n]+`')
_RE_COMPONENT_TAG   = re.compile(r'\[[-\w]+\s*—[^\]]*\]') # [name — description] single-line only
_RE_CITATION_INLINE = re.compile(r'\\\[\d+\\\]|\[(\d+)\]') # \[N\] or [N]
_RE_TABLE_ROW       = re.compile(r'^\s*\|.*\|\s*$', re.MULTILINE)
_RE_IMAGE_TAG       = re.compile(r'!\[.*?\]\(.*?\)')
_RE_HTML_TAG        = re.compile(r'<[^>]+>')
_RE_ANCHOR          = re.compile(r'\{#[^}]+\}')
_RE_HEADING         = re.compile(r'^#{1,6}\s+', re.MULTILINE)
_RE_BOLD_ITALIC     = re.compile(r'\*{1,3}(.*?)\*{1,3}')
_RE_HORIZONTAL_RULE = re.compile(r'^\s*[-*_]{3,}\s*$', re.MULTILINE)
_RE_MULTI_BLANK     = re.compile(r'\n{3,}')


def strip_markdown(text: str) -> str:
    """Remove markdown structure, returning prose-only text."""
    text = _RE_FRONTMATTER.sub('', text)
    text = _RE_CODE_FENCE.sub(' ', text)
    text = _RE_INLINE_CODE.sub(' ', text)
    text = _RE_COMPONENT_TAG.sub(' ', text)
    text = _RE_CITATION_INLINE.sub(' ', text)
    text = _RE_TABLE_ROW.sub('', text)
    text = _RE_IMAGE_TAG.sub(' ', text)
    text = _RE_HTML_TAG.sub(' ', text)
    text = _RE_ANCHOR.sub('', text)
    text = _RE_HEADING.sub('', text)
    text = _RE_BOLD_ITALIC.sub(r'\1', text)
    text = _RE_HORIZONTAL_RULE.sub('', text)
    # Remove markdown link syntax but keep link text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = _RE_MULTI_BLANK.sub('\n\n', text)
    return text.strip()


def count_structural_markers(raw_text: str) -> dict:
    """Count markdown structural elements in the raw (un-stripped) text."""
    lines = raw_text.split('\n')
    total_lines = len(lines)
    bullet_lines = sum(1 for l in lines if re.match(r'^\s*[-*+]\s', l))
    heading_lines = sum(1 for l in lines if re.match(r'^#{1,6}\s', l))
    code_fences = len(_RE_CODE_FENCE.findall(raw_text))
    return {
        "total_lines": total_lines,
        "bullet_lines": bullet_lines,
        "heading_lines": heading_lines,
        "code_fences": code_fences,
        "bullet_ratio": round(bullet_lines / max(total_lines, 1), 4),
        "heading_density_per_1000_words": 0,  # updated after word count
    }


# --- Segmentation ---

def split_sentences(text: str) -> list:
    """Heuristic sentence splitter that avoids common abbreviations."""
    text = ABBREVIATIONS.sub(lambda m: m.group(0).replace('.', '<DOT>'), text)
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'(])', text)
    sentences = []
    for part in parts:
        part = part.replace('<DOT>', '.').strip()
        if len(part) > 3:
            sentences.append(part)
    return sentences


def tokenize_words(text: str) -> list:
    """Lowercase word tokens, stripping leading/trailing punctuation."""
    raw_tokens = re.findall(r"[a-zA-Z''-]+", text)
    words = []
    for tok in raw_tokens:
        tok = tok.strip("'-").lower()
        if tok:
            words.append(tok)
    return words


def split_paragraphs(text: str) -> list:
    """Split on double newlines; return non-empty paragraphs."""
    return [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]


# --- Feature computations (Tier 1: stdlib) ---

def compute_mattr(words: list, window: int = 100) -> float:
    """Moving Average Type-Token Ratio."""
    if len(words) < window:
        if not words:
            return 0.0
        return round(len(set(words)) / len(words), 4)
    ttrs = []
    for i in range(len(words) - window + 1):
        chunk = words[i:i + window]
        ttrs.append(len(set(chunk)) / window)
    return round(statistics.mean(ttrs), 4)


def compute_function_word_profile(words: list) -> dict:
    """Frequency of each function word, normalized per 1000 words."""
    total = max(len(words), 1)
    fw_counts = collections.Counter(w for w in words if w in FUNCTION_WORDS)
    profile = {}
    for fw, count in fw_counts.most_common(50):
        profile[fw] = round(count / total * 1000, 3)
    return profile


def compute_distinctive_content_words(words: list, top_n: int = 30) -> list:
    """Most frequent non-function content words (placeholder for true TF-IDF)."""
    content = [w for w in words if w not in FUNCTION_WORDS and len(w) > 2]
    counter = collections.Counter(content)
    total = max(len(words), 1)
    return [
        {"word": w, "count": c, "per_1000": round(c / total * 1000, 3)}
        for w, c in counter.most_common(top_n)
    ]


def compute_punctuation_rates(text: str, word_count: int) -> dict:
    """Count punctuation marks, return rates per 1000 words and per sentence."""
    sentences = split_sentences(text)
    n_sent = max(len(sentences), 1)
    per_kw = lambda n: round(n / max(word_count, 1) * 1000, 3)
    per_sent = lambda n: round(n / n_sent, 3)

    commas     = text.count(',')
    em_dashes  = text.count('—') + text.count('--')
    en_dashes  = text.count('–')
    semicolons = text.count(';')
    colons     = text.count(':')
    parens     = text.count('(')
    questions  = text.count('?')
    exclaims   = text.count('!')
    ellipses   = text.count('...')

    return {
        "comma_per_sentence": per_sent(commas),
        "comma_per_1000w": per_kw(commas),
        "em_dash_per_1000w": per_kw(em_dashes),
        "semicolon_per_1000w": per_kw(semicolons),
        "colon_per_1000w": per_kw(colons),
        "parenthetical_per_1000w": per_kw(parens),
        "question_per_1000w": per_kw(questions),
        "exclamation_per_1000w": per_kw(exclaims),
        "ellipsis_per_1000w": per_kw(ellipses),
        "en_dash_per_1000w": per_kw(en_dashes),
    }


def compute_sentence_stats(sentences: list) -> dict:
    """Length statistics over the sentence list."""
    if not sentences:
        return {}
    lengths = [len(tokenize_words(s)) for s in sentences]
    lengths = [l for l in lengths if l > 0]
    if not lengths:
        return {}
    sorted_l = sorted(lengths)
    n = len(sorted_l)
    return {
        "sentence_count": n,
        "mean_words": round(statistics.mean(lengths), 2),
        "median_words": round(statistics.median(lengths), 2),
        "stdev_words": round(statistics.stdev(lengths) if n > 1 else 0, 2),
        "q1_words": sorted_l[n // 4],
        "q3_words": sorted_l[3 * n // 4],
        "min_words": sorted_l[0],
        "max_words": sorted_l[-1],
        "pct_short_le5": round(sum(1 for l in lengths if l <= 5) / n, 3),
        "pct_long_ge30": round(sum(1 for l in lengths if l >= 30) / n, 3),
    }


def compute_sentence_initial_patterns(sentences: list, top_n: int = 20) -> list:
    """Most common first words across sentences."""
    initials = []
    for s in sentences:
        words = tokenize_words(s)
        if words:
            initials.append(words[0])
    counter = collections.Counter(initials)
    return [{"word": w, "count": c} for w, c in counter.most_common(top_n)]


def compute_paragraph_stats(paragraphs: list) -> dict:
    """Word count statistics over paragraphs."""
    if not paragraphs:
        return {}
    lengths = [len(tokenize_words(p)) for p in paragraphs if len(tokenize_words(p)) > 0]
    if not lengths:
        return {}
    return {
        "paragraph_count": len(lengths),
        "mean_words": round(statistics.mean(lengths), 2),
        "median_words": round(statistics.median(lengths), 2),
        "stdev_words": round(statistics.stdev(lengths) if len(lengths) > 1 else 0, 2),
    }


def compute_hedging_booster(words: list, raw_text: str) -> dict:
    """Hedge and booster token rates per 100 words."""
    total = max(len(words), 1)
    hedge_count = sum(1 for w in words if w in HEDGE_TOKENS)
    boost_count = sum(1 for w in words if w in BOOSTER_TOKENS)
    text_lower = raw_text.lower()
    for phrase in HEDGE_PHRASES:
        hedge_count += text_lower.count(phrase)
    return {
        "hedge_per_100w": round(hedge_count / total * 100, 3),
        "boost_per_100w": round(boost_count / total * 100, 3),
        "hedge_boost_ratio": round(hedge_count / max(boost_count, 1), 3),
    }


def compute_pronoun_rates(words: list) -> dict:
    """First/second/third person pronoun rates per 100 words."""
    total = max(len(words), 1)
    p1sg = sum(1 for w in words if w in PRONOUN_FIRST_SG)
    p1pl = sum(1 for w in words if w in PRONOUN_FIRST_PL)
    p2   = sum(1 for w in words if w in PRONOUN_SECOND)
    p3   = sum(1 for w in words if w in PRONOUN_THIRD)
    return {
        "first_sg_per_100w": round(p1sg / total * 100, 3),
        "first_pl_per_100w": round(p1pl / total * 100, 3),
        "second_per_100w": round(p2 / total * 100, 3),
        "third_per_100w": round(p3 / total * 100, 3),
        "first_pl_to_sg_ratio": round(p1pl / max(p1sg, 1), 3),
    }


def compute_concession_rate(sentences: list) -> float:
    """Fraction of sentences containing a concession word."""
    if not sentences:
        return 0.0
    hits = 0
    for s in sentences:
        words = set(tokenize_words(s))
        if words & CONCESSION_WORDS:
            hits += 1
    return round(hits / len(sentences), 3)


def compute_hapax_ratio(words: list) -> float:
    """Ratio of words that appear exactly once."""
    if not words:
        return 0.0
    counter = collections.Counter(words)
    hapax = sum(1 for c in counter.values() if c == 1)
    return round(hapax / len(words), 4)


# --- Tier 2: textstat ---

def compute_readability(text: str) -> dict:
    if not HAS_TEXTSTAT or not text.strip():
        return {}
    try:
        return {
            "flesch_kincaid_grade": _textstat.flesch_kincaid_grade(text),
            "gunning_fog": _textstat.gunning_fog(text),
            "flesch_reading_ease": _textstat.flesch_reading_ease(text),
            "avg_syllables_per_word": round(_textstat.avg_syllables_per_word(text), 3),
            "lexical_density": round(
                _textstat.lexicon_count(text, removepunct=True) /
                max(_textstat.word_count(text), 1), 3
            ),
        }
    except Exception:
        return {}


# --- Tier 3: spaCy ---

def compute_spacy_features(text: str) -> dict:
    if not HAS_SPACY:
        return {}
    try:
        nlp = _spacy.load("en_core_web_sm")
    except OSError:
        return {"error": "spaCy model not found — run: python -m spacy download en_core_web_sm"}

    chunk = text[:50000]  # spaCy has memory limits; sample if huge
    doc = nlp(chunk)

    pos_bigrams = collections.Counter()
    depths = []
    passive_count = 0
    nominalizations = 0
    nom_suffixes = ("tion", "ness", "ment", "ity", "ism", "ance", "ence")

    for sent in doc.sents:
        tokens = [t for t in sent if not t.is_space]
        pos_seq = [t.pos_ for t in tokens]
        for i in range(len(pos_seq) - 1):
            pos_bigrams[(pos_seq[i], pos_seq[i+1])] += 1

        depths.append(max((t.head.i - t.i for t in tokens), default=0))

        verbs = [t for t in tokens if t.pos_ == "VERB"]
        for v in verbs:
            children_deps = {c.dep_ for c in v.children}
            if "nsubjpass" in children_deps or "auxpass" in children_deps:
                passive_count += 1

        for t in tokens:
            if t.pos_ == "NOUN" and any(t.lemma_.endswith(s) for s in nom_suffixes):
                nominalizations += 1

    total_sents = max(len(list(doc.sents)), 1)
    total_tokens = max(len([t for t in doc if not t.is_space]), 1)

    top_bigrams = [
        {"pos_bigram": f"{a}+{b}", "count": c}
        for (a, b), c in pos_bigrams.most_common(20)
    ]

    return {
        "avg_dependency_depth": round(statistics.mean(depths) if depths else 0, 3),
        "passive_ratio": round(passive_count / total_sents, 3),
        "nominalization_per_1000w": round(nominalizations / total_tokens * 1000, 3),
        "top_pos_bigrams": top_bigrams,
    }


# --- Main feature aggregation ---

def compute_features(text: str, register: str = "default",
                     use_textstat: bool = True, use_spacy: bool = True) -> dict:
    """Compute all features for a block of prose text."""
    prose = strip_markdown(text)
    sentences = split_sentences(prose)
    words = tokenize_words(prose)
    paragraphs = split_paragraphs(prose)

    word_count = len(words)
    structural = count_structural_markers(text)
    structural["heading_density_per_1000_words"] = round(
        structural["heading_lines"] / max(word_count, 1) * 1000, 3
    )

    profile = {
        "register": register,
        "corpus_stats": {
            "word_count": word_count,
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "char_count": len(prose),
        },
        "lexical": {
            "mattr_window100": compute_mattr(words),
            "hapax_ratio": compute_hapax_ratio(words),
            "distinctive_content_words": compute_distinctive_content_words(words),
            "function_word_profile": compute_function_word_profile(words),
        },
        "syntactic": {
            "sentence_stats": compute_sentence_stats(sentences),
            "sentence_initial_patterns": compute_sentence_initial_patterns(sentences),
            "paragraph_stats": compute_paragraph_stats(paragraphs),
            "concession_rate": compute_concession_rate(sentences),
        },
        "punctuation": compute_punctuation_rates(prose, word_count),
        "hedging_booster": compute_hedging_booster(words, prose),
        "pronouns": compute_pronoun_rates(words),
        "structural": structural,
    }

    if use_textstat and HAS_TEXTSTAT:
        profile["readability"] = compute_readability(prose)

    if use_spacy and HAS_SPACY:
        profile["deep_syntactic"] = compute_spacy_features(prose)

    return profile


# --- Report generation ---

def generate_report(profile: dict, source_label: str = "") -> str:
    """Generate a human-readable markdown report from a feature profile."""
    lines = [
        f"# Stylometric Profile",
        f"",
        f"**Source:** {source_label or 'unknown'}  ",
        f"**Register:** {profile.get('register', 'default')}  ",
        f"**Date:** {date.today().isoformat()}",
        f"",
        f"---",
        f"",
        f"## Corpus Overview",
        f"",
    ]

    cs = profile.get("corpus_stats", {})
    lines += [
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Words (filtered prose) | {cs.get('word_count', '—'):,} |",
        f"| Sentences | {cs.get('sentence_count', '—'):,} |",
        f"| Paragraphs | {cs.get('paragraph_count', '—'):,} |",
        f"",
    ]

    if cs.get("word_count", 0) < 20000:
        lines.append(f"> **Warning:** corpus has fewer than 20,000 words after filtering. "
                     f"Distributional features may be unreliable.\n")

    # Sentence length
    ss = profile.get("syntactic", {}).get("sentence_stats", {})
    if ss:
        lines += [
            f"## Sentence Length",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Mean words | {ss.get('mean_words', '—')} |",
            f"| Median words | {ss.get('median_words', '—')} |",
            f"| Std dev | {ss.get('stdev_words', '—')} |",
            f"| Q1 / Q3 | {ss.get('q1_words', '—')} / {ss.get('q3_words', '—')} |",
            f"| Min / Max | {ss.get('min_words', '—')} / {ss.get('max_words', '—')} |",
            f"| % short (≤5 words) | {ss.get('pct_short_le5', 0)*100:.1f}% |",
            f"| % long (≥30 words) | {ss.get('pct_long_ge30', 0)*100:.1f}% |",
            f"",
        ]

    # Punctuation
    punc = profile.get("punctuation", {})
    if punc:
        lines += [
            f"## Punctuation Rates (per 1000 words unless noted)",
            f"",
            f"| Punctuation | Rate |",
            f"|-------------|------|",
            f"| Comma (per sentence) | {punc.get('comma_per_sentence', '—')} |",
            f"| Em dash | {punc.get('em_dash_per_1000w', '—')} |",
            f"| En dash | {punc.get('en_dash_per_1000w', '—')} |",
            f"| Semicolon | {punc.get('semicolon_per_1000w', '—')} |",
            f"| Colon | {punc.get('colon_per_1000w', '—')} |",
            f"| Parenthetical | {punc.get('parenthetical_per_1000w', '—')} |",
            f"| Question mark | {punc.get('question_per_1000w', '—')} |",
            f"| Exclamation | {punc.get('exclamation_per_1000w', '—')} |",
            f"| Ellipsis | {punc.get('ellipsis_per_1000w', '—')} |",
            f"",
        ]

    # Hedging / booster
    hb = profile.get("hedging_booster", {})
    if hb:
        lines += [
            f"## Hedging and Booster Density (per 100 words)",
            f"",
            f"| Metric | Rate |",
            f"|--------|------|",
            f"| Hedge tokens | {hb.get('hedge_per_100w', '—')} |",
            f"| Booster tokens | {hb.get('boost_per_100w', '—')} |",
            f"| Hedge/boost ratio | {hb.get('hedge_boost_ratio', '—')} |",
            f"",
        ]

    # Pronouns
    pr = profile.get("pronouns", {})
    if pr:
        lines += [
            f"## Pronoun Rates (per 100 words)",
            f"",
            f"| Pronoun class | Rate |",
            f"|--------------|------|",
            f"| First person singular (I/me/my) | {pr.get('first_sg_per_100w', '—')} |",
            f"| First person plural (we/us/our) | {pr.get('first_pl_per_100w', '—')} |",
            f"| Second person (you/your) | {pr.get('second_per_100w', '—')} |",
            f"| Third person | {pr.get('third_per_100w', '—')} |",
            f"| We/I ratio | {pr.get('first_pl_to_sg_ratio', '—')} |",
            f"",
        ]

    # Sentence-initial patterns
    sip = profile.get("syntactic", {}).get("sentence_initial_patterns", [])
    if sip:
        lines += [f"## Sentence-Initial Word Patterns (top 20)", f"", f"| Word | Count |", f"|------|-------|"]
        for item in sip[:20]:
            lines.append(f"| {item['word']} | {item['count']} |")
        lines.append("")

    # Distinctive content words
    dcw = profile.get("lexical", {}).get("distinctive_content_words", [])
    if dcw:
        lines += [f"## Most-Used Content Words (top 30)", f"", f"| Word | Per 1000 words |", f"|------|----------------|"]
        for item in dcw[:30]:
            lines.append(f"| {item['word']} | {item['per_1000']} |")
        lines.append("")

    # Function word profile
    fwp = profile.get("lexical", {}).get("function_word_profile", {})
    if fwp:
        top10_fw = sorted(fwp.items(), key=lambda x: -x[1])[:10]
        lines += [
            f"## Top Function Words (per 1000 words, top 10 shown)",
            f"",
            f"| Word | Rate |",
            f"|------|------|",
        ]
        for w, rate in top10_fw:
            lines.append(f"| {w} | {rate} |")
        lines.append("")

    # Lexical richness
    lex = profile.get("lexical", {})
    lines += [
        f"## Lexical Richness",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| MATTR (window 100) | {lex.get('mattr_window100', '—')} |",
        f"| Hapax ratio | {lex.get('hapax_ratio', '—')} |",
        f"| Concession rate | {profile.get('syntactic', {}).get('concession_rate', '—')} |",
        f"",
    ]

    # Paragraph stats
    ps = profile.get("syntactic", {}).get("paragraph_stats", {})
    if ps:
        lines += [
            f"## Paragraph Structure",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Paragraph count | {ps.get('paragraph_count', '—')} |",
            f"| Mean words/paragraph | {ps.get('mean_words', '—')} |",
            f"| Median words/paragraph | {ps.get('median_words', '—')} |",
            f"| Std dev | {ps.get('stdev_words', '—')} |",
            f"",
        ]

    # Readability
    rd = profile.get("readability", {})
    if rd and not rd.get("error"):
        lines += [
            f"## Readability (textstat)",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Flesch-Kincaid grade | {rd.get('flesch_kincaid_grade', '—')} |",
            f"| Gunning Fog | {rd.get('gunning_fog', '—')} |",
            f"| Flesch reading ease | {rd.get('flesch_reading_ease', '—')} |",
            f"| Avg syllables/word | {rd.get('avg_syllables_per_word', '—')} |",
            f"| Lexical density | {rd.get('lexical_density', '—')} |",
            f"",
        ]

    # Deep syntactic
    ds = profile.get("deep_syntactic", {})
    if ds and not ds.get("error"):
        lines += [
            f"## Deep Syntactic (spaCy)",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Avg dependency depth | {ds.get('avg_dependency_depth', '—')} |",
            f"| Passive ratio | {ds.get('passive_ratio', '—')} |",
            f"| Nominalizations per 1000w | {ds.get('nominalization_per_1000w', '—')} |",
            f"",
        ]
        top_pos = ds.get("top_pos_bigrams", [])[:10]
        if top_pos:
            lines += [f"**Top POS bigrams:**", f"", f"| POS bigram | Count |", f"|------------|-------|"]
            for item in top_pos:
                lines.append(f"| {item['pos_bigram']} | {item['count']} |")
            lines.append("")

    return "\n".join(lines)


# --- File loading ---

def load_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Warning: could not read {path}: {e}", file=sys.stderr)
        return ""


def load_corpus(input_path: Path) -> tuple:
    """Returns (combined_text, {register: text} per register)."""
    if input_path.is_file():
        text = load_file(input_path)
        return text, {"default": text}
    elif input_path.is_dir():
        files = sorted(input_path.rglob("*.md")) + sorted(input_path.rglob("*.txt"))
        combined = []
        for f in files:
            text = load_file(f)
            if text.strip():
                combined.append(text)
        return "\n\n".join(combined), {}
    else:
        print(f"Error: {input_path} is not a file or directory.", file=sys.stderr)
        sys.exit(1)


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Stylometric feature extraction for writing corpus analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="File or directory to analyze")
    parser.add_argument("--register", default="default", help="Register label for this corpus")
    parser.add_argument("--output", help="Write JSON profile to this path")
    parser.add_argument("--report", help="Write markdown report to this path")
    parser.add_argument("--no-textstat", action="store_true")
    parser.add_argument("--no-spacy", action="store_true")
    parser.add_argument("--min-words", type=int, default=20000)
    args = parser.parse_args()

    input_path = Path(args.input)
    combined_text, _ = load_corpus(input_path)

    if not combined_text.strip():
        print("Error: no text found in input.", file=sys.stderr)
        sys.exit(1)

    use_textstat = HAS_TEXTSTAT and not args.no_textstat
    use_spacy    = HAS_SPACY    and not args.no_spacy

    if HAS_TEXTSTAT and not use_textstat:
        print("Note: textstat is installed but --no-textstat was set.", file=sys.stderr)
    if HAS_SPACY and not use_spacy:
        print("Note: spaCy is installed but --no-spacy was set.", file=sys.stderr)
    if not HAS_TEXTSTAT:
        print("Note: textstat not installed — readability features disabled. pip install textstat", file=sys.stderr)
    if not HAS_SPACY:
        print("Note: spaCy not installed — deep syntactic features disabled. pip install spacy", file=sys.stderr)

    profile = compute_features(
        combined_text,
        register=args.register,
        use_textstat=use_textstat,
        use_spacy=use_spacy,
    )

    word_count = profile["corpus_stats"]["word_count"]
    if word_count < args.min_words:
        print(f"Warning: corpus has {word_count:,} words after filtering "
              f"(minimum recommended: {args.min_words:,}). "
              "Distributional features may be unreliable.", file=sys.stderr)

    # Output JSON
    json_str = json.dumps(profile, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(json_str, encoding="utf-8")
        print(f"JSON profile written to {args.output}", file=sys.stderr)
    else:
        print(json_str)

    # Output report
    if args.report:
        report_text = generate_report(profile, source_label=str(input_path))
        Path(args.report).write_text(report_text, encoding="utf-8")
        print(f"Markdown report written to {args.report}", file=sys.stderr)


if __name__ == "__main__":
    main()
