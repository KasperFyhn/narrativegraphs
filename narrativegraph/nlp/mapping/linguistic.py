from collections import defaultdict
from typing import Literal, Counter

import nltk
from nltk import PorterStemmer, pos_tag, word_tokenize

from narrativegraph.nlp.mapping.common import Mapper


class StemmingMapper(Mapper):

    def __init__(
        self,
        ignore_determiners: bool = True,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        super().__init__()
        self._ignore_determiners = ignore_determiners
        self._ranking = ranking

        self._pos_tag = nltk.pos_tag
        self._stemmer = PorterStemmer()

    def _normalize(self, label: str) -> str:
        if self._ignore_determiners:
            tokens = word_tokenize(label)
            pos_tagged = pos_tag(tokens)
            label = " ".join(w[0] for w in pos_tagged if w[1] != "DT")
        return self._stemmer.stem(label)

    @staticmethod
    def _negative_length(label: str) -> int:
        return -len(label.split())

    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        if self._ranking == "shortest":
            ranker = self._negative_length
        elif self._ranking == "most_frequent":
            counter = Counter(labels)
            ranker = counter.__getitem__
        else:
            raise NotImplementedError("Unknown ranking")

        clusters = defaultdict(list)
        for label in set(labels):
            clusters[self._normalize(label)].append(label)

        for cluster in clusters.values():
            cluster.sort(key=ranker, reverse=True)

        return {label: cluster[0] for cluster in clusters.values() for label in cluster}


class SubgramStemmingMapper(StemmingMapper):

    def __init__(
        self,
        head_word_subtag: str,
        ignore_determiners: bool = True,
        ranking: Literal["shortest", "most_frequent"] = "shortest",
    ):
        self._head_word_subtag = head_word_subtag
        super().__init__(ignore_determiners=ignore_determiners, ranking=ranking)

    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        counter = Counter(labels)

        norm_map = {
            label: " "
            + self._normalize(label)
            + " "  # surrounding spaces avoids matches like evil <-> devil
            for label in counter.keys()
        }
        cluster_map = {
            label: []
            for label in counter.keys()
            if self._head_word_subtag in pos_tag([label])[0][1]
        }

        unclustered = []
        for label in counter.keys():
            norm_label = norm_map[label]
            matches = [
                candidate
                for candidate in cluster_map.keys()
                if norm_map[candidate] in norm_label
            ]
            if not matches:
                unclustered.append(label)
                continue

            # best match is the shortest norm match; then the most frequent label
            best_match = min(
                matches,
                key=lambda match: (
                    len(match.strip().split()),
                    -counter[match],
                ),
            )
            if best_match != label:
                cluster_map[best_match].append(label)

        result = {
            alt_label: main_label
            for main_label, alt_labels in cluster_map.items()
            for alt_label in alt_labels + [main_label]
        }
        for uc in unclustered:
            result[uc] = uc
        return result
