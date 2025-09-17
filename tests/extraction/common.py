import unittest

from narrativegraph.nlp.extraction.common import Triplet


class ExtractorTest(unittest.TestCase):

    def assertTripletEqual(self, expected: Triplet, actual: Triplet):
        """
        Custom assertion to compare Triplet NamedTuples.
        Compares text, start_char, and end_char for each part.
        """
        self.assertEqual(
            expected.subj.text, actual.subj.text, f"Subject text mismatch. {actual}"
        )
        self.assertEqual(
            expected.subj.start_char,
            actual.subj.start_char,
            f"Subject start_char mismatch. {actual}",
        )
        self.assertEqual(
            expected.subj.end_char,
            actual.subj.end_char,
            f"Subject end_char mismatch. {actual}",
        )

        self.assertEqual(
            expected.pred.text, actual.pred.text, f"Predicate text mismatch. {actual}"
        )
        self.assertEqual(
            expected.pred.start_char,
            actual.pred.start_char,
            f"Predicate start_char mismatch. {actual}",
        )
        self.assertEqual(
            expected.pred.end_char,
            actual.pred.end_char,
            f"Predicate end_char mismatch. {actual}",
        )

        self.assertEqual(
            expected.obj.text, actual.obj.text, f"Object text mismatch. {actual}"
        )
        self.assertEqual(
            expected.obj.start_char,
            actual.obj.start_char,
            f"Object start_char mismatch. {actual}",
        )
        self.assertEqual(
            expected.obj.end_char,
            actual.obj.end_char,
            f"Object end_char mismatch. {actual}",
        )

    def assertTripletsEqual(self, expected: list[Triplet], actual: list[Triplet]):
        assert len(expected) == len(
            actual
        ), f"Expected {len(expected)}, got {len(actual)}: {actual}"
        for e, a in zip(expected, actual):
            self.assertTripletEqual(e, a)
