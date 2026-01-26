from typing import Optional

import pandas as pd
from sqlalchemy import case, func, select

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.db.entities import EntityCategory, EntityOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.dto.entities import (
    EntityDetails,
    EntityLabel,
)
from narrativegraphs.service.common import OrmAssociatedService


class EntityService(OrmAssociatedService):
    _orm = EntityOrm
    _category_orm = EntityCategory

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()

            df = pd.read_sql(
                select(
                    EntityOrm.id.label("id"),
                    EntityOrm.label.label("label"),
                    *EntityOrm.stats_columns(),
                    EntityOrm.alt_labels.label("alt_labels"),
                ),
                engine,
            )

            with_categories = self._add_category_columns(df)

        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def get_single(self, id_: int) -> EntityDetails:
        return self._get_by_id_and_transform(id_, EntityDetails.from_orm)

    def get_multiple(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[EntityDetails]:
        return self._get_multiple_by_ids_and_transform(
            EntityDetails.from_orm, ids=ids, limit=limit
        )

    def doc_ids_by_entity(
        self, entity_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self._get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(
                    (TripletOrm.subject_id == entity_id)
                    | (TripletOrm.object_id == entity_id)
                )
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]

    def labels_by_ids(self, entity_ids: list[int]) -> list[EntityLabel]:
        with self._get_session_context() as sc:
            entities = (
                sc.query(EntityOrm.id, EntityOrm.label)
                .filter(EntityOrm.id.in_(entity_ids))
                .all()
            )

            return [
                EntityLabel(id=entity.id, label=entity.label) for entity in entities
            ]

    def search(self, label_search: str, limit: int = None) -> list[EntityLabel]:
        with self._get_session_context() as sc:
            search_lower = label_search.lower()

            match_quality = case(
                (func.lower(EntityOrm.label) == search_lower, 0),  # exact
                (func.lower(EntityOrm.label).startswith(search_lower), 1),  # prefix
                else_=2,  # contains
            )

            matches = (
                sc.query(EntityOrm.id, EntityOrm.label)
                .filter(EntityOrm.label.ilike(f"%{label_search}%"))
                .order_by(
                    match_quality,
                    EntityOrm.frequency.desc(),  # more frequent = better
                    func.length(EntityOrm.label),  # shorter = better
                    EntityOrm.label,  # alphabetical tiebreaker
                )
                .limit(limit)
                .all()
            )
            return [EntityLabel.from_orm(entity) for entity in matches]
