import unittest

from narrativegraphs.nlp.extraction.common import Triplet


class ExtractorTest(unittest.TestCase):
    def assert_triplet_equal(self, expected: Triplet, actual: Triplet):
        """
        Custom assertion to compare Triplet NamedTuples.
        Compares text, start_char, and end_char for each part.
        Fails only at the end if there is at least one error.
        """
        errors = []

        for part_name in ["subj", "pred", "obj"]:
            expected_part = getattr(expected, part_name)
            actual_part = getattr(actual, part_name)
            for field_name in ["text", "start_char", "end_char"]:
                expected_field = getattr(expected_part, field_name)
                actual_field = getattr(actual_part, field_name)
                if expected_field != actual_field:
                    errors.append(
                        f"{part_name} {field_name} mismatch. "
                        f"Expected: {expected_field}, Got: {actual_field}"
                    )

        self.assertTrue(len(errors) == 0, "\n".join(errors))

    def assert_triplets_equal(self, expected: list[Triplet], actual: list[Triplet]):
        assert len(expected) == len(actual), (
            f"Expected {len(expected)}, got {len(actual)}: {actual}"
        )
        for e, a in zip(expected, actual):
            self.assert_triplet_equal(e, a)
