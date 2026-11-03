# 09. How to Write

Read this file before the voice targets and bans. It describes how the writing is done. The profile, the baseline and the checker describe how the result is measured, and they can only confirm a text that was written the way this file describes.

It applies to every text that other people will read. That includes emails, cover letters, answers to form fields, profile texts, portfolio pages, case studies, summaries and overviews, website copy, social posts, listing texts, and the prose of a README. It also applies when the author asks a question about such a text.

## The rule

Write the text the way you would explain the subject to the author in chat. When you explain something to a person across a table, you say what the thing is, how it works, and why it exists, in ordinary words. That explanation is the text. There is no separate public voice. Words like profile, post, summary or listing decide the length and the point of view of the text. They never decide how the sentences sound.

## The process

### 1. Read the real source

Read the source of the subject before writing anything. That means the product itself, its documentation, the job posting, the records of what was done, or the notes the author wrote while doing it. A page, a case study or an earlier summary is a compressed copy of the source and carries its gaps. The author's remarks in conversation are context for understanding the subject. They are not the content of the text. Write only what could be explained again without looking it up, because text turns vague exactly where knowledge is missing.

### 2. Explain it to the author first

Picture the author asking "What is this, and why does it exist?" and answer in chat, in plain paragraphs. Open each part with one plain statement of what the thing does. Then explain how it works and what that gives the reader. Name the actual feature, the actual number and one example made for this text. Show this explanation before any layout, component or post format exists.

### 3. Adapt by cutting only

When the author approves the explanation, fit it to the target by shortening it and by changing the point of view where needed. The approved wording stays. No new sentences are written in a different voice.

### 4. Test every sentence

Check each sentence with three questions before the text is shown.

- Would I say this sentence to the author across a table? A sentence that sounds strange out loud is rewritten.
- Does it carry a fact, such as a feature, a number, an example or a result? A sentence that carries none is cut.
- Could anyone else say the same sentence about their own subject? If yes, it says nothing about this subject, and it goes.

### 5. Run the checker last

Run `scripts/voice_check.py` on the finished text. Pass the explanation with `--explanation` so that every number and name in the text is traced to it. Pass the phrases the author has rejected so far with `--rejected`. The checker confirms that no banned pattern is present. It cannot turn a text written to a format into a text written to a person.

### 6. After a rejection, state what was understood

When the author rejects a text, say in your own words what the objection was and name the rule that the text broke. Then start again from the source. The rewrite never edits the rejected wording, because the rejected wording carries the mistake.

## The two messages

The method has two messages, in this order, and they are never merged. The first message is the explanation to the author in chat. The second message, sent after approval, is the text, cut from the explanation. A sentence that appears in the text and not in the explanation is a defect, because it was written to the format and not to a person. If a new sentence seems necessary, it goes into the explanation first and waits for approval there.

The explanation step can be turned off, and it is on by default. For one text, the author says "just write it" or "skip the explanation", and "explain first" turns it back on. For a voice, `"explainFirst": false` in `voices/<name>/hook.json` turns it off, and the environment variable `WRITE_LIKE_ME_EXPLAIN` set to `off` or `on` wins over that file. With the step off, the text is written directly from the request and the real source. The other rules stay. Nothing is added that the request or the source did not contain, and the checker runs before the text is shown, without `--explanation`.

## Moves that are never allowed

- Slogans, taglines and any sentence that sounds like an advert.
- Stacking features one after another instead of explaining how the thing works.
- Defining something by what it is not or by what it does not have.
- Compressed antithesis, the shape "X, not Y", in a sentence, a heading or a label.
- Benefit tails, which are clauses at the end of a sentence that describe what the reader will gain.
- Abstract ranges that the reader cannot picture, such as a system that "takes work from a first thought to a finished result".
- A closing caveat, a disclaimer, a "one thing to note" paragraph or a limitation paragraph after the text or after an answer. A caveat that would change the author's decision is the answer and goes first. Any other caveat goes.
- Anything the request, the source or the approved explanation did not contain, such as a company name, a number, a product name or a claim.
- A phrase the author objected to in an earlier draft, even when it comes back reworded.
- The author's dictated fragments copied in order. When the author dictates in pieces, the text is a rewrite in the register, never a transcript.

## Working with the author

The method covers the writing. These rules cover the work around it.

- Work on one piece at a time. A section, a field, a title or a single sentence is the unit. Show only that piece while it is being worked on. When the author asks for the full text, show everything already decided and leave out everything that is not.
- The author's text is the base. When the author quotes a text back and names a problem, change only what was named and keep the rest word for word. A named change is the only change.
- A question gets an answer and nothing else. No draft, no edit and no action accompanies it. A yes or no question is answered with yes or no first.
- A status question asked during work on one piece is about that piece. Answer for that piece only.
- Read how the thing is actually used before writing a demo or a description of it. Its records, logs and real inputs show what the thing does in practice, and an invented usage reads as invented.
- Review the draft against every correction made so far before showing it. The author should never have to point out a mistake that was already pointed out.

## The same content, written both ways

The pair below is made up. It describes an invented invoicing program.

**Written to the format**

```
Invoicing, simplified.
Fast, accurate and effortless billing for modern tradespeople, so you can focus on the work.
```

**Written to a person**

```
Tallyman is a small invoicing program for carpenters who work alone. At the end of a job the carpenter types the hours and the materials into one screen. Tallyman fills in the client's address from the last invoice, adds the materials at the price the carpenter paid, and produces a PDF that the carpenter sends from their own email. A job with ten hours and one delivery of lumber takes about two minutes to bill.
```

The second version is longer and nobody has to guess what it means. It says what the program does and how, and it gives one example. The first version could describe any invoicing program, which is the sign that it was written to a format.
