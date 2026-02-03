import unittest

from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.entities.spacy import SpacyEntityExtractor


class TestSpacyEntityExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = SpacyEntityExtractor()

    def assert_entity_equal(self, expected: SpanAnnotation, actual: SpanAnnotation):
        """Custom assertion to compare SpanAnnotation objects."""
        errors = []
        for field_name in ["text", "start_char", "end_char"]:
            expected_field = getattr(expected, field_name)
            actual_field = getattr(actual, field_name)
            if expected_field != actual_field:
                errors.append(
                    f"{field_name} mismatch. Expected: {expected_field}, "
                    f"Got: {actual_field}"
                )
        self.assertTrue(len(errors) == 0, "\n".join(errors))

    def assert_entities_equal(
        self, expected: list[SpanAnnotation], actual: list[SpanAnnotation]
    ):
        self.assertEqual(
            len(expected),
            len(actual),
            f"Expected {len(expected)} entities, got {len(actual)}: "
            f"{[e.text for e in actual]}",
        )
        for e, a in zip(expected, actual):
            self.assert_entity_equal(e, a)

    def test_initialization_error(self):
        """Test that initialization raises error when both ner and noun_chunks are
        False."""
        with self.assertRaises(ValueError):
            SpacyEntityExtractor(named_entities=False, noun_chunks=False)

    def test_simple_named_entities(self):
        """Test extraction with simple named entities."""
        text = "Alice met Bob in Paris."
        entities = self.extractor.extract(text)

        expected = [
            SpanAnnotation(text="Alice", start_char=0, end_char=5),
            SpanAnnotation(text="Bob", start_char=10, end_char=13),
            SpanAnnotation(text="Paris", start_char=17, end_char=22),
        ]
        self.assert_entities_equal(expected, entities)

    def test_noun_chunks_only(self):
        """Test extraction using only noun chunks."""
        extractor = SpacyEntityExtractor(named_entities=False, noun_chunks=True)
        text = "The big dog chased the small cat."
        entities = extractor.extract(text)

        expected = [
            SpanAnnotation(text="The big dog", start_char=0, end_char=11),
            SpanAnnotation(text="the small cat", start_char=19, end_char=32),
        ]
        self.assert_entities_equal(expected, entities)

    def test_ner_priority_over_noun_chunks(self):
        """Test that NER entities take priority over overlapping noun chunks."""
        text = "Apple Inc. released a new iPhone."
        entities = self.extractor.extract(text)

        # Apple Inc. should be from NER, not just "Apple" as noun chunk
        entity_texts = [e.text for e in entities]
        self.assertIn("Apple Inc.", entity_texts)

    def test_no_overlapping_entities(self):
        """Test that extracted entities don't overlap."""
        text = "The New York City mayor visited Paris, France yesterday."
        entities = self.extractor.extract(text)

        # Check no overlaps
        for i, e1 in enumerate(entities):
            for e2 in entities[i + 1 :]:
                overlap = not (
                    e1.end_char <= e2.start_char or e2.end_char <= e1.start_char
                )
                self.assertFalse(
                    overlap,
                    f"Entities overlap: '{e1.text}' ({e1.start_char}-{e1.end_char}) "
                    f"and '{e2.text}' ({e2.start_char}-{e2.end_char})",
                )

    def test_remove_pronouns(self):
        """Test that pronouns are filtered out by default."""
        extractor = SpacyEntityExtractor(remove_pronouns=True)
        text = "He visited Paris. She went to London."
        entities = extractor.extract(text)

        entity_texts = [e.text for e in entities]
        self.assertNotIn("He", entity_texts)
        self.assertNotIn("She", entity_texts)
        self.assertIn("Paris", entity_texts)
        self.assertIn("London", entity_texts)

    def test_keep_pronouns(self):
        """Test that pronouns can be kept when remove_pronouns=False."""
        extractor = SpacyEntityExtractor(remove_pronouns=False, noun_chunks=True)
        text = "He visited Paris."
        entities = extractor.extract(text)

        entity_texts = [e.text for e in entities]
        self.assertIn("He", entity_texts)

    def test_entity_length_filtering(self):
        """Test filtering entities by length ranges."""
        extractor = SpacyEntityExtractor(
            named_entities=(2, 4),  # Only entities with 2-3 tokens
            noun_chunks=False,
        )
        text = "Dr. John Smith visited New York City."
        entities = extractor.extract(text)

        # Should include multi-token entities within range
        entity_texts = [e.text for e in entities]
        # Single token entities should be excluded
        self.assertNotIn("Dr.", entity_texts)

    def test_multiple_sentences(self):
        """Test extraction from multiple sentences."""
        text = "Alice visited Paris. Bob went to London. Eve stayed in Tokyo."
        entities = self.extractor.extract(text)

        entity_texts = [e.text for e in entities]
        self.assertIn("Alice", entity_texts)
        self.assertIn("Paris", entity_texts)
        self.assertIn("Bob", entity_texts)
        self.assertIn("London", entity_texts)
        # At least some entities from the third sentence
        self.assertTrue(
            "Eve" in entity_texts or "Tokyo" in entity_texts,
            f"Expected Eve or Tokyo in {entity_texts}",
        )

    def test_no_valid_entities(self):
        """Test with text that has no named entities."""
        extractor = SpacyEntityExtractor(named_entities=True, noun_chunks=False)
        text = "Running quickly is good."
        entities = extractor.extract(text)

        # Should return empty list when no named entities found
        self.assertEqual(len(entities), 0)

    def test_batch_extract(self):
        """Test batch extraction from multiple documents."""
        texts = [
            "Alice met Bob in Paris.",
            "Carol visited London with Dave.",
            "Eve and Frank went to Tokyo.",
        ]

        results = list(self.extractor.batch_extract(texts, n_cpu=1))

        self.assertEqual(len(results), 3)

        # First document
        doc1_texts = [e.text for e in results[0]]
        self.assertIn("Alice", doc1_texts)
        self.assertIn("Bob", doc1_texts)
        self.assertIn("Paris", doc1_texts)

        # Second document
        doc2_texts = [e.text for e in results[1]]
        self.assertIn("Carol", doc2_texts)
        self.assertIn("London", doc2_texts)

        # Third document
        doc3_texts = [e.text for e in results[2]]
        self.assertIn("Tokyo", doc3_texts)

    def test_batch_extract_preserves_order(self):
        """Test that batch extraction preserves document order."""
        texts = [
            "Document about Paris.",
            "Document about London.",
            "Document about Tokyo.",
        ]

        results = list(self.extractor.batch_extract(texts, n_cpu=1))

        self.assertEqual(len(results), 3)
        self.assertIn("Paris", [e.text for e in results[0]])
        self.assertIn("London", [e.text for e in results[1]])
        self.assertIn("Tokyo", [e.text for e in results[2]])

    def test_filters_cardinal_ordinal(self):
        """Test that CARDINAL and ORDINAL entity types are filtered out."""
        text = "The first 100 people visited Paris."
        entities = self.extractor.extract(text)

        entity_texts = [e.text for e in entities]
        # Numbers and ordinals should be filtered
        self.assertNotIn("first", entity_texts)
        self.assertNotIn("100", entity_texts)
        # But location should remain
        self.assertIn("Paris", entity_texts)

    def test_entities_sorted_by_position(self):
        """Test that entities are returned sorted by position."""
        text = "Paris is where Alice met Bob."
        entities = self.extractor.extract(text)

        # Entities should be sorted by start_char
        for i in range(len(entities) - 1):
            self.assertLessEqual(
                entities[i].start_char,
                entities[i + 1].start_char,
                f"Entities not sorted: {entities[i].text} at {entities[i].start_char} "
                f"comes before {entities[i + 1].text} at {entities[i + 1].start_char}",
            )


if __name__ == "__main__":
    unittest.main()
