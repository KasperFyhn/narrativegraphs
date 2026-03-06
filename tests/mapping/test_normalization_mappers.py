import unittest

from narrativegraphs.nlp.mapping.linguistic import (
    LemmatizationMapper,
    NormalizationMapper,
    SubgramLemmatizationMapper,
    SubgramNormalizationMapper,
    lemmatizer_normalizer,
    snowball_normalizer,
    spacy_normalizer,
)


def lowercase_string(text: str) -> str:
    return text.lower()


class TestNormalizationMapper(unittest.TestCase):
    def test_custom_normalizer(self):
        """A custom normalizer is used in place of the default."""
        mapper = NormalizationMapper(
            normalizer=lowercase_string, ignore_determiners=False
        )
        mapping = mapper.create_mapping(["FOO", "foo", "bar"])
        self.assertEqual(mapping["FOO"], mapping["foo"])
        self.assertNotEqual(mapping["foo"], mapping["bar"])

    def test_fallback_normalizer_uses_first(self):
        """When the first normalizer in a sequence succeeds, its result is used."""
        mapper = NormalizationMapper(
            normalizer=[lambda x: "same", lambda x: "other"],
            ignore_determiners=False,
        )
        mapping = mapper.create_mapping(["foo", "bar"])
        self.assertEqual(mapping["foo"], mapping["bar"])

    def test_fallback_normalizer_falls_back(self):
        """When the first normalizer raises, the next one is tried."""

        def failing(x):
            raise RuntimeError(f"unavailable: {x}")

        mapper = NormalizationMapper(
            normalizer=[failing, lowercase_string],
            ignore_determiners=False,
        )
        mapping = mapper.create_mapping(["FOO", "foo"])
        self.assertEqual(mapping["FOO"], mapping["foo"])

    def test_ignore_determiners_clusters_variants(self):
        """Labels differing only by a leading determiner cluster together."""
        mapper = NormalizationMapper(normalizer=lambda x: x, ignore_determiners=True)
        mapping = mapper.create_mapping(["the cat", "cat"])
        self.assertEqual(mapping["the cat"], mapping["cat"])

    def test_ranking_shortest(self):
        """The shortest label in a cluster is chosen as the canonical form."""
        mapper = NormalizationMapper(
            normalizer=lambda x: x,
            ignore_determiners=True,
            ranking="shortest",
        )
        mapping = mapper.create_mapping(["the cat", "cat"])
        self.assertEqual(mapping["the cat"], "cat")
        self.assertEqual(mapping["cat"], "cat")

    def test_ranking_shortest_tiebreak_alphabetical(self):
        """When cluster members have equal length and frequency, alphabetically first
        wins."""
        mapper = NormalizationMapper(
            normalizer=lambda x: x.lower(),
            ignore_determiners=False,
            ranking="shortest",
        )
        # "Natural Language" and "natural language" are both 2 tokens, freq=1.
        # 'N' (ASCII 78) < 'n' (ASCII 110) → "Natural Language" is alphabetically first.
        mapping = mapper.create_mapping(["natural language", "Natural Language"])
        self.assertEqual(mapping["natural language"], "Natural Language")
        self.assertEqual(mapping["Natural Language"], "Natural Language")

    def test_ranking_most_frequent(self):
        """The most frequent label in a cluster is chosen as the canonical form."""
        mapper = NormalizationMapper(
            normalizer=lambda x: x,
            ignore_determiners=True,
            ranking="most_frequent",
        )
        # "the cat" appears twice, "cat" once → "the cat" wins
        mapping = mapper.create_mapping(["the cat", "the cat", "cat"])
        self.assertEqual(mapping["the cat"], "the cat")
        self.assertEqual(mapping["cat"], "the cat")

    def test_normalize_cache_populated(self):
        """_normalize_cache is populated after create_mapping."""
        mapper = NormalizationMapper(normalizer=lambda x: x, ignore_determiners=False)
        mapper.create_mapping(["foo", "bar"])
        self.assertIn("foo", mapper._normalize_cache)
        self.assertIn("bar", mapper._normalize_cache)

    def test_normalize_cache_avoids_redundant_calls(self):
        """The normalizer is called at most once per unique label."""
        call_count = 0

        def counting_normalizer(x):
            nonlocal call_count
            call_count += 1
            return x.lower()

        mapper = NormalizationMapper(
            normalizer=counting_normalizer, ignore_determiners=False
        )
        mapper.create_mapping(["FOO", "FOO", "FOO"])
        self.assertEqual(call_count, 1)


