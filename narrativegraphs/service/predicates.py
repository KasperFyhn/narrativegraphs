from typing import Optional

import pandas as pd
from sqlalchemy import select

from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.db.predicates import PredicateCategory, PredicateOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.dto.predicates import (
    PredicateDetails,
)
from narrativegraphs.service.common import OrmAssociatedService


class PredicateService(OrmAssociatedService):
    _orm = PredicateOrm
    _category_orm = PredicateCategory

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()

            df = pd.read_sql(
                select(
                    PredicateOrm.id.label("id"),
                    PredicateOrm.label.label("label"),
                    *PredicateOrm.stats_columns(),
                    PredicateOrm.alt_labels.label("alt_labels"),
                ),
                engine,
            )

            with_categories = self._add_category_columns(df)
        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def get_single(self, id_: int) -> PredicateDetails:
        return self._get_by_id_and_transform(id_, PredicateDetails.from_orm)

    def get_multiple(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[PredicateDetails]:
        return self._get_multiple_by_ids_and_transform(
            PredicateDetails.from_orm, ids=ids, limit=limit
        )

    def doc_ids_by_predicate(
        self, predicate_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self._get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(TripletOrm.predicate_id == predicate_id)
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]
