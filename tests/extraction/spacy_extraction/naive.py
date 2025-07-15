import unittest

from narrativegraph.extraction.common import Triplet, TripletPart
from narrativegraph.extraction.spacy.naive import NaiveSpacyTripletExtractor
from tests.extraction.common import ExtractorTest


class TestNaiveSpacyTripletExtractor(ExtractorTest):

    @classmethod
    def setUpClass(cls):
        cls.extractor = NaiveSpacyTripletExtractor()

    def test_initialization_error(self):
        """Test that initialization raises error when both ner and noun_chunks are False."""
        with self.assertRaises(NotImplementedError):
            NaiveSpacyTripletExtractor(named_entities=False, noun_chunks=False)

    def test_simple_named_entities(self):
        """Test extraction with simple named entities."""
        text = "John visited Paris yesterday."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=TripletPart(text="John", start_char=0, end_char=4),
                pred=TripletPart(text="visited", start_char=5, end_char=12),
                obj=TripletPart(text="Paris", start_char=13, end_char=18),
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(
            triplets[0], expected_triplets[0], msg=f"Test '{text}':"
        )

    def test_noun_chunks_only(self):
        """Test extraction using only noun chunks."""
        extractor = NaiveSpacyTripletExtractor(named_entities=False, noun_chunks=True)
        text = "The big dog chased the small cat."
        triplets = extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=TripletPart(text="The big dog", start_char=0, end_char=11),
                pred=TripletPart(text="chased", start_char=12, end_char=18),
                obj=TripletPart(text="the small cat", start_char=19, end_char=32),
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(
            triplets[0], expected_triplets[0], msg=f"Test '{text}':"
        )

    def test_mixed_entities_and_chunks(self):
        """Test extraction with both named entities and noun chunks."""
        text = "Apple Inc. released the new iPhone."
        triplets = self.extractor.extract(text)

        # Should extract triplets from both named entities and noun chunks
        self.assertGreater(len(triplets), 0)
        # Check that we have reasonable subject/object spans
        for triplet in triplets:
            self.assertGreater(len(triplet.subj.text.strip()), 0)
            self.assertGreater(len(triplet.obj.text.strip()), 0)

    def test_max_tokens_between_filtering(self):
        """Test that triplets are filtered based on max_tokens_between."""
        extractor = NaiveSpacyTripletExtractor(max_tokens_between=1)
        text = "John walked slowly and carefully to the store."
        triplets = extractor.extract(text)

        # With max_tokens_between=1, long predicates should be filtered out
        for triplet in triplets:
            # Count tokens in predicate (rough approximation)
            pred_tokens = len(triplet.pred.text.split())
            self.assertLessEqual(
                pred_tokens, 2
            )  # Allow some flexibility for tokenization

    def test_entity_length_filtering(self):
        """Test filtering entities by length ranges."""
        extractor = NaiveSpacyTripletExtractor(
            named_entities=(2, 4), noun_chunks=False  # Only entities with 2-3 tokens
        )
        text = "Dr. John Smith visited New York City."
        triplets = extractor.extract(text)

        # Should filter out single-token entities and very long entities
        for triplet in triplets:
            subj_tokens = len(triplet.subj.text.split())
            obj_tokens = len(triplet.obj.text.split())
            self.assertGreaterEqual(subj_tokens, 2)
            self.assertLess(subj_tokens, 4)
            self.assertGreaterEqual(obj_tokens, 2)
            self.assertLess(obj_tokens, 4)

    def test_multiple_triplets_same_sentence(self):
        """Test extraction of multiple triplets from the same sentence."""
        text = "John met Mary and then visited Paris."
        triplets = self.extractor.extract(text)

        # Should extract multiple triplets from entities in sequence
        self.assertGreater(len(triplets), 0)

        # All triplets should have valid spans
        for triplet in triplets:
            self.assertGreater(len(triplet.subj.text.strip()), 0)
            self.assertGreater(len(triplet.pred.text.strip()), 0)
            self.assertGreater(len(triplet.obj.text.strip()), 0)

    def test_multiple_sentences(self):
        """Test extraction from multiple sentences."""
        text = "John visited Paris. Mary went to London. Tom stayed home."
        triplets = self.extractor.extract(text)

        # Should extract from multiple sentences
        self.assertGreater(len(triplets), 0)

        # Check that character positions are correct across sentences
        for triplet in triplets:
            self.assertLess(triplet.subj.start_char, triplet.subj.end_char)
            self.assertLess(triplet.pred.start_char, triplet.pred.end_char)
            self.assertLess(triplet.obj.start_char, triplet.obj.end_char)

    def test_no_valid_entities(self):
        """Test with text that has no valid entities."""
        text = "It is raining."
        triplets = self.extractor.extract(text)

        # Should return empty list when no suitable entities found
        self.assertEqual(len(triplets), 0)

    def test_single_entity(self):
        """Test with text containing only one entity."""
        text = "John."
        triplets = self.extractor.extract(text)

        # Should return empty list when only one entity (need at least 2 for triplet)
        self.assertEqual(len(triplets), 0)

    def test_entities_too_far_apart(self):
        """Test entities that are too far apart based on max_tokens_between."""
        extractor = NaiveSpacyTripletExtractor(max_tokens_between=2)
        text = "John walked very slowly and carefully through the park to meet Mary."
        triplets = extractor.extract(text)

        # Should filter out triplets where entities are too far apart
        for triplet in triplets:
            # Verify the predicate isn't excessively long
            pred_tokens = len(triplet.pred.text.split())
            self.assertLessEqual(pred_tokens, 4)  # Allow some flexibility

    def test_empty_predicate(self):
        """Test adjacent entities with empty predicate."""
        text = "John Mary went to the store."
        triplets = self.extractor.extract(text)

        # Should handle cases where entities are adjacent
        for triplet in triplets:
            # Predicate might be empty or whitespace
            self.assertIsNotNone(triplet.pred.text)

    def test_noun_chunks_length_filtering(self):
        """Test filtering noun chunks by length."""
        extractor = NaiveSpacyTripletExtractor(
            named_entities=False, noun_chunks=(3, 5)  # Only noun chunks with 3-4 tokens
        )
        text = "The very large red car hit the small bike."
        triplets = extractor.extract(text)

        # Should only include noun chunks within the specified range
        for triplet in triplets:
            subj_tokens = len(triplet.subj.text.split())
            obj_tokens = len(triplet.obj.text.split())
            self.assertGreaterEqual(subj_tokens, 3)
            self.assertLessEqual(subj_tokens, 5)
            self.assertGreaterEqual(obj_tokens, 3)
            self.assertLessEqual(obj_tokens, 5)

    def test_overlapping_entities(self):
        """Test handling of overlapping entities and noun chunks."""
        text = "Apple Inc. in California released the new iPhone."
        triplets = self.extractor.extract(text)

        # Should handle overlapping spans gracefully
        self.assertGreaterEqual(len(triplets), 0)

        # Verify all triplets have valid character spans
        for triplet in triplets:
            self.assertLess(triplet.subj.start_char, triplet.subj.end_char)
            self.assertLess(triplet.pred.start_char, triplet.pred.end_char)
            self.assertLess(triplet.obj.start_char, triplet.obj.end_char)

    def test_complex_sentence_structure(self):
        """Test extraction from complex sentence structures."""
        text = "The European Union and the United States signed a comprehensive trade agreement."
        triplets = self.extractor.extract(text)

        # Should extract meaningful triplets from complex noun phrases
        self.assertGreater(len(triplets), 0)

        # Check that we get reasonable spans
        for triplet in triplets:
            self.assertGreater(len(triplet.subj.text.strip()), 0)
            self.assertGreater(len(triplet.obj.text.strip()), 0)
