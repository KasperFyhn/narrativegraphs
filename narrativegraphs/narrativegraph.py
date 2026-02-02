from datetime import date, datetime
from typing import Literal

import networkx as nx
import pandas as pd

from narrativegraphs.basegraph import BaseGraph
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.pipeline import Pipeline
from narrativegraphs.nlp.triplets import TripletExtractor
from narrativegraphs.nlp.tuplets.common import CooccurrenceExtractor


class NarrativeGraph(BaseGraph):
    """Full narrative graph with triplet extraction, relations, and co-occurrences.

    NarrativeGraph extracts subject-predicate-object triplets from text documents
    and builds both a directed relation graph and an undirected co-occurrence graph.
    """

    _cooccurrence_only = False

    def __init__(
        self,
        triplet_extractor: TripletExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        predicate_mapper: Mapper = None,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
        n_cpu: int = -1,
    ):
        """Initialize a NarrativeGraph.

        Args:
            triplet_extractor: Extractor for subject-predicate-object triplets.
            cooccurrence_extractor: Extractor for entity co-occurrences.
            entity_mapper: Mapper for entity normalization.
            predicate_mapper: Mapper for predicate normalization.
            sqlite_db_path: Path to SQLite database file. If None, uses in-memory DB.
            on_existing_db: Behavior when database exists:
                - "stop": Raise error if DB contains data
                - "overwrite": Delete existing DB
                - "reuse": Use existing DB data
            n_cpu: Number of CPUs for parallel processing (-1 for all).
        """
        super().__init__(sqlite_db_path, on_existing_db)
        self._pipeline = Pipeline(
            self._engine,
            triplet_extractor=triplet_extractor,
            cooccurrence_extractor=cooccurrence_extractor,
            entity_mapper=entity_mapper,
            predicate_mapper=predicate_mapper,
            n_cpu=n_cpu,
        )

    def fit(
        self,
        docs: list[str],
        doc_ids: list[int | str] = None,
        timestamps: list[datetime | date] = None,
        categories: (
            list[str | list[str]]
            | dict[str, list[str | list[str]]]
            | list[dict[str, str | list[str]]]
        ) = None,
    ) -> "NarrativeGraph":
        """
        Fit a narrative graph from documents. The docs can be accompanied by lists with
        the same length of IDs, timestamps and categories.

        Args:
            docs: Required argument, a list of documents as strings.
            doc_ids: Optional list of document ids. Same length as docs.
            timestamps: Optional list of document timestamps. Same length as docs.
            categories: Optional list of document categories. Supports single or
                multiple categories. A document can have a single or multiple labels
                per category. See further down for examples.

        Returns:
            A fitted NarrativeGraph instance.

        """
        self._pipeline.run(
            docs,
            doc_ids=doc_ids,
            timestamps=timestamps,
            categories=categories,
        )
        return self

    @property
    def predicates_(self) -> pd.DataFrame:
        """Predicates as a pandas DataFrame."""
        return self.predicates.as_df()

    @property
    def relations_(self) -> pd.DataFrame:
        """Relations as a pandas DataFrame."""
        return self.relations.as_df()

    @property
    def triplets_(self) -> pd.DataFrame:
        """Triplets as a pandas DataFrame."""
        return self.triplets.as_df()

    @property
    def relation_graph_(self) -> nx.DiGraph:
        """The full relation graph as a directed NetworkX graph."""
        rg = self.graph.get_graph("relation")
        g = nx.DiGraph()
        g.add_nodes_from((n.id, n) for n in rg.nodes)
        g.add_edges_from((e.from_id, e.to_id, e) for e in rg.edges)
        return g

    @classmethod
    def load(cls, file_path: str) -> "NarrativeGraph":
        """

        Args:
            file_path: path to a SQLite database to load a NarrativeGraph from.

        Returns:
            A NarrativeGraph object
        """
        return super().load(file_path)
