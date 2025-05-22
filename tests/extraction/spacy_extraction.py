import unittest

from narrativegraph.extraction.common import Triplet, TripletPart
from narrativegraph.extraction.spacy import DependencyGraphExtractor


class TestDependencyGraphExtractor(unittest.TestCase):
    """
    Test suite for the _extract_triplets_from_doc function.
    """

    @classmethod
    def setUpClass(cls):
        cls.extractor = DependencyGraphExtractor()

    def assertTripletEqual(self, expected: Triplet, actual: Triplet, msg: str = ""):
        """
        Custom assertion to compare Triplet NamedTuples.
        Compares text, start_char, and end_char for each part.
        """
        self.assertEqual(actual.subject.text, expected.subject.text, f"{msg} Subject text mismatch.")
        self.assertEqual(actual.subject.start_char, expected.subject.start_char, f"{msg} Subject start_char mismatch.")
        self.assertEqual(actual.subject.end_char, expected.subject.end_char, f"{msg} Subject end_char mismatch.")

        self.assertEqual(actual.predicate.text, expected.predicate.text, f"{msg} Predicate text mismatch.")
        self.assertEqual(actual.predicate.start_char, expected.predicate.start_char,
                         f"{msg} Predicate start_char mismatch.")
        self.assertEqual(actual.predicate.end_char, expected.predicate.end_char, f"{msg} Predicate end_char mismatch.")

        self.assertEqual(actual.obj.text, expected.obj.text, f"{msg} Object text mismatch.")
        self.assertEqual(actual.obj.start_char, expected.obj.start_char, f"{msg} Object start_char mismatch.")
        self.assertEqual(actual.obj.end_char, expected.obj.end_char, f"{msg} Object end_char mismatch.")

    def test_active_voice(self):
        text = "John hit the ball."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subject=TripletPart(text="John", start_char=0, end_char=4),
                predicate=TripletPart(text="hit", start_char=5, end_char=8),
                obj=TripletPart(text="the ball", start_char=9, end_char=17)
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")

    def test_active_voice_with_adjuncts(self):
        text = "The dog chased the cat quickly in the barn."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subject=TripletPart(text="The dog", start_char=0, end_char=7),
                predicate=TripletPart(text="chased", start_char=8, end_char=14),
                obj=TripletPart(text="the cat", start_char=15, end_char=22)
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")

    def test_prepositional_object(self):
        text = "The dog looked at the sky"
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subject=TripletPart(text="The dog", start_char=0, end_char=7),
                predicate=TripletPart(text="looked", start_char=8, end_char=14),
                obj=TripletPart(text="the sky", start_char=18, end_char=25)
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")

    def test_copula_verb_attribute(self):
        text = "Pam is a doctor."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subject=TripletPart(text="Pam", start_char=0, end_char=3),
                predicate=TripletPart(text="is", start_char=4, end_char=6),
                obj=TripletPart(text="a doctor", start_char=7, end_char=15)
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")

    def test_xcomp_verb_object(self):
        text = "He likes to read books."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            # Triplet(
            #     subject=TripletPart(text="He", start_char=0, end_char=2),
            #     predicate=TripletPart(text="likes to read", start_char=3, end_char=16),
            #     # 'likes' (3-8), 'to' (9-11), 'read' (12-16)
            #     obj=TripletPart(text="books", start_char=17, end_char=22)
            # )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        # self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")

    def test_passive_voice_with_agent(self):
        text = "The book was read by Mary."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subject=TripletPart(text="Mary", start_char=21, end_char=25),  # Swapped subject (agent)
                predicate=TripletPart(text="read", start_char=13, end_char=17),  # 'was' (9-12), 'read' (13-17)
                obj=TripletPart(text="The book", start_char=0, end_char=8)  # Swapped object (grammatical subject)
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")

    def test_copular_verb_adjective(self):
        text = "The car is red."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subject=TripletPart(text="The car", start_char=0, end_char=7),
                predicate=TripletPart(text="is", start_char=8, end_char=10),
                obj=TripletPart(text="red", start_char=11, end_char=14)
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")

    def test_ditransitive_verb(self):
        text = "The boy gave his friend a present."
        triplets = self.extractor.extract(text)

        # This case is tricky as the current logic only picks one object.
        # It will likely pick 'a present' as dobj.
        expected_triplets = [
            Triplet(
                subject=TripletPart(text="The boy", start_char=0, end_char=7),
                predicate=TripletPart(text="gave", start_char=8, end_char=12),
                obj=TripletPart(text="a present", start_char=24, end_char=33)
            )
        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}':")



    def test_multiple_sentences(self):
        text = "John hit the ball. Birds fly fast. The dog chased the cat quickly."
        triplets = self.extractor.extract(text)

        expected_triplets = [
            Triplet(
                subject=TripletPart(text="John", start_char=0, end_char=4),
                predicate=TripletPart(text="hit", start_char=5, end_char=8),
                obj=TripletPart(text="the ball", start_char=9, end_char=17)
            ),
            Triplet(
                subject=TripletPart(text="The dog", start_char=35, end_char=42),
                predicate=TripletPart(text="chased", start_char=43, end_char=49),
                obj=TripletPart(text="the cat", start_char=50, end_char=57)
            )

        ]
        self.assertEqual(len(triplets), len(expected_triplets))
        self.assertTripletEqual(triplets[0], expected_triplets[0], msg=f"Test '{text}' sentence 1:")
        self.assertTripletEqual(triplets[1], expected_triplets[1], msg=f"Test '{text}' sentence 2:")

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
