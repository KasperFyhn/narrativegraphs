import functools
import logging
from collections import Counter, defaultdict
from typing import Callable, Literal, Sequence

import nltk
from nltk import SnowballStemmer, pos_tag, word_tokenize

from narrativegraphs.nlp.common.spacy import ensure_spacy_model
from narrativegraphs.nlp.mapping.common import Mapper

_logger = logging.getLogger("narrativegraphs.nlp.mapping.linguistic")

NormalizerFn = Callable[[str], str]


def _ensure_nltk_model(name: str):
    nltk.download(name, quiet=True)


@functools.lru_cache(maxsize=4096)
def _pos_tagged_tokens(label: str):
    return pos_tag(word_tokenize(label))


def snowball_normalizer(language: str = "english") -> NormalizerFn:
    """Returns a normalizer using NLTK's SnowballStemmer."""
    stemmer = SnowballStemmer(language)
    return stemmer.stem


def _nltk_tag_to_wordnet_pos(tag: str) -> str:
    if tag.startswith("V"):
        return "v"
    elif tag.startswith("J"):
        return "a"
    elif tag.startswith("R"):
        return "r"
    else:
        return "n"


def lemmatizer_normalizer() -> NormalizerFn:
    """Returns a normalizer using NLTK's WordNetLemmatizer with POS-aware
    lemmatization."""
    _ensure_nltk_model("wordnet")
    _ensure_nltk_model("punkt_tab")
    _ensure_nltk_model("averaged_perceptron_tagger_eng")
    from nltk.stem import WordNetLemmatizer

    lemmatizer = WordNetLemmatizer()

    def normalize(text: str) -> str:
        return " ".join(
            lemmatizer.lemmatize(word, pos=_nltk_tag_to_wordnet_pos(tag))
            for word, tag in _pos_tagged_tokens(text)
        )

    return normalize


def spacy_normalizer(model_name: str = "en_core_web_sm") -> NormalizerFn:
    """Returns a normalizer using spaCy's lemmatizer.

    Only the tokenizer, tagger, and lemmatizer components are enabled.
    """
    nlp = ensure_spacy_model(model_name)
    for pipe in ["parser", "ner", "senter"]:
        if nlp.has_pipe(pipe):
            nlp.disable_pipe(pipe)

    def normalize(text: str) -> str:
        return " ".join(token.lemma_.lower() for token in nlp(text))

    return normalize


def _make_fallback_normalizer(normalizers: Sequence[NormalizerFn]) -> NormalizerFn:
    def normalize(text: str) -> str:
        last_exc: Exception | None = None
        for norm in normalizers:
            try:
                return norm(text)
            except Exception as e:
                last_exc = e
        raise RuntimeError("All normalizers failed") from last_exc

    return normalize


