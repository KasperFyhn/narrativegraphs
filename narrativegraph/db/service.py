from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from tqdm import tqdm

from narrativegraph.db.cache import EntityAndRelationCache
from narrativegraph.db.engine import get_engine, setup_database, get_session
from narrativegraph.db.orms import DocumentOrm, TripletOrm, RelationOrm
from narrativegraph.extraction.common import Triplet


class DbService:

    def __init__(self, db_filepath: str | Path = None):
        # Setup
        self._engine = get_engine(db_filepath)
        setup_database(self._engine)
        self._session = get_session(self._engine)

    @property
    def session(self) -> Session:
        return self._session
        

    def add_documents(self, docs: list[str], doc_ids: list[int | str] = None, timestamps: list[datetime] = None,
                      categories: list[str] = None):
        if doc_ids is None:
            doc_ids = [None] * len(docs)
        if timestamps is None:
            timestamps = [None] * len(docs)
        if categories is None:
            categories = [None] * len(docs)

        assert len(doc_ids) == len(timestamps) == len(categories) == len(docs), \
            "Document metadata (ids, timestamps, categories) must be the same length as input documents"

        bulk = []
        for doc_text, doc_id, timestamp, category in zip(docs, doc_ids, timestamps, categories, strict=True):
            doc_orm = DocumentOrm(
                text=doc_text,
                id=doc_id if isinstance(doc_id, int) else None,
                str_id=doc_id if isinstance(doc_id, str) else None,
                timestamp=timestamp,
                category=category
            )
            bulk.append(doc_orm)

            if len(bulk) >= 500:
                self._session.bulk_save_objects(bulk)
                bulk.clear()

        # save any remaining in the bulk
        self._session.bulk_save_objects(bulk)

        self._session.commit()

    def get_docs(self):
        return self._session.query(DocumentOrm).all()

    def add_triplets(self, doc_id: int, triplets: list[Triplet], category: str = None):
        triplet_orms = [
                TripletOrm(
                    doc_id=doc_id,
                    subj_span_start=triplet.subject.start_char,
                    subj_span_end=triplet.subject.end_char,
                    subj_span_text=triplet.subject.text,
                    pred_span_start=triplet.predicate.start_char,
                    pred_span_end=triplet.predicate.end_char,
                    pred_span_text=triplet.predicate.text,
                    obj_span_start=triplet.obj.start_char,
                    obj_span_end=triplet.obj.end_char,
                    obj_span_text=triplet.obj.text,
                    category=category
                )
                for triplet in triplets
            ]
        self._session.bulk_save_objects(triplet_orms)
        self._session.commit()

    def map_triplets(self, entity_mappings: dict[str, str],
                     relation_mappings: dict[str, str]):
        cache = EntityAndRelationCache(self._session, entity_mappings, relation_mappings)

        for triplet in tqdm(self._session.query(TripletOrm).all(), desc="Mapping triplets"):
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

        self._session.commit()

        cache.update_entity_info()
        cache.update_relation_info()

    def get_triplets(self):
        return self._session.query(TripletOrm).all()

    def get_relations(self, n: int = None) -> list[RelationOrm]:
        with (get_session(self._engine) as session):
            return self._session.query(RelationOrm).limit(n).all()  # noqa
