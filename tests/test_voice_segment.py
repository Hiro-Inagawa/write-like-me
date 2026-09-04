import unittest
from voice_segment import segment, sentences_of


DRAFT = """---
title: x
---
# Heading — with dash

Prose one. Prose two continues
on a second line.

- bullet; with semicolon
| a | b |

```
code — ignored
```

Last paragraph.
"""


class SegmentTests(unittest.TestCase):
    def test_kinds_and_line_numbers(self):
        segs = segment(DRAFT)
        kinds = [(s.kind, s.line) for s in segs if s.kind not in ("blank", "code")]
        self.assertEqual(kinds[0], ("heading", 4))
        self.assertEqual(kinds[1], ("prose", 6))
        self.assertEqual(kinds[2], ("bullet", 9))
        self.assertEqual(kinds[3], ("table", 10))
        self.assertEqual(kinds[4], ("prose", 16))

    def test_prose_paragraph_is_joined(self):
        segs = [s for s in segment(DRAFT) if s.kind == "prose"]
        self.assertEqual(segs[0].text, "Prose one. Prose two continues on a second line.")

    def test_frontmatter_and_code_are_not_prose(self):
        texts = [s.text for s in segment(DRAFT) if s.kind in ("prose", "bullet", "heading")]
        self.assertFalse(any("title: x" in t for t in texts))
        self.assertFalse(any("code — ignored" in t for t in texts))

    def test_inline_code_and_links_are_normalized(self):
        segs = segment("Use `foo — bar` and [text](http://x) here.")
        self.assertEqual(segs[0].text, "Use code and text here.")

    def test_sentences(self):
        self.assertEqual(sentences_of("One here. Two here! Three?"), ["One here.", "Two here!", "Three?"])


if __name__ == "__main__":
    unittest.main()
