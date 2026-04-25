---
name: {{name}}-voice
description: Use when drafting or revising prose, articles, essays, or {{register_type}} sections in {{author_name}}'s voice. Activates when the user asks to write, revise, or check style on any English-language prose document. Does NOT activate for code, structured data, or conversation.
---

# {{name}}-voice

A voice skill for writing and revising prose in {{author_name}}'s established register. Built from corpus analysis of {{total_words}}+ words across {{register_count}} registers ({{register_list}}), combined with explicitly stated style rules.

---

## Session start

Before producing any prose:

1. Read `references/01-generative.md` for the quantitative targets, structural patterns, and exemplars.
2. Read `references/02-corrective.md` for the hard bans and scan checklist.
3. State in one sentence what you will write or revise. Wait for confirmation or redirection.

After delivering any prose:

- Scan the output against `references/02-corrective.md` before sending.
- If any hard ban is present, fix it first.

---

## Hard rules

These gate every output. No draft leaves without passing all three.

### Rule 1. Sentence density

{{sentence_density_rule}}

### Rule 2. Zero mechanical banned characters

{{punctuation_ban_rule}}

### Rule 3. No performed rhetoric

{{rhetoric_ban_rule}}

---

## Routing table

| Task | Read |
|------|------|
| Writing new prose | `01-generative.md` first, then write |
| Revising existing prose | `02-corrective.md` first, scan, then fix |
| Checking whether a draft sounds right | Both references; compare against Exemplars in `01-generative.md` |
| Checking provenance of corpus and profile | `03-corpus-source.md` |

---

## Register notes

{{register_notes_table}}

---

## What this skill does not do

- Does not select the appropriate register — user specifies (or primary register is assumed).
- Does not generate citations, data, or arguments from scratch. It writes in voice; it does not research.
- Does not adjust for non-English prose — all rules apply to English text only.
