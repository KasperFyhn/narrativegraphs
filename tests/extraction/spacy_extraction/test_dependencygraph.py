from narrativegraphs.nlp.extraction.common import SpanAnnotation, Triplet
from narrativegraphs.nlp.extraction.spacy.dependencygraph import (
    DependencyGraphExtractor,
)
from tests.extraction.common import ExtractorTest


class TestDependencyGraphExtractor(ExtractorTest):
    @classmethod
    def setUpClass(cls):
        cls.extractor = DependencyGraphExtractor(
            noun_chunks=True  # allow all noun chunks
        )

    def test_active_voice(self):
        text = "John hit the ball."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="John", start_char=0, end_char=4),
                pred=SpanAnnotation(text="hit", start_char=5, end_char=8),
                obj=SpanAnnotation(text="the ball", start_char=9, end_char=17),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_active_voice_with_adjuncts(self):
        text = "The dog chased the cat quickly in the barn."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="The dog", start_char=0, end_char=7),
                pred=SpanAnnotation(text="chased", start_char=8, end_char=14),
                obj=SpanAnnotation(text="the cat", start_char=15, end_char=22),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_prepositional_object(self):
        text = "The dog looked at the sky"
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="The dog", start_char=0, end_char=7),
                pred=SpanAnnotation(text="looked", start_char=8, end_char=14),
                obj=SpanAnnotation(text="the sky", start_char=18, end_char=25),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_copula_verb_attribute(self):
        text = "Pam is a doctor."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="Pam", start_char=0, end_char=3),
                pred=SpanAnnotation(text="is", start_char=4, end_char=6),
                obj=SpanAnnotation(text="a doctor", start_char=7, end_char=15),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_xcomp_verb_object(self):
        text = "He likes to read books."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            # Triplet(
            #     subj=TripletPart(text="He", start_char=0, end_char=2),
            #     pred=TripletPart(text="likes to read", start_char=3, end_char=16),
            #     # 'likes' (3-8), 'to' (9-11), 'read' (12-16)
            #     obj=TripletPart(text="books", start_char=17, end_char=22)
            # )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_passive_voice_with_agent(self):
        text = "The book was read by Mary."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(
                    text="Mary", start_char=21, end_char=25
                ),  # Swapped subject (agent)
                pred=SpanAnnotation(
                    text="read", start_char=13, end_char=17
                ),  # 'was' (9-12), 'read' (13-17)
                obj=SpanAnnotation(
                    text="The book", start_char=0, end_char=8
                ),  # Swapped object (grammatical subject)
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_copular_verb_adjective(self):
        text = "The car is red."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="The car", start_char=0, end_char=7),
                pred=SpanAnnotation(text="is", start_char=8, end_char=10),
                obj=SpanAnnotation(text="red", start_char=11, end_char=14),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_ditransitive_verb(self):
        text = "The boy gave his friend a present."
        triplets = self.extractor.extract(text)

        # This case is tricky as the current logic only picks one object.
        # It will likely pick 'a present' as dobj.
        expected_triplets = [
            Triplet(
                subj=SpanAnnotation(text="The boy", start_char=0, end_char=7),
                pred=SpanAnnotation(text="gave", start_char=8, end_char=12),
                obj=SpanAnnotation(text="a present", start_char=24, end_char=33),
            )
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_multiple_sentences(self):
        text = "John hit the ball. Birds fly fast. The dog chased the cat quickly."
        triplets = self.extractor.extract(text)

        expected_triplets = [
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
        ]
        self.assert_triplets_equal(expected_triplets, triplets)

    def test_intransitive_verb(self):
        text = "Birds fly."
        triplets = self.extractor.extract(text)
        self.assertEqual(len(triplets), 0)

    def test_no_verb_sentence(self):
        text = "A beautiful day."
        triplets = self.extractor.extract(text)
        self.assertEqual(len(triplets), 0)

    def test_pronoun_subject(self):
        text = "He saw the dog."
        triplets = self.extractor.extract(text)
        self.assertEqual(len(triplets), 0)

    def test_pronoun_object(self):
        text = "The dog saw him."
        triplets = self.extractor.extract(text)
        self.assertEqual(len(triplets), 0)
