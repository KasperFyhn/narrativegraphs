from abc import ABC

from narrativegraph.db.documents import DocumentOrm
from narrativegraph.nlp.extraction.common import Triplet


class CoOccurrenceExtractor(ABC):
    def extract(
        self, doc: DocumentOrm, triplets: list[Triplet]
    ) -> list[tuple[str, str]]:
        pass


class DefaultCoOccurrenceExtractor(CoOccurrenceExtractor):
    def __init__(self, window: int = 3, boundary: str = "\n\n"):
        self.window = window
        self.boundary = boundary

    def extract_from_chunk(self, triplets: list[Triplet]) -> list[tuple[str, str]]:
        seen = set()
        entities = []
        for triplet in triplets:
            for entity in [triplet.subj, triplet.obj]:
                key = (entity.start_char, entity.end_char)
                if key not in seen:
                    seen.add(key)
                    entities.append(entity)
        entities.sort(key=lambda e: e.start_char)

        pairs = []
        for i, entity in enumerate(entities):
            window_bound = min(i + 1 + self.window, len(entities))
            following = entities[i + 1 : window_bound]
            for other in following:
                pairs.append((entity.text, other.text))

        return pairs

    @staticmethod
    def is_triplet_within_bounds(start: int, end: int, triplet: Triplet) -> bool:
        min_position = min(
            triplet.subj.start_char,
            triplet.pred.start_char,
            triplet.obj.start_char,
        )
        max_position = max(
            triplet.subj.end_char,
            triplet.pred.end_char,
            triplet.obj.end_char,
        )
        return start <= min_position and max_position <= end

    def extract(
        self, doc: DocumentOrm, triplets: list[Triplet]
    ) -> list[tuple[str, str]]:
        if self.boundary is not None:
            chunks = doc.text.split(self.boundary)
        else:
            chunks = [doc.text]

        # Build chunk boundaries accounting for separator length
        chunk_bounds = []
        at = 0
        boundary_len = len(self.boundary) if self.boundary else 0

        for chunk in chunks:
            start = at
            end = at + len(chunk)
            chunk_bounds.append((start, end))
            at = end + boundary_len  # Account for the boundary

        # Sort triplets once by start position for efficiency
        sorted_triplets = sorted(
            triplets,
            key=lambda t: min(t.subj.start_char, t.pred.start_char, t.obj.start_char),
        )

        # Assign triplets to chunks
        triplet_idx = 0
        all_pairs = []

        for start, end in chunk_bounds:
            chunk_triplets = []

            # Collect all triplets that could overlap with this chunk
            temp_idx = triplet_idx
            while temp_idx < len(sorted_triplets):
                triplet = sorted_triplets[temp_idx]
                min_pos = min(
                    triplet.subj.start_char,
                    triplet.pred.start_char,
                    triplet.obj.start_char,
                )

                # If triplet starts after chunk ends, we're done with this chunk
                if min_pos >= end:
                    break

                # Check if fully contained
                if self.is_triplet_within_bounds(start, end, triplet):
                    chunk_triplets.append(triplet)

                temp_idx += 1

            # Advance the starting point for next chunk
            # (triplets can't start before the current chunk's start)
            while (
                triplet_idx < len(sorted_triplets)
                and min(
                    sorted_triplets[triplet_idx].subj.start_char,
                    sorted_triplets[triplet_idx].pred.start_char,
                    sorted_triplets[triplet_idx].obj.start_char,
                )
                < start
            ):
                triplet_idx += 1

            # Extract pairs from this chunk
            pairs = self.extract_from_chunk(chunk_triplets)
            all_pairs.extend(pairs)

        return all_pairs
