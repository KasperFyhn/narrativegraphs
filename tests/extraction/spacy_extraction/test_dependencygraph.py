import unittest

from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.triplets.common import Triplet
from narrativegraphs.nlp.triplets.spacy.dependencygraph import (
    DependencyGraphExtractor,
    EntityPairDependencyExtractor,
)
from tests.extraction.common import ExtractorTest

# ----------------------------------------------------------------------
# Shared test cases
# ----------------------------------------------------------------------


class _CommonExtractionTests(ExtractorTest):
    """Abstract base of test cases expected to pass for any compatible extractor.

    Concrete subclasses must set ``cls.extractor`` in ``setUpClass``.
    This class is skipped when run directly so the test runner does not
    attempt to execute it without an extractor being configured.
    """

    @classmethod
    def setUpClass(cls):
        if cls is _CommonExtractionTests:
            raise unittest.SkipTest("abstract base")

    def test_active_voice(self):
        triplets = self.extractor.extract("John hit the ball.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="John", start_char=0, end_char=4),
                    pred=SpanAnnotation(text="hit", start_char=5, end_char=8),
                    obj=SpanAnnotation(text="the ball", start_char=9, end_char=17),
                )
            ],
            triplets,
        )

    def test_passive_voice_with_agent(self):
        triplets = self.extractor.extract("The book was read by Mary.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="Mary", start_char=21, end_char=25),
                    pred=SpanAnnotation(text="read", start_char=13, end_char=17),
                    obj=SpanAnnotation(text="The book", start_char=0, end_char=8),
                )
            ],
            triplets,
        )

    def test_copula_verb_attribute(self):
        triplets = self.extractor.extract("Pam is a doctor.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="Pam", start_char=0, end_char=3),
                    pred=SpanAnnotation(text="is", start_char=4, end_char=6),
                    obj=SpanAnnotation(text="a doctor", start_char=7, end_char=15),
                )
            ],
            triplets,
        )

    def test_conjunct_verbs(self):
        """Subject is shared across verbs joined by a conjunction."""
        triplets = self.extractor.extract("Alice ate the apple and drank the wine.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="Alice", start_char=0, end_char=5),
                    pred=SpanAnnotation(text="ate", start_char=6, end_char=9),
                    obj=SpanAnnotation(text="the apple", start_char=10, end_char=19),
                ),
                Triplet(
                    subj=SpanAnnotation(text="Alice", start_char=0, end_char=5),
                    pred=SpanAnnotation(text="drank", start_char=24, end_char=29),
                    obj=SpanAnnotation(text="the wine", start_char=30, end_char=38),
                ),
            ],
            triplets,
        )

    def test_np_prepositional_relation(self):
        """Prepositional phrase on a noun chunk produces its own triplet."""
        triplets = self.extractor.extract("Alice from Paris visited London.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="Alice", start_char=0, end_char=5),
                    pred=SpanAnnotation(text="from", start_char=6, end_char=10),
                    obj=SpanAnnotation(text="Paris", start_char=11, end_char=16),
                ),
                Triplet(
                    subj=SpanAnnotation(text="Alice", start_char=0, end_char=5),
                    pred=SpanAnnotation(text="visited", start_char=17, end_char=24),
                    obj=SpanAnnotation(text="London", start_char=25, end_char=31),
                ),
            ],
            triplets,
        )

    def test_xcomp_verb_object(self):
        # xcomp constructions are not extracted — only direct verb relations.
        self.assertEqual(len(self.extractor.extract("He likes to read books.")), 0)

    def test_adjective_complement_not_extracted(self):
        """ADJ tokens are not noun chunks so acomp produces no triplet."""
        self.assertEqual(len(self.extractor.extract("The car is red.")), 0)

    def test_ditransitive_verb(self):
        # Only the direct object is picked up; indirect object (dative) is skipped.
        triplets = self.extractor.extract("The boy gave his friend a present.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="The boy", start_char=0, end_char=7),
                    pred=SpanAnnotation(text="gave", start_char=8, end_char=12),
                    obj=SpanAnnotation(text="a present", start_char=24, end_char=33),
                )
            ],
            triplets,
        )

    def test_multiple_sentences(self):
        text = "John hit the ball. Birds fly fast. The dog chased the cat quickly."
        triplets = self.extractor.extract(text)
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="John", start_char=0, end_char=4),
                    pred=SpanAnnotation(text="hit", start_char=5, end_char=8),
                    obj=SpanAnnotation(text="the ball", start_char=9, end_char=17),
                ),
                Triplet(
                    subj=SpanAnnotation(text="The dog", start_char=35, end_char=42),
                    pred=SpanAnnotation(text="chased", start_char=43, end_char=49),
                    obj=SpanAnnotation(text="the cat", start_char=50, end_char=57),
                ),
            ],
            triplets,
        )

    def test_intransitive_verb(self):
        self.assertEqual(len(self.extractor.extract("Birds fly.")), 0)

    def test_pronoun_subject(self):
        self.assertEqual(len(self.extractor.extract("He saw the dog.")), 0)

    def test_pronoun_object(self):
        self.assertEqual(len(self.extractor.extract("The dog saw him.")), 0)


