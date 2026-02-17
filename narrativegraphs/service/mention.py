from typing import Optional

import pandas as pd
from sqlalchemy import select

from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.entityoccurrences import EntityOccurrenceOrm
from narrativegraphs.dto.common import IdentifiableSpan
from narrativegraphs.service.common import OrmAssociatedService


class EntityMentionService(OrmAssociatedService):
    _orm = EntityOccurrenceOrm

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()
            df = pd.read_sql(
                select(
                    EntityOccurrenceOrm.id.label("id"),
                    EntityOrm.id.label("entity_id"),
                    EntityOrm.label.label("entity_label"),
                    EntityOccurrenceOrm.span_text.label("entity_span_text"),
                    EntityOccurrenceOrm.span_start.label("entity_span_start"),
                    EntityOccurrenceOrm.span_end.label("entity_span_end"),
                ).join(
                    EntityOrm,
                    EntityOccurrenceOrm.entity_id == EntityOrm.id,
                ),
                engine,
            )

        cleaned = df.dropna(axis=1, how="all")

        return cleaned

    def get_single(self, id_: int) -> dict:
        return self._get_by_id_and_transform(
            id_, IdentifiableSpan.from_entity_occurrence_orm
        )

    def get_multiple(
        self, ids: list[int] = None, limit: Optional[int] = None
    ) -> list[dict]:
        return self._get_multiple_by_ids_and_transform(
            IdentifiableSpan.from_entity_occurrence_orm, ids=ids, limit=limit
        )

    def get_by_entity_ids(self, entity_ids: list[int]) -> list[IdentifiableSpan]:
        with self._get_session_context() as session:
            occurrences = (
                session.query(EntityOccurrenceOrm)
                .filter(EntityOccurrenceOrm.entity_id.in_(entity_ids))
                .all()
            )
            return [
                IdentifiableSpan.from_entity_occurrence_orm(occ) for occ in occurrences
            ]
