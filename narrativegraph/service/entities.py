from typing import Optional

import pandas as pd
from sqlalchemy import select

from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.entities import EntityOrm, EntityCategory
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.dto.entities import (
    EntityLabel,
    EntityDetails,
)
from narrativegraph.service.common import OrmAssociatedService


class EntityService(OrmAssociatedService):
    _orm = EntityOrm
    _category_orm = EntityCategory

    def as_df(self) -> pd.DataFrame:
        with self.get_session_context() as session:
            engine = session.get_bind()

            entities_df = pd.read_sql(
                select(
                    EntityOrm.id.label("id"),
                    EntityOrm.label.label("label"),
                    *EntityOrm.stats_columns(),
                    EntityOrm.alt_labels.label("alt_labels")
                ),
                engine,
            )

            with_categories = self._add_category_columns(entities_df)

        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def by_id(self, id_: int) -> EntityDetails:
        return self._get_by_id_and_transform(id_, EntityDetails.from_orm)

    def by_ids(
        self, ids: list[int], limit: Optional[int] = None
    ) -> list[EntityDetails]:
        return self._get_multiple_by_ids_and_transform(
            ids, EntityDetails.from_orm, limit=limit
        )

    def doc_ids_by_entity(
        self, entity_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self.get_session_context() as sc:
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
        with self.get_session_context() as sc:
            entities = (
                sc.query(EntityOrm.id, EntityOrm.label)
                .filter(EntityOrm.id.in_(entity_ids))
                .all()
            )

            return [
                EntityLabel(id=entity.id, label=entity.label) for entity in entities
            ]
