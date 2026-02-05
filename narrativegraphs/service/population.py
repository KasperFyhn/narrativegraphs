from datetime import date

from tqdm import tqdm

from narrativegraphs.db.documents import DocumentCategory, DocumentOrm
from narrativegraphs.db.triplets import (
    TripletOrm,
)
from narrativegraphs.db.tuplets import TupletOrm
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
    def _bulk_save_docs_with_categories(
        self,
        bulk: list[DocumentOrm],
        categories: list[dict[str, list[str]]],
    ) -> None:
        with self.get_session_context() as sc:
            sc.add_all(bulk)
            sc.flush()
            cat_bulk = []
            for item, cat_dict in zip(bulk, categories):
                for name, values in cat_dict.items():
                    for value in values:
                        cat_orm = DocumentCategory(
                            target_id=item.id,
                            name=name,
                            value=value,
                        )
                        cat_bulk.append(cat_orm)
                if len(cat_bulk) > 1000:
                    sc.bulk_save_objects(cat_bulk)
            # save any remaining in the bulk
            sc.bulk_save_objects(cat_bulk)
            sc.flush()

    def add_documents(
        self,
        docs: list[str],
        doc_ids: list[int | str] = None,
        timestamps: list[date] = None,
        categories: list[dict[str, list[str]]] = None,
    ):
        if doc_ids is None:
            doc_ids = [None] * len(docs)
        if timestamps is None:
            timestamps = [None] * len(docs)
        if categories is None:
            categories = [{}] * len(docs)

        assert len(doc_ids) == len(timestamps) == len(categories) == len(docs), (
            "Document metadata (ids, timestamps, categories) must be the same "
            "length as input documents"
        )

        bulk = []
        doc_cats = []
        with self.get_session_context():
            for doc_text, doc_id, timestamp, categorization in zip(
                docs, doc_ids, timestamps, categories, strict=True
            ):
                doc_orm = DocumentOrm(
                    text=doc_text,
                    id=doc_id if isinstance(doc_id, int) else None,
                    str_id=doc_id if isinstance(doc_id, str) else None,
                    timestamp=timestamp,
                )
                bulk.append(doc_orm)
                doc_cats.append(categorization)

                if len(bulk) >= 500:
                    self._bulk_save_docs_with_categories(bulk, doc_cats)
                    bulk.clear()
                    doc_cats.clear()

            # save any remaining in the bulk
            self._bulk_save_docs_with_categories(bulk, doc_cats)

    def get_docs(
        self,
    ) -> list[DocumentOrm]:
        with self.get_session_context() as sc:
            return sc.query(DocumentOrm).all()

    def add_triplets(
        self,
        doc: DocumentOrm,
        triplets: list[Triplet],
    ):
        with self.get_session_context() as sc:
            triplet_orms = [
                TripletOrm(
                    doc_id=doc.id,
                    timestamp=doc.timestamp,
                    subj_span_start=triplet.subj.start_char,
                    subj_span_end=triplet.subj.end_char,
                    subj_span_text=triplet.subj.text,
                    pred_span_start=triplet.pred.start_char,
                    pred_span_end=triplet.pred.end_char,
                    pred_span_text=triplet.pred.text,
                    obj_span_start=triplet.obj.start_char,
                    obj_span_end=triplet.obj.end_char,
                    obj_span_text=triplet.obj.text,
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
    ):
        with self.get_session_context() as sc:
            tuplet_orms = [
                TupletOrm(
                    doc_id=doc.id,
                    timestamp=doc.timestamp,
                    entity_one_span_start=tuplet.entity_one.start_char,
                    entity_one_span_end=tuplet.entity_one.end_char,
                    entity_one_span_text=tuplet.entity_one.text,
                    entity_two_span_start=tuplet.entity_two.start_char,
                    entity_two_span_end=tuplet.entity_two.end_char,
                    entity_two_span_text=tuplet.entity_two.text,
                    context=tuplet.context.text if tuplet.context else None,
                    context_offset=tuplet.context.doc_offset
                    if tuplet.context
                    else None,
                )
                for tuplet in tuplets
            ]
            sc.bulk_save_objects(tuplet_orms)

    def _map_tuplets(
        self,
        entity_cache: EntityCache,
    ):
        """Map tuplets to entities and cooccurrences."""
        with self.get_session_context() as sc:
            tuplets = self.get_tuplets()
            cooc_cache = CooccurrenceCache(sc, entity_cache, tuplets)
            if len(tuplets) > 100_000:
                tuplets = tqdm(tuplets, desc="Mapping tuplets")
            for tuplet in tuplets:
                entity_one_id = entity_cache.get_entity_id(tuplet.entity_one_span_text)
                entity_two_id = entity_cache.get_entity_id(tuplet.entity_two_span_text)
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
            return self._map_tuplets(EntityCache(sc, entity_mappings))

    def _map_triplets(
        self,
        entity_cache: EntityCache,
        predicate_cache: PredicateCache,
        relation_cache: RelationCache,
    ):
        """Map triples to entities and cooccurrences."""
        with self.get_session_context():
            triplets = self.get_triplets()
            if len(triplets) > 100_000:
                triplets = tqdm(triplets, desc="Mapping tuplets")
            for triplet in triplets:
                subject_id = entity_cache.get_entity_id(triplet.subj_span_text)
                predicate_id = predicate_cache.get_predicate_id(
                    triplet.pred_span_text,
                )
                object_id = entity_cache.get_entity_id(triplet.obj_span_text)
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
        """Map triplets to entities, predicates, and relations."""

        with self.get_session_context() as sc:
            entity_cache = EntityCache(sc, entity_mappings)
            self._map_tuplets(entity_cache)

            predicate_cache = PredicateCache(sc, predicate_mappings)
            relation_cache = RelationCache(
                sc, entity_cache, predicate_cache, self.get_triplets()
            )
            self._map_triplets(entity_cache, predicate_cache, relation_cache)

    def get_triplets(
        self,
    ):
        with self.get_session_context() as sc:
            return sc.query(TripletOrm).all()

    def get_tuplets(
        self,
    ):
        with self.get_session_context() as sc:
            return sc.query(TupletOrm).all()
