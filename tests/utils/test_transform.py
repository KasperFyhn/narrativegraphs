import unittest

from narrativegraphs.utils.transform import normalize_categories


class TestNormalizeCategories(unittest.TestCase):
    def test_list_of_strings(self):
        self.assertEqual(
            normalize_categories(["label1", "label2"]),
            [{"category": ["label1"]}, {"category": ["label2"]}],
        )

    def test_list_of_list_of_strings(self):
        self.assertEqual(
            normalize_categories([["label1", "label2"], ["label2"]]),
            [{"category": ["label1", "label2"]}, {"category": ["label2"]}],
        )

    def test_list_of_dicts_with_string_values(self):
        self.assertEqual(
            normalize_categories([{"category1": "label1"}, {"category1": "label2"}]),
            [{"category1": ["label1"]}, {"category1": ["label2"]}],
        )

    def test_list_of_dicts_with_list_of_string_values(self):
        self.assertEqual(
            normalize_categories(
                [{"category1": ["label1"]}, {"category1": ["label2"]}]
            ),
            [{"category1": ["label1"]}, {"category1": ["label2"]}],
        )

    def test_dict_with_list_values(self):
        self.assertEqual(
            normalize_categories(
                {"category1": ["label1", "label2"], "category2": ["label1", "label2"]}
            ),
            [
                {"category1": ["label1"], "category2": ["label1"]},
                {"category1": ["label2"], "category2": ["label2"]},
            ],
        )

    def test_dict_with_list_of_list_values(self):
        self.assertEqual(
            normalize_categories(
                {
                    "category1": [["label1"], ["label1", "label2"]],
                    "category2": [["label1"], ["label2", "label3"]],
                }
            ),
            [
                {"category1": ["label1"], "category2": ["label1"]},
                {"category1": ["label1", "label2"], "category2": ["label2", "label3"]},
            ],
        )

    def test_empty_list(self):
        self.assertEqual(normalize_categories([]), [])

    def test_empty_dict(self):
        self.assertEqual(normalize_categories({}), [])

    def test_non_string_values(self):
        with self.assertRaises(ValueError):
            normalize_categories({"category1": 42})  # noqa, deliberate

    def test_mixed_types_in_list(self):
        with self.assertRaises(ValueError):
            normalize_categories([{"category1": "label1"}, "label2", ["label3"], 42])

    # def test_nested_lists_in_values(self):
    #     with self.assertRaises(ValueError):
    #         normalize_categories({"category1": [["label1"], "label2"]})

    def test_different_lengths(self):
        with self.assertRaises(ValueError):
            normalize_categories(
                {"category1": ["label1", "label2"], "category2": ["label2"]}
            )
