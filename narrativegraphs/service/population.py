from datetime import date
from typing import Any

from narrativegraphs.db.documents import DocumentCategory, DocumentMetadata, DocumentOrm
from narrativegraphs.db.entityoccurrences import EntityOccurrenceOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.db.tuplets import TupletOrm
from narrativegraphs.nlp.common.annotation import SpanAnnotation
from narrativegraphs.nlp.triplets.common import Triplet
from narrativegraphs.nlp.tuplets.common import Tuplet
from narrativegraphs.service.cache import (
    CooccurrenceCache,
    EntityCache,
    PredicateCache,
    RelationCache,
)
from narrativegraphs.service.common import DbService


class PopulationService(DbService):
    def _bulk_save_docs_with_categories_and_meta(
        self,
        bulk: list[DocumentOrm],
        categories: list[dict[str, list[str]]],
        metadata: list[dict[str, Any]],
    ) -> None:
        with self.get_session_context() as sc:
            sc.add_all(bulk)
            sc.flush()
            cat_bulk = []
            meta_bulk = []
            for doc, cat_dict, meta_dict in zip(bulk, categories, metadata):
                for name, values in cat_dict.items():
                    for value in values:
                        cat_orm = DocumentCategory(
                            target_id=doc.id,
                            name=name,
                            value=value,
                        )
                        cat_bulk.append(cat_orm)
                if len(cat_bulk) > 1000:
                    sc.bulk_save_objects(cat_bulk)
                    cat_bulk.clear()
                for name, value in meta_dict.items():
                    meta_orm = DocumentMetadata(
                        name=name,
                        value=str(value),
                        doc_id=doc.id,
                    )
                    meta_bulk.append(meta_orm)
                if len(meta_bulk) > 1000:
                    sc.bulk_save_objects(meta_bulk)
                    meta_bulk.clear()
            # save any remaining in the bulk
            sc.bulk_save_objects(cat_bulk)
            sc.bulk_save_objects(meta_bulk)
            sc.flush()

    def add_documents(
        self,
        docs: list[str],
        doc_ids: list[int | str] = None,
        timestamps: list[date] = None,
        timestamps_ordinal: list[int] = None,
        categories: list[dict[str, list[str]]] = None,
        metadata: list[dict[str, Any]] = None,
    ):
        if doc_ids is None:
            doc_ids = [None] * len(docs)
        if timestamps is None:
            timestamps = [None] * len(docs)
        if timestamps_ordinal is None:
            timestamps_ordinal = [None] * len(docs)
        if categories is None:
            categories = [{}] * len(docs)
        if metadata is None:
            metadata = [{}] * len(docs)

        assert (
            len(doc_ids)
            == len(timestamps)
            == len(timestamps_ordinal)
            == len(categories)
            == len(metadata)
            == len(docs)
        ), (
            "Document metadata (ids, timestamps, categories) must be the same "
            "length as input documents"
        )

        bulk = []
        doc_cats = []
        doc_meta = []
        with self.get_session_context():
            for (
                doc_text,
                doc_id,
                timestamp,
                timestamp_ordinal,
                categorization,
                meta,
            ) in zip(
                docs,
                doc_ids,
                timestamps,
                timestamps_ordinal,
                categories,
                metadata,
                strict=True,
            ):
                doc_orm = DocumentOrm(
                    text=doc_text,
                    id=doc_id if isinstance(doc_id, int) else None,
                    str_id=doc_id if isinstance(doc_id, str) else None,
                    timestamp=timestamp,
                    timestamp_ordinal=timestamp_ordinal,
                )
                bulk.append(doc_orm)
                doc_cats.append(categorization)
                doc_meta.append(meta)

                if len(bulk) >= 500:
                    self._bulk_save_docs_with_categories_and_meta(
                        bulk, doc_cats, doc_meta
                    )
                    bulk.clear()
                    doc_cats.clear()
                    doc_meta.clear()

            # save any remaining in the bulk
            self._bulk_save_docs_with_categories_and_meta(bulk, doc_cats, doc_meta)

    def get_docs(
        self,
    ) -> list[DocumentOrm]:
        with self.get_session_context() as sc:
            return sc.query(DocumentOrm).all()

    OccurrenceLookup = dict[tuple[int, int, str], EntityOccurrenceOrm]

    def add_entity_occurrences(
        self,
        doc: DocumentOrm,
        entities: list[SpanAnnotation],
    ) -> OccurrenceLookup:
        """Add entity occurrences up-front. Returns lookup dict for add_triplets and
        add_tuplets."""
        with self.get_session_context() as sc:
            # Deduplicate by span position and build lookup
            lookup: PopulationService.OccurrenceLookup = {}
            for entity in entities:
                key = (entity.start_char, entity.end_char, entity.text)
                if key not in lookup:
                    lookup[key] = EntityOccurrenceOrm(
                        doc_id=doc.id,
                        span_start=entity.start_char,
                        span_end=entity.end_char,
                        span_text=entity.text,
                    )

            sc.add_all(lookup.values())
            sc.flush()  # Get IDs assigned
            return lookup

    def add_triplets(
        self,
        doc: DocumentOrm,
        triplets: list[Triplet],
        occurrence_lookup: OccurrenceLookup,
    ):
        """Add triplets that reference entity occurrences from the lookup."""
        with self.get_session_context() as sc:
            triplet_orms = [
                TripletOrm(
                    doc_id=doc.id,
                    subject_occurrence_id=occurrence_lookup[
                        (
                            triplet.subj.start_char,
                            triplet.subj.end_char,
                            triplet.subj.text,
                        )
                    ].id,
                    object_occurrence_id=occurrence_lookup[
                        (triplet.obj.start_char, triplet.obj.end_char, triplet.obj.text)
                    ].id,
                    pred_span_start=triplet.pred.start_char,
                    pred_span_end=triplet.pred.end_char,
                    pred_span_text=triplet.pred.text,
                    context=triplet.context.text if triplet.context else None,
                    context_offset=triplet.context.doc_offset
                    if triplet.context
                    else None,
                )
                for triplet in triplets
            ]
            sc.bulk_save_objects(triplet_orms)

    def add_tuplets(
        self,
        doc: DocumentOrm,
        tuplets: list[Tuplet],
        occurrence_lookup: OccurrenceLookup,
    ):
        """Add tuplets that reference entity occurrences from the lookup."""
        with self.get_session_context() as sc:
            tuplet_orms = [
                TupletOrm(
                    doc_id=doc.id,
                    entity_one_occurrence_id=occurrence_lookup[
                        (
                            tuplet.entity_one.start_char,
                            tuplet.entity_one.end_char,
                            tuplet.entity_one.text,
                        )
                    ].id,
                    entity_two_occurrence_id=occurrence_lookup[
                        (
                            tuplet.entity_two.start_char,
                            tuplet.entity_two.end_char,
                            tuplet.entity_two.text,
                        )
                    ].id,
                    context=tuplet.context.text if tuplet.context else None,
                    context_offset=tuplet.context.doc_offset
                    if tuplet.context
                    else None,
                )
                for tuplet in tuplets
            ]
            sc.bulk_save_objects(tuplet_orms)

    def _map_occurrences_to_entities(self, sc, entity_cache: EntityCache):
        """Map all unmapped occurrences to their corresponding entities."""
        occurrences = self.get_entity_occurrences()
        for occ in occurrences:
            occ.entity_id = entity_cache.get_entity_id(occ.span_text)

    def _map_tuplets(self, sc, entity_cache: EntityCache):
        """Map tuplets to entities and cooccurrences."""
        tuplets = self.get_tuplets()
        cooc_cache = CooccurrenceCache(sc, entity_cache, tuplets)
        for tuplet in tuplets:
            entity_one_id = entity_cache.get_entity_id(
                tuplet.entity_one_occurrence.span_text
            )
            entity_two_id = entity_cache.get_entity_id(
                tuplet.entity_two_occurrence.span_text
            )
            cooccurrence_id = cooc_cache.get_cooccurrence_id(
                entity_one_id,
                entity_two_id,
            )

            tuplet.entity_one_id = entity_one_id
            tuplet.entity_two_id = entity_two_id
            tuplet.cooccurrence_id = cooccurrence_id

    def map_tuplets(
        self,
        entity_mappings: dict[str, str],
    ):
        with self.get_session_context() as sc:
            entity_cache = EntityCache(sc, entity_mappings)
            self._map_tuplets(sc, entity_cache)
            self._map_occurrences_to_entities(sc, entity_cache)

    def _map_triplets(
        self,
        sc,
        entity_cache: EntityCache,
        predicate_cache: PredicateCache,
        relation_cache: RelationCache,
    ):
        """Map triplets to entities, predicates, and relations."""
        triplets = self.get_triplets()
        for triplet in triplets:
            subject_id = entity_cache.get_entity_id(
                triplet.subject_occurrence.span_text
            )
            predicate_id = predicate_cache.get_predicate_id(
                triplet.pred_span_text,
            )
            object_id = entity_cache.get_entity_id(triplet.object_occurrence.span_text)
            relation_id = relation_cache.get_relation_id(
                subject_id,
                predicate_id,
                object_id,
            )
            triplet.subject_id = subject_id
            triplet.predicate_id = predicate_id
            triplet.object_id = object_id
            triplet.relation_id = relation_id

    def map_tuplets_and_triplets(
        self,
        entity_mappings: dict[str, str],
        predicate_mappings: dict[str, str],
    ):
        """Map triplets and tuplets to entities, predicates, and relations."""
        with self.get_session_context() as sc:
            entity_cache = EntityCache(sc, entity_mappings)
            self._map_tuplets(sc, entity_cache)

            predicate_cache = PredicateCache(sc, predicate_mappings)
            relation_cache = RelationCache(
                sc, entity_cache, predicate_cache, self.get_triplets()
            )
            self._map_triplets(sc, entity_cache, predicate_cache, relation_cache)

            # Map occurrences to entities after all tuplets and triplets are mapped
            self._map_occurrences_to_entities(sc, entity_cache)

    def get_triplets(self):
        with self.get_session_context() as sc:
            return sc.query(TripletOrm).all()

    def get_tuplets(self):
        with self.get_session_context() as sc:
            return sc.query(TupletOrm).all()

    def get_entity_occurrences(self):
        with self.get_session_context() as sc:
            return sc.query(EntityOccurrenceOrm).all()
