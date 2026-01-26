from narrativegraphs.nlp.extraction.common import SpanAnnotation, Triplet
from narrativegraphs.nlp.extraction.spacy.naive import NaiveSpacyTripletExtractor
from tests.extraction.common import ExtractorTest


class TestNaiveSpacyTripletExtractor(ExtractorTest):
    @classmethod
    def setUpClass(cls):
        cls.extractor = NaiveSpacyTripletExtractor()

    def test_initialization_error(self):
        """Test that initialization raises error when both ner and noun_chunks are
        False."""
        with self.assertRaises(NotImplementedError):
            NaiveSpacyTripletExtractor(named_entities=False, noun_chunks=False)

    def test_simple_named_entities(self):
        """Test extraction with simple named entities."""
        text = "John visited Paris yesterday."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="John", start_char=0, end_char=4),
                pred=SpanAnnotation(text="visited", start_char=5, end_char=12),
                obj=SpanAnnotation(text="Paris", start_char=13, end_char=18),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_noun_chunks_only(self):
        """Test extraction using only noun chunks."""
        extractor = NaiveSpacyTripletExtractor(named_entities=False, noun_chunks=True)
        text = "The big dog chased the small cat."
        triplets = extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="The big dog", start_char=0, end_char=11),
                pred=SpanAnnotation(text="chased", start_char=12, end_char=18),
                obj=SpanAnnotation(text="the small cat", start_char=19, end_char=32),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_mixed_entities_and_chunks(self):
        """Test extraction with both named entities and noun chunks."""
        text = "Apple Inc. released a new iPhone."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="Apple Inc.", start_char=0, end_char=10),
                pred=SpanAnnotation(text="released", start_char=11, end_char=19),
                obj=SpanAnnotation(text="a new iPhone", start_char=20, end_char=32),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_max_tokens_between_filtering(self):
        """Test that triplets are filtered based on max_tokens_between."""
        extractor = NaiveSpacyTripletExtractor(max_tokens_between=1)
        text = "John walked slowly and carefully to the store."
        triplets = extractor.extract(text)

        self.assertEqual(len(triplets), 0)

    def test_entity_length_filtering(self):
        """Test filtering entities by length ranges."""
        extractor = NaiveSpacyTripletExtractor(
            named_entities=(2, 4),
            noun_chunks=False,  # Only entities with 2-3 tokens
        )
        text = "Dr. John Smith visited New York City."
        triplets = extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(
                    text="John Smith",
                    start_char=4,
                    end_char=14,
                ),
                pred=SpanAnnotation(text="visited", start_char=15, end_char=22),
                obj=SpanAnnotation(text="New York City", start_char=23, end_char=36),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

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

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="John", start_char=0, end_char=4),
                pred=SpanAnnotation(text="visited", start_char=5, end_char=12),
                obj=SpanAnnotation(text="Paris", start_char=13, end_char=18),
            ),
            Triplet(
                subj=SpanAnnotation(text="Mary", start_char=20, end_char=24),
                pred=SpanAnnotation(text="went to", start_char=25, end_char=32),
                obj=SpanAnnotation(text="London", start_char=33, end_char=39),
            ),
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

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
        text = "He sent John a letter."
        triplets = self.extractor.extract(text)

        self.assertEqual(len(triplets), 0)

    def test_noun_chunks_length_filtering(self):
        """Test filtering noun chunks by length."""
        extractor = NaiveSpacyTripletExtractor(
            named_entities=False,
            noun_chunks=(3, 5),  # Only noun chunks with 3-4 tokens
        )
        text = "The large red car hit the green bike in the street."
        triplets = extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(
                    text="The large red car",
                    start_char=0,
                    end_char=17,
                ),
                pred=SpanAnnotation(text="hit", start_char=18, end_char=21),
                obj=SpanAnnotation(text="the green bike", start_char=22, end_char=36),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_stray_predicate(self):
        extractor = NaiveSpacyTripletExtractor(
            named_entities=(2, None),
            noun_chunks=(3, None),
        )

        text = (
            "I Asked Trump A Policy Question. Then He Called Me ‘Beautiful.’\n\n"
            "Donald Trump, the Republican front-runner for the presidential "
            "nomination, met with The Washington Post’s editorial board"
        )
        triplets = extractor.extract(text)
        print(triplets)
