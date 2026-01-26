from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import aliased

from narrativegraphs.db.cooccurrences import CooccurrenceCategory, CooccurrenceOrm
from narrativegraphs.db.documents import DocumentOrm
from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.tuplets import TupletOrm
from narrativegraphs.dto.cooccurrences import CooccurrenceDetails
from narrativegraphs.service.common import OrmAssociatedService


class CooccurrenceService(OrmAssociatedService):
    _orm = CooccurrenceOrm
    _category_orm = CooccurrenceCategory

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()

            # Create aliases for the two entity joins
            entity_one = aliased(EntityOrm)
            entity_two = aliased(EntityOrm)

            df = pd.read_sql(
                select(
                    CooccurrenceOrm.id.label("id"),
                    entity_one.label.label("entity_one"),
                    entity_one.frequency.label("entity_one_frequency"),
                    entity_two.label.label("entity_two"),
                    entity_two.frequency.label("entity_two_frequency"),
                    *CooccurrenceOrm.stats_columns(),
                    CooccurrenceOrm.pmi.label("pmi"),
                    entity_one.id.label("entity_one_id"),
                    entity_two.id.label("entity_two_id"),
                )
                .join(
                    entity_one,
                    CooccurrenceOrm.entity_one_id == entity_one.id,
                )
                .join(
                    entity_two,
                    CooccurrenceOrm.entity_two_id == entity_two.id,
                ),
                engine,
            )

            with_categories = self._add_category_columns(df)
        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def get_single(self, id_: int) -> CooccurrenceDetails:
        return self._get_by_id_and_transform(id_, CooccurrenceDetails.from_orm)

    def get_multiple(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[CooccurrenceDetails]:
        return self._get_multiple_by_ids_and_transform(
            CooccurrenceDetails.from_orm, ids=ids, limit=limit
        )

    def doc_ids_by_cooccurrence(
        self, cooccurrence_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self._get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TupletOrm)
                .filter(TupletOrm.cooccurrence_id == cooccurrence_id)
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]
