from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import aliased

from narrativegraph.db.cooccurrences import CoOccurrenceCategory, CoOccurrenceOrm
from narrativegraph.db.documents import DocumentOrm
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.triplets import TripletOrm
from narrativegraph.dto.cooccurrences import CoOccurrenceDetails
from narrativegraph.service.common import OrmAssociatedService


class CoOccurrencesService(OrmAssociatedService):
    _orm = CoOccurrenceOrm
    _category_orm = CoOccurrenceCategory

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()

            # Create aliases for the two entity joins
            entity_one = aliased(EntityOrm)
            entity_two = aliased(EntityOrm)

            df = pd.read_sql(
                select(
                    CoOccurrenceOrm.id.label("id"),
                    entity_one.label.label("entity_one"),
                    entity_one.frequency.label("entity_one_frequency"),
                    entity_two.label.label("entity_two"),
                    entity_two.frequency.label("entity_two_frequency"),
                    *CoOccurrenceOrm.stats_columns(),
                    CoOccurrenceOrm.pmi.label("pmi"),
                    entity_one.id.label("entity_one_id"),
                    entity_two.id.label("entity_two_id"),
                )
                .join(
                    entity_one,
                    CoOccurrenceOrm.entity_one_id == entity_one.id,
                )
                .join(
                    entity_two,
                    CoOccurrenceOrm.entity_two_id == entity_two.id,
                ),
                engine,
            )

            with_categories = self._add_category_columns(df)
        cleaned = with_categories.dropna(axis=1, how="all")

        return cleaned

    def by_id(self, id_: int) -> CoOccurrenceDetails:
        return self._get_by_id_and_transform(id_, CoOccurrenceDetails.from_orm)

    def get_multiple(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[CoOccurrenceDetails]:
        return self._get_multiple_by_ids_and_transform(
            CoOccurrenceDetails.from_orm, ids=ids, limit=limit
        )

    def doc_ids_by_co_occurrence(
        self, co_occurrence_id: int, limit: Optional[int] = None
    ) -> list[int]:
        with self._get_session_context() as sc:
            query = (
                sc.query(DocumentOrm.id)
                .join(TripletOrm)
                .filter(TripletOrm.co_occurrence_id == co_occurrence_id)
                .distinct()
            )
            if limit:
                query = query.limit(limit)

        return [doc.id for doc in query.all()]
