from datetime import date

from sqlalchemy.orm import Session, InstrumentedAttribute
from tqdm import tqdm

from narrativegraph.db.orms import (
    DocumentOrm,
    TripletOrm,
    DocumentCategory, EntityOrm, RelationOrm, EntityCategory, RelationCategory,
)
from narrativegraph.nlp.extraction.common import Triplet
from narrativegraph.service.common import DbService


class PopulationService(DbService):

    def _bulk_save_with_categories(
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
            categories = [None] * len(docs)

        assert (
            len(doc_ids) == len(timestamps) == len(categories) == len(docs)
        ), "Document metadata (ids, timestamps, categories) must be the same length as input documents"

        bulk = []
        doc_cats = []
        with self.get_session_context() as sc:
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
                    self._bulk_save_with_categories(bulk, doc_cats)
                    bulk.clear()
                    doc_cats.clear()

            # save any remaining in the bulk
            self._bulk_save_with_categories(bulk, doc_cats)

    def get_docs(
        self,
    ) -> list[DocumentOrm]:
        with self.get_session_context() as sc:
            return sc.query(DocumentOrm).all()

    def add_triplets(
        self,
        doc_id: int,
        triplets: list[Triplet],
    ):
        with self.get_session_context() as sc:
            triplet_orms = [
                TripletOrm(
                    doc_id=doc_id,
                    subj_span_start=triplet.subj.start_char,
                    subj_span_end=triplet.subj.end_char,
                    subj_span_text=triplet.subj.text,
                    pred_span_start=triplet.pred.start_char,
                    pred_span_end=triplet.pred.end_char,
                    pred_span_text=triplet.pred.text,
                    obj_span_start=triplet.obj.start_char,
                    obj_span_end=triplet.obj.end_char,
                    obj_span_text=triplet.obj.text,
                )
                for triplet in triplets
            ]
            sc.bulk_save_objects(triplet_orms)

    def map_triplets(
        self,
        entity_mappings: dict[str, str],
        relation_mappings: dict[str, str],
    ):
        with self.get_session_context() as sc:
            cache = EntityAndRelationCache(sc, entity_mappings, relation_mappings)

            for triplet in tqdm(sc.query(TripletOrm).all(), desc="Mapping triplets"):
                subject_id = cache.get_or_create_entity(triplet.subj_span_text)
                object_id = cache.get_or_create_entity(triplet.obj_span_text)
                relation_id = cache.get_or_create_relation(
                    subject_id,
                    object_id,
                    triplet.pred_span_text,
                )

                triplet.subject_id = subject_id
                triplet.relation_id = relation_id
                triplet.object_id = object_id

            sc.commit()

            cache.update_entity_info()
            cache.update_relation_info()

    def get_triplets(
        self,
    ):
        with self.get_session_context() as sc:
            return sc.query(TripletOrm).all()


class EntityAndRelationCache:

    def __init__(
        self,
        session: Session,
        entity_mappings: dict[str, str],
        predicate_mappings: dict[str, str],
    ):
        self._session = session
        self._entities = {str(e.label): e for e in session.query(EntityOrm).all()}
        self._relations = {
            (int(r.subject_id), str(r.label), int(r.object_id)): r  # noqa
            for r in session.query(RelationOrm).all()
        }

        self._entity_mappings = entity_mappings
        self._predicate_mappings = predicate_mappings

    def get_or_create_entity(self, label: InstrumentedAttribute[str] | str):
        """Fetch an entity by label, or create it if it doesn't exist."""
        mapped_entity = self._entity_mappings[label]

        entity = self._entities.get(mapped_entity, None)
        if entity is None:
            entity = EntityOrm(label=mapped_entity)
            self._session.add(entity)
            self._session.flush()  # Get the ID immediately
            self._entities[mapped_entity] = entity  # noqa
        return entity.id

    def get_or_create_relation(
        self,
        subject_id: int,
        object_id: int,
        predicate_label: InstrumentedAttribute[str] | str,
    ):
        """Fetch a relation by label, or create it if it doesn't exist."""
        mapped_predicate = self._predicate_mappings[predicate_label]
        relation_key = (
            subject_id,
            mapped_predicate,
            object_id,
        )

        relation = self._relations.get(relation_key, None)
        if relation is None:
            relation = RelationOrm(
                label=mapped_predicate,
                subject_id=subject_id,
                object_id=object_id,
            )
            self._session.add(relation)
            self._session.flush()  # Get the ID immediately
            self._relations[relation_key] = relation  # noqa
        return relation.id

    def update_entity_info(self):
        for entity in tqdm(self._entities.values(), desc="Updating entity info"):
            as_subject = len(entity.subject_triplets)  # noqa
            as_object = len(entity.object_triplets)  # noqa

            entity.term_frequency = as_subject + as_object

            triplets = entity.subject_triplets + entity.object_triplets
            entity.doc_frequency = len(
                set(t.doc_id for t in triplets),
            )
            dates = [t.timestamp for t in triplets if t.timestamp is not None]

            category_orms = EntityCategory.from_triplets(entity.id, triplets)
            self._session.add_all(category_orms)

            entity.first_occurrence = min(dates, default=None)
            entity.last_occurrence = max(dates, default=None)
            # super_entity = self._mappings.get_super_entity(entity.label)
            # if super_entity is not None:
            #     entity.supernode_id = self.get_or_create_entity(super_entity)
            #     entity.is_supernode = entity.id == entity.supernode_id
        self._session.commit()

    def update_relation_info(self):
        for relation in tqdm(
            self._relations.values(),
            desc="Updating relation info",
        ):
            relation.term_frequency = len(relation.triplets)  # noqa
            relation.doc_frequency = len(set(t.doc_id for t in relation.triplets))
            dates = [t.timestamp for t in relation.triplets if t.timestamp is not None]
            relation.first_occurrence = min(dates, default=None)
            relation.last_occurrence = max(dates, default=None)

            category_orms = RelationCategory.from_triplets(
                relation.id, relation.triplets
            )
            self._session.add_all(category_orms)

        self._session.commit()