class NormalizationMapper(Mapper):
    def __init__(
        self,
        normalizer: NormalizerFn | Sequence[NormalizerFn] | None = None,
        ignore_determiners: bool = True,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        super().__init__()
        self._ignore_determiners = ignore_determiners
        self._ranking = ranking
        self._normalize_cache: dict[str, str] = {}

        if normalizer is None:
            self._normalizer = snowball_normalizer()
        elif callable(normalizer):
            self._normalizer = normalizer
        else:
            self._normalizer = _make_fallback_normalizer(normalizer)

        _ensure_nltk_model("punkt_tab")
        if ignore_determiners:
            _ensure_nltk_model("averaged_perceptron_tagger_eng")

    def _normalize(self, label: str) -> str:
        if label in self._normalize_cache:
            return self._normalize_cache[label]

        text = label
        if self._ignore_determiners:
            text = " ".join(w for w, tag in _pos_tagged_tokens(label) if tag != "DT")
        result = self._normalizer(text)
        self._normalize_cache[label] = result
        return result

    @staticmethod
    def _negative_length(label: str) -> int:
        return -len(word_tokenize(label))

    def _ranker(self, labels: list[str]) -> Callable[[str], tuple]:
        counter = Counter(labels)
        if self._ranking == "shortest":
            return lambda x: (
                self._negative_length(x), counter.__getitem__(x), [-ord(c) for c in x]
            )
        elif self._ranking == "most_frequent":
            return lambda x: (
                counter.__getitem__(x), self._negative_length(x), [-ord(c) for c in x]
            )
        else:
            raise NotImplementedError("Unknown ranking")

    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        ranker = self._ranker(labels)

        clusters: dict[str, list[str]] = defaultdict(list)
        for label in set(labels):
            clusters[self._normalize(label)].append(label)

        result = {}
        for cluster in clusters.values():
            canonical = max(cluster, key=ranker)
            for label in cluster:
                result[label] = canonical
        return result


class SubgramNormalizationMapper(NormalizationMapper):
    def __init__(
        self,
        head_word_type: Literal["noun", "verb"],
        normalizer: NormalizerFn | Sequence[NormalizerFn] | None = None,
        ignore_determiners: bool = True,
        min_subgram_length: int = 2,
        min_subgram_frequency: int = 10,
        min_subgram_frequency_ratio: float = 2.0,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        super().__init__(
            normalizer=normalizer,
            ignore_determiners=ignore_determiners,
            ranking=ranking,
        )
        self._head_word_subtag = "NN" if head_word_type == "noun" else "VB"
        self._min_subgram_length = min_subgram_length
        self._min_subgram_frequency = min_subgram_frequency
        self._min_subgram_frequency_ratio = min_subgram_frequency_ratio

    def _matches_head_word_subtag(self, label: str) -> bool:
        return any(
            self._head_word_subtag in tag for _, tag in _pos_tagged_tokens(label)
        )

    def _subgram_mapping(self, labels: list[str]) -> dict[str, str]:
        labels_set = set(labels)

        norm_map = {
            label: " "
            + self._normalize(label)
            + " "  # surrounding spaces avoids matches like evil <-> devil
            for label in labels_set
        }
        cluster_map: dict[str, list[str]] = defaultdict(list)
        ranker = self._ranker(labels)

        counter = Counter(labels)
        main_label_candidates = {
            label
            for label in labels_set
            if self._matches_head_word_subtag(label)
            and len(self._normalize(label).split()) >= self._min_subgram_length
            and counter[label] >= self._min_subgram_frequency
        }

        for label in labels_set:
            norm_label = norm_map[label]
            matches = [
                candidate
                for candidate in main_label_candidates
                if norm_map[candidate] in norm_label
                # Only map if the candidate is considerably more frequent
                and counter[candidate]
                >= self._min_subgram_frequency_ratio * counter[label]
            ]
            if not matches:
                continue

            best_match = max(matches, key=ranker)
            if best_match != label:
                cluster_map[best_match].append(label)

        return {
            alt_label: main_label
            for main_label, alt_labels in cluster_map.items()
            for alt_label in alt_labels + [main_label]
        }

    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        norm_mapping = super().create_mapping(labels)
        subgram_mapping = self._subgram_mapping(
            [norm_mapping[label] for label in labels]
        )
        result = {}
        for label in labels:
            norm = norm_mapping[label]
            result[label] = subgram_mapping.get(norm, norm)
        return result


class StemmingMapper(NormalizationMapper):
    def __init__(
        self,
        ignore_determiners: bool = True,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        super().__init__(
            normalizer=snowball_normalizer(),
            ignore_determiners=ignore_determiners,
            ranking=ranking,
        )


class SubgramStemmingMapper(SubgramNormalizationMapper):
    def __init__(
        self,
        head_word_type: Literal["noun", "verb"],
        ignore_determiners: bool = True,
        min_subgram_length: int = 2,
        min_subgram_frequency: int = 10,
        min_subgram_frequency_ratio: float = 2.0,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        super().__init__(
            head_word_type=head_word_type,
            normalizer=snowball_normalizer(),
            ignore_determiners=ignore_determiners,
            min_subgram_length=min_subgram_length,
            min_subgram_frequency=min_subgram_frequency,
            min_subgram_frequency_ratio=min_subgram_frequency_ratio,
            ranking=ranking,
        )


class LemmatizationMapper(NormalizationMapper):
    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        ignore_determiners: bool = True,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        super().__init__(
            normalizer=spacy_normalizer(model_name),
            ignore_determiners=ignore_determiners,
            ranking=ranking,
        )


class SubgramLemmatizationMapper(SubgramNormalizationMapper):
    def __init__(
        self,
        head_word_type: Literal["noun", "verb"],
        model_name: str = "en_core_web_sm",
        ignore_determiners: bool = True,
        min_subgram_length: int = 2,
        min_subgram_frequency: int = 10,
        min_subgram_frequency_ratio: float = 2.0,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        super().__init__(
            head_word_type=head_word_type,
            normalizer=spacy_normalizer(model_name),
            ignore_determiners=ignore_determiners,
            min_subgram_length=min_subgram_length,
            min_subgram_frequency=min_subgram_frequency,
            min_subgram_frequency_ratio=min_subgram_frequency_ratio,
            ranking=ranking,
        )
