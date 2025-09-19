from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import aliased

from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.predicates import PredicateOrm
from narrativegraph.db.relations import RelationOrm, RelationCategory
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.dto.relations import (
    RelationDetails,
)
from narrativegraph.service.common import OrmAssociatedService


class RelationService(OrmAssociatedService):
    _orm = RelationOrm
    _category_orm = RelationCategory

    def as_df(self) -> pd.DataFrame:
        with self.get_session_context() as session:
            engine = session.get_bind()

            # Create aliases for the two entity joins
            subject_entity = aliased(EntityOrm)
            object_entity = aliased(EntityOrm)

            entities_df = pd.read_sql(
                select(
                    RelationOrm.id.label("id"),
                    subject_entity.label.label("subject"),
                    PredicateOrm.label.label("predicate"),
                    object_entity.label.label("object"),
                    *RelationOrm.stats_columns(),
                    subject_entity.id.label("subject_entity_id"),
                    PredicateOrm.id.label("predicate_id"),
                    object_entity.id.label("object_entity_id"),
                    RelationOrm.alt_labels.label("alt_pred_labels")
                )
                .join(PredicateOrm)
                .join(
                    subject_entity,
                    RelationOrm.subject_id == subject_entity.id,
                )
                .join(
                    object_entity,
                    RelationOrm.object_id == object_entity.id,
                ),
                engine,
            )

            with_categories = self._add_category_columns(entities_df)

        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def by_id(self, id_: int) -> RelationDetails:
        return self._get_by_id_and_transform(id_, RelationDetails.from_orm)

    def by_ids(
        self, ids: list[int], limit: Optional[int] = None
    ) -> list[RelationDetails]:
        return self._get_multiple_by_ids_and_transform(ids, RelationDetails.from_orm)

    def doc_ids_by_relation(
        self, relation_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self.get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(TripletOrm.relation_id == relation_id)
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]