# ----------------------------------------------------------------------
# DependencyGraphExtractor
# ----------------------------------------------------------------------


class TestDependencyGraphExtractor(_CommonExtractionTests):
    @classmethod
    def setUpClass(cls):
        cls.extractor = DependencyGraphExtractor(
            noun_chunks=True  # allow all noun chunks regardless of length
        )

    def test_prepositional_object(self):
        triplets = self.extractor.extract("The dog looked at the sky")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="The dog", start_char=0, end_char=7),
                    pred=SpanAnnotation(text="looked", start_char=8, end_char=14),
                    obj=SpanAnnotation(text="the sky", start_char=18, end_char=25),
                )
            ],
            triplets,
        )

    def test_active_voice_with_adjuncts(self):
        triplets = self.extractor.extract("The dog chased the cat quickly in the barn.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="The dog", start_char=0, end_char=7),
                    pred=SpanAnnotation(text="chased", start_char=8, end_char=14),
                    obj=SpanAnnotation(text="the cat", start_char=15, end_char=22),
                )
            ],
            triplets,
        )

    def test_no_verb_sentence(self):
        self.assertEqual(len(self.extractor.extract("A beautiful day.")), 0)

    def test_conjunct_verbs_disabled(self):
        extractor = DependencyGraphExtractor(noun_chunks=True, conjunct_verbs=False)
        triplets = extractor.extract("Alice ate the apple and drank the wine.")
        self.assertEqual(len(triplets), 1)
        self.assertEqual(triplets[0].pred.text, "ate")

    def test_prepositional_relations_disabled(self):
        extractor = DependencyGraphExtractor(
            noun_chunks=True, prepositional_relations=False
        )
        triplets = extractor.extract("Alice from Paris visited London.")
        self.assertEqual(len(triplets), 1)
        self.assertEqual(triplets[0].pred.text, "visited")


# ----------------------------------------------------------------------
# EntityPairExtractor
# ----------------------------------------------------------------------


class TestEntityPairExtractor(_CommonExtractionTests):
    @classmethod
    def setUpClass(cls):
        cls.extractor = EntityPairDependencyExtractor(
            noun_chunks=True  # allow all noun chunks regardless of length
        )

    def test_prepositional_object(self):
        # EPE uses compound predicate "verb prep" for sv_prep_o
        triplets = self.extractor.extract("The dog looked at the sky")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="The dog", start_char=0, end_char=7),
                    pred=SpanAnnotation(text="looked at", start_char=8, end_char=17),
                    obj=SpanAnnotation(text="the sky", start_char=18, end_char=25),
                )
            ],
            triplets,
        )

    def test_active_voice_with_adjuncts(self):
        # EPE emits both svo and sv_prep_o triplets
        triplets = self.extractor.extract("The dog chased the cat quickly in the barn.")
        self.assert_triplets_equal(
            [
                Triplet(
                    subj=SpanAnnotation(text="The dog", start_char=0, end_char=7),
                    pred=SpanAnnotation(text="chased", start_char=8, end_char=14),
                    obj=SpanAnnotation(text="the cat", start_char=15, end_char=22),
                ),
                Triplet(
                    subj=SpanAnnotation(text="The dog", start_char=0, end_char=7),
                    pred=SpanAnnotation(text="chased in", start_char=8, end_char=33),
                    obj=SpanAnnotation(text="the barn", start_char=34, end_char=42),
                ),
            ],
            triplets,
        )

    def test_max_sentence_length_guard(self):
        """Sentences exceeding the token limit are skipped entirely."""
        extractor = EntityPairDependencyExtractor(
            noun_chunks=True, max_sentence_length=3
        )
        self.assertEqual(len(extractor.extract("John hit the ball.")), 0)

    def test_max_entity_distance_guard(self):
        """Entity pairs whose roots are too far apart in token space are skipped."""
        # John (i=0) and ball (i=3): distance 3 exceeds limit of 1
        extractor = EntityPairDependencyExtractor(
            noun_chunks=True, max_entity_distance=1
        )
        self.assertEqual(len(extractor.extract("John hit the ball.")), 0)

    def test_custom_path_patterns(self):
        """An empty pattern set produces no triplets regardless of sentence."""
        extractor = EntityPairDependencyExtractor(noun_chunks=True, path_patterns=())
        self.assertEqual(len(extractor.extract("John hit the ball.")), 0)
