# 02 — Author Filtering

How to extract only the author's turns from conversation exports.

---

## The problem

Conversation export files contain both the user's messages and the AI's responses interleaved. Including AI responses in the corpus contaminates the stylometric profile because AI systems have their own measurable style (shorter sentences, higher hedging, more "I'll help you" type openers, different function word distribution).

The `extract_author_turns.py` script solves this by reading the export format and extracting only the sections attributed to the author.

---

## Supported export formats

### Claude.ai export (primary format)

Claude.ai exports conversation markdown with heading-style author markers:

```
## Hiro

[author's message text]

## Claude

[assistant's response]

## Hiro

[author's next message]
```

The author marker is the heading that precedes the user's content. Default: `## Hiro`.

The script extracts everything between each `## Hiro` heading and the next heading (of any kind).

### Custom markers

If the user's export uses a different format, provide via `--marker`:

```bash
python extract_author_turns.py input/ --marker "**User:**"
python extract_author_turns.py input/ --marker "You:"
python extract_author_turns.py input/ --marker "## Me"
```

The marker is matched as a line prefix (stripped). Case-sensitive.

---

## Running the script

```bash
python extract_author_turns.py <input_dir> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--marker TEXT` | `## Hiro` | Author heading marker |
| `--output PATH` | stdout | Write extracted text to file |
| `--preview N` | 5 | Show N random sample turns before proceeding |
| `--min-file-bytes N` | 500 | Skip files smaller than N bytes |
| `--no-dedup` | — | Include `_2.md`, `_3.md` duplicate files |
| `--warn-threshold F` | 0.05 | Warn if author turns are < F fraction of source |

---

## Deduplication

Claude.ai exports often create duplicate files (`conversation.md`, `conversation_2.md`, `conversation_3.md`) for the same conversation. The script skips files ending in `_2.md`, `_3.md`, etc. by default.

Disable with `--no-dedup` if the numbered files are genuinely different conversations.

---

## Cleaning turn content

After extracting author turns, each turn is cleaned:

1. Strip frontmatter blocks
2. Strip code fences (content the user pasted in, not prose they wrote)
3. Strip inline code
4. Strip image tags
5. Strip markdown links (keep link text)
6. Strip HTML tags
7. Strip very short turns (< 20 chars) — these are usually "yes", "ok", "thanks"

---

## Claude-tell filtering

The script checks for markers that indicate the AI's content leaked into an author turn. These patterns flag a turn for human review rather than automatic exclusion:

- "I'll help you..."
- "Here's a..."
- "Certainly!"
- "As an AI..."
- "I'd be happy to..."
- "Let me know if you..."

If these appear in extracted author turns, check whether the export format placed AI content under an author heading.

---

## Preview and confirmation

Before writing the full extraction, the script shows 5 random sample turns. Confirm:

- Does the content read like the author's genuine writing?
- Are there any obvious AI phrases leaking through?
- Is the length distribution reasonable (some short, some long)?

If the preview shows mostly very short turns ("ok", "yes", "can you do X?") and little prose, the conversation export may be too transactional to be useful as a stylometric source. The script reports a warning if author turns average fewer than 30 words.

---

## Minimum corpus size

After extraction, check total word count:
- **< 5,000 words:** Extreme caution. Only use clear zero/one values (em-dash count, semicolon count).
- **5,000–20,000 words:** Directional values only. Warn in provenance file.
- **> 20,000 words:** Distributional features are reliable.
- **> 100,000 words:** High confidence. Rare features (hapax legomena, uncommon connectives) are measurable.
