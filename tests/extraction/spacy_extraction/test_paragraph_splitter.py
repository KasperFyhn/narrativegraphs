import unittest

from tests.extraction.spacy_extraction.common import DummySpacyTripletExtractor


class TestSpacyParagraphSplitter(unittest.TestCase):
    def test_splits_on_double_line_break(self) -> None:
        extractor = DummySpacyTripletExtractor(split_sentence_on_double_line_break=True)
        nlp = extractor.nlp

        text = "First paragraph\n\nSecond paragraph"

        doc = nlp(text)

        self.assertEqual(2, len(list(doc.sents)))
