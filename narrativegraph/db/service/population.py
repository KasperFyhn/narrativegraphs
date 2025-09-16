from datetime import date
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session
from tqdm import tqdm

from narrativegraph.db.cache import EntityAndRelationCache
from narrativegraph.db.dtos import Document, transform_orm_to_dto, Node
from narrativegraph.db.orms import (
    DocumentOrm,
    TripletOrm,
    RelationOrm,
    DocumentCategory,
    EntityOrm,
)
from narrativegraph.db.service.common import DbService
from narrativegraph.extraction.common import Triplet


class PopulationService(DbService):

    def _bulk_save_with_categories(
        self,
        bulk: list[DocumentOrm],
        categories: list[dict[str, list[str]]],
    ) -> None:
        with self.open_session() as sc:
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
        with self.open_session() as sc:
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
        with self.open_session() as sc:
            return sc.query(DocumentOrm).all()

    def add_triplets(
        self,
        doc_id: int,
        triplets: list[Triplet],
    ):
        with self.open_session() as sc:
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
        with self.open_session() as sc:
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
        with self.open_session() as sc:
            return sc.query(TripletOrm).all()
