from typing import Iterable

from narrativegraph.tripletextraction.common import Triplet


class TripletAggregation:

    def __init__(self, triplets: Iterable[list[Triplet]]):
        self._entities = None
        self._relations = None


    @property
    def entities(self) -> list[str]:
        return self._entities


    @property
    def relations(self) -> list[str]:
        return self._relations
