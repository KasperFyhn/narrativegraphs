"""Recording every mention of an entity, not only the ones in a relation."""

import unittest

from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.common.mentions import (
    expand_to_all_occurrences,
    find_all_occurrences,
)

TEXT = "Frodo carried the ring. Later Frodo rested while the ring glowed."


def span(text, start, end):
    return SpanAnnotation(text=text[start:end], start_char=start, end_char=end)


class TestFindAllOccurrences(unittest.TestCase):
    def test_finds_every_occurrence(self):
        self.assertEqual([(0, 5), (30, 35)], find_all_occurrences(TEXT, "Frodo"))

    def test_respects_word_boundaries(self):
        text = "The ring was ringing and the wringer broke."

        self.assertEqual([(4, 8)], find_all_occurrences(text, "ring"))

    def test_matches_case_insensitively(self):
        text = "The Ring. the ring. THE RING."

        self.assertEqual(3, len(find_all_occurrences(text, "the ring")))

    def test_tolerates_differing_whitespace(self):
        text = "the dark\nlord came. the dark lord left."

        self.assertEqual(2, len(find_all_occurrences(text, "the dark lord")))

    def test_punctuation_bounded_surfaces_still_match(self):
        """A surface with no word characters gets no word-boundary anchors."""
        self.assertEqual([(22, 23), (64, 65)], find_all_occurrences(TEXT, "."))

    def test_empty_surface_finds_nothing(self):
        self.assertEqual([], find_all_occurrences(TEXT, "   "))


class TestExpandToAllOccurrences(unittest.TestCase):
    def test_keeps_every_original_span_untouched(self):
        """Population looks triplets up by exact span, so these must survive."""
        originals = [span(TEXT, 0, 5), span(TEXT, 14, 22)]

        expanded = expand_to_all_occurrences(TEXT, originals)

        for original in originals:
            self.assertIn(original, expanded)

    def test_adds_the_other_mentions(self):
        expanded = expand_to_all_occurrences(TEXT, [span(TEXT, 0, 5)])

        self.assertEqual(
            [(0, 5), (30, 35)], sorted((e.start_char, e.end_char) for e in expanded)
        )

    def test_added_mentions_never_overlap(self):
        expanded = expand_to_all_occurrences(
            TEXT, [span(TEXT, 14, 22), span(TEXT, 0, 5)]
        )

        spans = sorted((e.start_char, e.end_char) for e in expanded)
        for current, following in zip(spans, spans[1:]):
            self.assertLessEqual(current[1], following[0])

    def test_longer_surfaces_claim_their_text_first(self):
        # "the ring" and "ring" compete; the longer one should win.
        expanded = expand_to_all_occurrences(
            TEXT, [span(TEXT, 14, 22), span(TEXT, 18, 22)]
        )

        texts = sorted(e.text.lower() for e in expanded)
        self.assertEqual(["ring", "the ring", "the ring"], texts)

    def test_no_entities_expands_to_nothing(self):
        self.assertEqual([], expand_to_all_occurrences(TEXT, []))


if __name__ == "__main__":
    unittest.main()
