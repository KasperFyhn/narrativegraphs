import re
from abc import ABC
from typing import Callable

import spacy

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.nlp.extraction.common import SpanAnnotation, Tuplet
from narrativegraphs.nlp.utils.spacysegmentation import custom_sentencizer  # noqa


class CooccurrenceExtractor(ABC):
    def extract(self, doc: DocumentOrm, triplets: list[SpanAnnotation]) -> list[Tuplet]:
        pass


class ChunkCooccurrenceExtractor(CooccurrenceExtractor):
    def __init__(
        self,
        window: int = 3,
        custom_boundary: str | re.Pattern = None,
        custom_chunker: Callable[[str], list[str]] = None,
        language: str = "en",
    ):
        if window is not None and window < 0:
            raise ValueError("Window must be >= 0")
        self.window = window
        self._boundary_pattern = None

        if custom_chunker:
            self._chunker = custom_chunker
            self._chunker_type = "custom"
        elif custom_boundary:
            if isinstance(custom_boundary, str):
                self._boundary_pattern = re.compile(custom_boundary)
            else:
                self._boundary_pattern = custom_boundary
            self._chunker_type = "regex"
        else:
            nlp = spacy.blank(language)
            nlp.add_pipe("sentencizer")
            nlp.add_pipe("custom_sentencizer")
            self._nlp = nlp
            self._chunker_type = "spacy"

    def _get_chunk_bounds(self, text: str) -> list[tuple[int, int]]:
        """Return list of (start_char, end_char) for each chunk."""
        if self._chunker_type == "spacy":
            doc = self._nlp(text)
            return [(sent.start_char, sent.end_char) for sent in doc.sents]

        elif self._chunker_type == "regex":
            bounds = []
            last_end = 0
            for match in self._boundary_pattern.finditer(text):
                if last_end < match.start():
                    bounds.append((last_end, match.start()))
                last_end = match.end()
            if last_end < len(text):
                bounds.append((last_end, len(text)))
            return bounds

        else:  # custom chunker
            chunks = self._chunker(text)
            bounds = []
            pos = 0
            for chunk in chunks:
                idx = text.find(chunk, pos)
                if idx != -1:
                    bounds.append((idx, idx + len(chunk)))
                    pos = idx + len(chunk)
            return bounds

    @staticmethod
    def is_entity_within_bounds(start: int, end: int, entity: SpanAnnotation) -> bool:
        return start <= entity.start_char and entity.end_char <= end

    def _assign_entities_to_chunks(
        self,
        chunk_bounds: list[tuple[int, int]],
        entities: list[SpanAnnotation],
    ) -> list[list[SpanAnnotation]]:
        """Assign each entity to its containing chunk."""
        sorted_entities = sorted(entities, key=lambda e: e.start_char)
        chunk_entities = [[] for _ in chunk_bounds]
        entity_idx = 0

        for chunk_idx, (start, end) in enumerate(chunk_bounds):
            while entity_idx < len(sorted_entities):
                entity = sorted_entities[entity_idx]

                if entity.start_char >= end:
                    break

                if self.is_entity_within_bounds(start, end, entity):
                    chunk_entities[chunk_idx].append(entity)

                entity_idx += 1

        return chunk_entities

    def extract(self, doc: DocumentOrm, entities: list[SpanAnnotation]) -> list[Tuplet]:
        chunk_bounds = self._get_chunk_bounds(doc.text)
        chunk_entities = self._assign_entities_to_chunks(chunk_bounds, entities)

        all_pairs = []
        num_chunks = len(chunk_entities)

        for i in range(num_chunks):
            if self.window is None:
                window_end = i + 1
            else:
                window_end = min(i + 1 + self.window, num_chunks)
            window_entities = [
                e for chunk in chunk_entities[i + 1 : window_end] for e in chunk
            ]

            current_chunk = chunk_entities[i]
            for j, entity in enumerate(current_chunk):
                for other in current_chunk[j + 1 :] + window_entities:
                    all_pairs.append(Tuplet(entity_one=entity, entity_two=other))

        return all_pairs


class DocumentCooccurrenceExtractor(CooccurrenceExtractor):
    def extract(self, doc: DocumentOrm, entities: list[SpanAnnotation]) -> list[Tuplet]:
        pairs = []
        for i, entity in enumerate(entities):
            for other in entities[i + 1 :]:
                pairs.append(Tuplet(entity_one=entity, entity_two=other))
        return pairs
