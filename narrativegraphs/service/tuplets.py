from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import aliased

from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.entityoccurrences import EntityOccurrenceOrm
from narrativegraphs.db.tuplets import TupletOrm
from narrativegraphs.dto.common import TextContext
from narrativegraphs.dto.tuplets import Tuplet, TupletGroup
from narrativegraphs.service.common import OrmAssociatedService


class TupletService(OrmAssociatedService):
    _orm = TupletOrm

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()

            # Create aliases for the two entity joins
            entity_one = aliased(EntityOrm)
            entity_two = aliased(EntityOrm)
            # Create aliases for the two occurrence joins
            entity_one_occurrence = aliased(EntityOccurrenceOrm)
            entity_two_occurrence = aliased(EntityOccurrenceOrm)

            df = pd.read_sql(
                select(
                    TupletOrm.id.label("id"),
                    entity_one.id.label("entity_one_id"),
                    entity_one.label.label("entity_one_label"),
                    entity_one_occurrence.span_text.label("entity_one_span_text"),
                    entity_one_occurrence.span_start.label("entity_one_span_start"),
                    entity_one_occurrence.span_end.label("entity_one_span_end"),
                    entity_two.id.label("entity_two_id"),
                    entity_two.label.label("entity_two_label"),
                    entity_two_occurrence.span_text.label("entity_two_span_text"),
                    entity_two_occurrence.span_start.label("entity_two_span_start"),
                    entity_two_occurrence.span_end.label("entity_two_span_end"),
                )
                .join(
                    entity_one_occurrence,
                    TupletOrm.entity_one_occurrence_id == entity_one_occurrence.id,
                )
                .join(
                    entity_two_occurrence,
                    TupletOrm.entity_two_occurrence_id == entity_two_occurrence.id,
                )
                .join(
                    entity_one,
                    TupletOrm.entity_one_id == entity_one.id,
                )
                .join(
                    entity_two,
                    TupletOrm.entity_two_id == entity_two.id,
                ),
                engine,
            )

        cleaned = df.dropna(axis=1, how="all")

        return cleaned

    def get_single(self, id_: int) -> dict:
        return self._get_by_id_and_transform(id_, lambda x: x.__dict__)

    def get_multiple(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[dict]:
        return self._get_multiple_by_ids_and_transform(
            lambda x: x.__dict__, ids=ids, limit=limit
        )

    def get_by_entity_ids(self, entity_ids: list[int]) -> list[Tuplet]:
        with self._get_session_context() as session:
            tuplets = (
                session.query(TupletOrm)
                .filter(
                    TupletOrm.entity_one_id.in_(entity_ids)
                    & TupletOrm.entity_two_id.in_(entity_ids)
                )
                .all()
            )
            return [Tuplet.from_orm(tuplet) for tuplet in tuplets]

    def get_contexts_by_entity_ids(
        self, entity_ids: list[int], remove_self_loops: bool = True
    ) -> list[TupletGroup]:
        tuplets = self.get_by_entity_ids(entity_ids)
        tuplet_groups = [
            TupletGroup.from_tuplet(tuplet)
            for tuplet in tuplets
            if tuplet.entity_one.id != tuplet.entity_two.id or not remove_self_loops
        ]
        return TextContext.combine_many(tuplet_groups)
