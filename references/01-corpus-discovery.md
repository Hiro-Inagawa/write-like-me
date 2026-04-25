# 01 — Corpus Discovery

How to find the right source material for a voice skill.

---

## What makes a good corpus

A voice skill requires prose that the author actually wrote, in a register that will be used as the writing target. The ideal corpus has:

- **At least 5,000 words in the primary register** (the one that will be the writing target). Below 5,000 words, distributional features have high variance. Below 2,000 words, only the most extreme features are reliable.
- **Enough variety of topic** that the features measured reflect habit rather than subject matter. One long essay on a single topic may overfit.
- **No ghost-writing or heavily edited material** unless the author approved every sentence. Co-written content contaminates the profile.

---

## Common corpus locations

| Location type | Description | What to look for |
|--------------|-------------|-----------------|
| Essay / article folder | Finished polished prose | `.md`, `.txt`, `.docx` files; look for clean prose files, not outlines or notes |
| Academic paper folder | Formal register | Main draft files, not references sections or appendices |
| Blog posts | Public register | Source files, not CMS exports with HTML |
| Conversation exports | Casual register | Claude.ai, ChatGPT, or other conversational AI export files |
| Notes / personal documents | Personal register | Voice memos transcribed, journal entries, personal notes |
| Email drafts | Mixed formal/casual | Generally noisier; use if no other source |

---

## Consent guardrail

Before analyzing anything, confirm:

- Is this the user's own writing?
- If analyzing a shared corpus (team writing), does the user have permission from all contributors?

If any writing belongs to someone else without permission, exclude it.

---

## Register identification

Ask the user to categorize their writing sources by register. The register label determines which stylometric baseline to use for interpretation:

| Register | Description | Typical sentence length |
|----------|-------------|------------------------|
| `article-public` | Published or polished essays, blog posts | 20–40 words |
| `paper-formal` | Academic drafts, reports | 15–25 words |
| `declarative-personal` | Notes, profiles, personal documents | 10–20 words |
| `conversation-casual` | Chat, informal messages | 8–18 words |

If the user has only one type of writing, use that as the primary register.

---

## What to exclude

Always exclude:
- Content written by others (quoted material, third-party citations)
- Bot-generated content in conversation exports (use `extract_author_turns.py` to strip this)
- Research papers, arxiv PDFs, or any material not written by the user
- Changelog, commit messages, code comments (these are not prose)
- Structural metadata: front matter, YAML headers, table of contents

---

## When the corpus is small

If the total filtered corpus is under 20,000 words, warn: "distributional features may be unreliable." Still proceed, but flag in the provenance file which metrics are based on small-sample data. The hard rules (zero em-dashes, no announcement colons, etc.) are valid even from small samples when they represent extreme values (0 occurrences = always never uses it).