class TestSubgramNormalizationMapper(unittest.TestCase):
    def test_custom_normalizer(self):
        """SubgramNormalizationMapper accepts and uses a custom normalizer."""
        mapper = SubgramNormalizationMapper(
            head_word_type="noun",
            normalizer=lowercase_string,
            min_subgram_frequency=1,
            min_subgram_frequency_ratio=1.0,
        )
        # "dark lord" (noun) appears at least as often as "the dark lord",
        # and is a subgram of it — so "the dark lord" should map to "dark lord"
        mapping = mapper.create_mapping(["dark lord", "dark lord", "the dark lord"])
        self.assertEqual(mapping["the dark lord"], "dark lord")

    def test_subgram_tiebreak_alphabetical(self):
        """When two subgram candidates tie on length and frequency, alphabetically
        first wins.

        "natural language processing" contains both "natural language" and
        "language processing" as subgrams. Both are length-2 and appear twice.
        "language processing" is alphabetically first (l < n) and must win.
        """
        mapper = SubgramNormalizationMapper(
            head_word_type="noun",
            normalizer=lambda x: x,
            ignore_determiners=False,
            min_subgram_frequency=2,
            min_subgram_frequency_ratio=1.0,
        )
        labels = [
            "natural language",
            "natural language",
            "language processing",
            "language processing",
            "natural language processing",
        ]
        mapping = mapper.create_mapping(labels)
        self.assertEqual(mapping["natural language processing"], "language processing")


class TestSnowballNormalizer(unittest.TestCase):
    def test_stems_inflected_forms_identically(self):
        norm = snowball_normalizer()
        self.assertEqual(norm("running"), norm("runs"))

    def test_language_parameter(self):
        norm = snowball_normalizer("english")
        self.assertIsNotNone(norm("testing"))


class TestLemmatizerNormalizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.norm = staticmethod(lemmatizer_normalizer())

    def test_lemmatizes_plural_noun(self):
        self.assertEqual(self.norm("cats"), "cat")

    def test_lemmatizes_verb(self):
        # "running" is tagged VBG → pos="v" → lemma "run"
        self.assertEqual(self.norm("running"), "run")


class TestSpacyNormalizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.norm = staticmethod(spacy_normalizer())

    def test_lemmatizes_plural_noun(self):
        self.assertEqual(self.norm("cats"), "cat")

    def test_lemmatizes_multi_word(self):
        result = self.norm("dark lords")
        self.assertIn("lord", result)


class TestLemmatizationMapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapper = LemmatizationMapper()

    def test_initialization(self):
        self.mapper.create_mapping(["cat", "cats"])

    def test_clusters_inflected_forms(self):
        mapping = self.mapper.create_mapping(["cat", "cats"])
        self.assertEqual(mapping["cat"], mapping["cats"])


class TestSubgramLemmatizationMapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapper = SubgramLemmatizationMapper("noun", min_subgram_frequency=2)

    def test_initialization(self):
        labels = ["dark lord", "the dark lord"]
        mapping = self.mapper.create_mapping(labels)
        self.assertEqual(set(mapping.keys()), set(labels))

    def test_lemmatizes_plural_noun(self):
        labels = [
            "dark lord",
            "dark lord",
            "dark lord",
            "the dark lord Sauron",
        ]
        mapping = self.mapper.create_mapping(labels)
        self.assertEqual(mapping["dark lord"], mapping["the dark lord Sauron"])


if __name__ == "__main__":
    unittest.main()
