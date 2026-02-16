import unittest

from narrativegraphs.dto.common import TextContext


class TestTextContextOverlaps(unittest.TestCase):
    def test_overlapping_contexts(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="world!", doc_offset=6)
        self.assertTrue(tc1.overlaps_or_adjacent(tc2))
        self.assertTrue(tc2.overlaps_or_adjacent(tc1))

    def test_non_overlapping_contexts(self):
        tc1 = TextContext(doc_id=1, text="hello", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="world", doc_offset=10)
        self.assertFalse(tc1.overlaps_or_adjacent(tc2))
        self.assertFalse(tc2.overlaps_or_adjacent(tc1))

    def test_adjacent_contexts_overlap(self):
        tc1 = TextContext(doc_id=1, text="hello", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="world", doc_offset=5)
        self.assertTrue(tc1.overlaps_or_adjacent(tc2))

    def test_different_doc_ids(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=0)
        tc2 = TextContext(doc_id=2, text="hello world", doc_offset=0)
        self.assertFalse(tc1.overlaps_or_adjacent(tc2))

    def test_one_contained_in_other(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="lo wo", doc_offset=3)
        self.assertTrue(tc1.overlaps_or_adjacent(tc2))
        self.assertTrue(tc2.overlaps_or_adjacent(tc1))

    def test_identical_contexts(self):
        tc1 = TextContext(doc_id=1, text="hello", doc_offset=5)
        tc2 = TextContext(doc_id=1, text="hello", doc_offset=5)
        self.assertTrue(tc1.overlaps_or_adjacent(tc2))

    def test_overlapping_with_non_zero_offsets(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=100)
        tc2 = TextContext(doc_id=1, text="world!", doc_offset=106)
        self.assertTrue(tc1.overlaps_or_adjacent(tc2))


class TestTextContextCombine(unittest.TestCase):
    def test_combine_overlapping_from_zero(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="world!", doc_offset=6)
        result = tc1.combine(tc2)
        self.assertEqual(result.text, "hello world!")
        self.assertEqual(result.doc_offset, 0)

    def test_combine_overlapping_reversed(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="world!", doc_offset=6)
        result = tc2.combine(tc1)
        self.assertEqual(result.text, "hello world!")
        self.assertEqual(result.doc_offset, 0)

    def test_combine_with_non_zero_offsets(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=100)
        tc2 = TextContext(doc_id=1, text="world!", doc_offset=106)
        result = tc1.combine(tc2)
        self.assertEqual(result.text, "hello world!")
        self.assertEqual(result.doc_offset, 100)

    def test_combine_with_non_zero_offsets_reversed(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=100)
        tc2 = TextContext(doc_id=1, text="world!", doc_offset=106)
        result = tc2.combine(tc1)
        self.assertEqual(result.text, "hello world!")
        self.assertEqual(result.doc_offset, 100)

    def test_combine_contained_context(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="lo wo", doc_offset=3)
        result = tc1.combine(tc2)
        self.assertEqual(result.text, "hello world")
        self.assertEqual(result.doc_offset, 0)

    def test_combine_identical_contexts(self):
        tc1 = TextContext(doc_id=1, text="hello", doc_offset=5)
        tc2 = TextContext(doc_id=1, text="hello", doc_offset=5)
        result = tc1.combine(tc2)
        self.assertEqual(result.text, "hello")
        self.assertEqual(result.doc_offset, 5)

    def test_combine_non_overlapping_raises(self):
        tc1 = TextContext(doc_id=1, text="hello", doc_offset=0)
        tc2 = TextContext(doc_id=1, text="world", doc_offset=10)
        with self.assertRaises(ValueError):
            tc1.combine(tc2)

    def test_combine_different_doc_ids_raises(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=0)
        tc2 = TextContext(doc_id=2, text="world!", doc_offset=6)
        with self.assertRaises(ValueError):
            tc1.combine(tc2)

    def test_combine_mutates_self(self):
        tc1 = TextContext(doc_id=1, text="hello world", doc_offset=100)
        tc2 = TextContext(doc_id=1, text="world!", doc_offset=106)
        result = tc1.combine(tc2)
        self.assertIs(result, tc1)
        self.assertEqual(tc1.text, "hello world!")

    def test_combine_second_extends_beyond_first(self):
        tc1 = TextContext(doc_id=1, text="abc", doc_offset=50)
        tc2 = TextContext(doc_id=1, text="cdefgh", doc_offset=52)
        result = tc1.combine(tc2)
        self.assertEqual(result.text, "abcdefgh")
        self.assertEqual(result.doc_offset, 50)


class TestTextContextCombineMany(unittest.TestCase):
    def test_combine_many_overlapping(self):
        contexts = [
            TextContext(doc_id=1, text="hello ", doc_offset=0),
            TextContext(doc_id=1, text="o world", doc_offset=4),
            TextContext(doc_id=1, text="ld!", doc_offset=9),
        ]
        result = TextContext.combine_many(contexts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "hello world!")
        self.assertEqual(result[0].doc_offset, 0)

    def test_combine_many_non_overlapping(self):
        contexts = [
            TextContext(doc_id=1, text="hello", doc_offset=0),
            TextContext(doc_id=1, text="world", doc_offset=10),
        ]
        result = TextContext.combine_many(contexts)
        self.assertEqual(len(result), 2)

    def test_combine_many_different_docs(self):
        contexts = [
            TextContext(doc_id=1, text="hello world", doc_offset=0),
            TextContext(doc_id=1, text="world!", doc_offset=6),
            TextContext(doc_id=2, text="foo bar", doc_offset=0),
            TextContext(doc_id=2, text="bar baz", doc_offset=4),
        ]
        result = TextContext.combine_many(contexts)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].text, "hello world!")
        self.assertEqual(result[1].text, "foo bar baz")

    def test_combine_many_empty(self):
        result = TextContext.combine_many([])
        self.assertEqual(result, [])

    def test_combine_many_single(self):
        contexts = [TextContext(doc_id=1, text="hello", doc_offset=0)]
        result = TextContext.combine_many(contexts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "hello")

    def test_combine_many_unsorted_input(self):
        contexts = [
            TextContext(doc_id=1, text="world!", doc_offset=6),
            TextContext(doc_id=1, text="hello ", doc_offset=0),
        ]
        result = TextContext.combine_many(contexts)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "hello world!")
