from datetime import date, datetime
from typing import Literal

from narrativegraphs.basegraph import BaseGraph
from narrativegraphs.nlp.entities.common import EntityExtractor
from narrativegraphs.nlp.mapping import Mapper
from narrativegraphs.nlp.pipeline import CooccurrencePipeline
from narrativegraphs.nlp.tuplets.common import CooccurrenceExtractor


class CooccurrenceGraph(BaseGraph):
    """Co-occurrence graph without triplet extraction.

    CooccurrenceGraph extracts entities directly from text and builds an
    undirected co-occurrence graph. Unlike NarrativeGraph, it does not
    extract subject-predicate-object triplets or build a relation graph.

    Use this when you only need entity co-occurrence analysis without
    the overhead of triplet extraction.
    """

    _cooccurrence_only = True

    def __init__(
        self,
        entity_extractor: EntityExtractor = None,
        cooccurrence_extractor: CooccurrenceExtractor = None,
        entity_mapper: Mapper = None,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
        n_cpu: int = -1,
    ):
        """Initialize a CooccurrenceGraph.

        Args:
            entity_extractor: Extractor for entities (default: SpacyEntityExtractor).
            cooccurrence_extractor: Extractor for entity co-occurrences.
            entity_mapper: Mapper for entity normalization.
            sqlite_db_path: Path to SQLite database file. If None, uses in-memory DB.
            on_existing_db: Behavior when database exists:
                - "stop": Raise error if DB contains data
                - "overwrite": Delete existing DB
                - "reuse": Use existing DB data
            n_cpu: Number of CPUs for parallel processing (-1 for all).
        """
        super().__init__(sqlite_db_path, on_existing_db)
        self._pipeline = CooccurrencePipeline(
            self._engine,
            entity_extractor=entity_extractor,
            cooccurrence_extractor=cooccurrence_extractor,
            entity_mapper=entity_mapper,
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
    ) -> "CooccurrenceGraph":
        """Fit a co-occurrence graph from documents.

        Args:
            docs: Required argument, a list of documents as strings.
            doc_ids: Optional list of document ids. Same length as docs.
            timestamps: Optional list of document timestamps. Same length as docs.
            categories: Optional list of document categories. Supports single or
                multiple categories. A document can have a single or multiple labels
                per category.

        Returns:
            A fitted CooccurrenceGraph instance.
        """
        self._pipeline.run(
            docs,
            doc_ids=doc_ids,
            timestamps=timestamps,
            categories=categories,
        )
        return self

    @classmethod
    def load(cls, file_path: str) -> "CooccurrenceGraph":
        """Load a CooccurrenceGraph from a SQLite database file.

        Args:
            file_path: Path to a SQLite database to load a CooccurrenceGraph from.

        Returns:
            A CooccurrenceGraph object.
        """
        return super().load(file_path)
