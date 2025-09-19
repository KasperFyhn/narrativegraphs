from typing import Optional

import pandas as pd
from sqlalchemy import select

from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.predicates import PredicateOrm, PredicateCategory
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.dto.predicates import (
    PredicateDetails,
)
from narrativegraph.service.common import OrmAssociatedService


class PredicateService(OrmAssociatedService):
    _orm = PredicateOrm
    _category_orm = PredicateCategory

    def as_df(self) -> pd.DataFrame:
        with self.get_session_context() as session:
            engine = session.get_bind()

            entities_df = pd.read_sql(
                select(
                    PredicateOrm.id.label("id"),
                    PredicateOrm.label.label("label"),
                    *PredicateOrm.stats_columns(),
                    PredicateOrm.alt_labels.label("alt_labels")
                ),
                engine,
            )

            with_categories = self._add_category_columns(entities_df)
        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def by_id(self, id_: int) -> PredicateDetails:
        return self._get_by_id_and_transform(id_, PredicateDetails.from_orm)

    def by_ids(
        self, ids: list[int], limit: Optional[int] = None
    ) -> list[PredicateDetails]:
        return self._get_multiple_by_ids_and_transform(
            ids, PredicateDetails.from_orm, limit=limit
        )

    def doc_ids_by_predicate(
        self, predicate_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self.get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(TripletOrm.predicate_id == predicate_id)
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]
