import unittest

from narrativegraph.extraction.common import Triplet


class ExtractorTest(unittest.TestCase):

    def assertTripletEqual(self, expected: Triplet, actual: Triplet, msg: str = ""):
        """
        Custom assertion to compare Triplet NamedTuples.
        Compares text, start_char, and end_char for each part.
        """
        self.assertEqual(
            actual.subj.text, expected.subj.text, f"{msg} Subject text mismatch."
        )
        self.assertEqual(
            actual.subj.start_char,
            expected.subj.start_char,
            f"{msg} Subject start_char mismatch.",
        )
        self.assertEqual(
            actual.subj.end_char,
            expected.subj.end_char,
            f"{msg} Subject end_char mismatch.",
        )

        self.assertEqual(
            actual.pred.text, expected.pred.text, f"{msg} Predicate text mismatch."
        )
        self.assertEqual(
            actual.pred.start_char,
            expected.pred.start_char,
            f"{msg} Predicate start_char mismatch.",
        )
        self.assertEqual(
            actual.pred.end_char,
            expected.pred.end_char,
            f"{msg} Predicate end_char mismatch.",
        )

        self.assertEqual(
            actual.obj.text, expected.obj.text, f"{msg} Object text mismatch."
        )
        self.assertEqual(
            actual.obj.start_char,
            expected.obj.start_char,
            f"{msg} Object start_char mismatch.",
        )
        self.assertEqual(
            actual.obj.end_char,
            expected.obj.end_char,
            f"{msg} Object end_char mismatch.",
        )