from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import aliased

from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.predicates import PredicateOrm
from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.service.common import OrmAssociatedService


class TripletService(OrmAssociatedService):
    _orm = TripletOrm

    def as_df(self) -> pd.DataFrame:
        with self._get_session_context() as session:
            engine = session.get_bind()

            # Create aliases for the two entity joins
            subject_entity = aliased(EntityOrm)
            object_entity = aliased(EntityOrm)

            df = pd.read_sql(
                select(
                    TripletOrm.id.label("id"),
                    subject_entity.id.label("subject_entity_id"),
                    subject_entity.label.label("subject_label"),
                    TripletOrm.subj_span_text.label("subject_span_text"),
                    TripletOrm.subj_span_start.label("subject_span_start"),
                    TripletOrm.subj_span_end.label("subject_span_end"),
                    PredicateOrm.id.label("predicate_id"),
                    PredicateOrm.label.label("predicate_label"),
                    TripletOrm.pred_span_text.label("pred_span_text"),
                    object_entity.id.label("object_entity_id"),
                    object_entity.label.label("object_label"),
                    TripletOrm.obj_span_text.label("object_span_text"),
                    TripletOrm.obj_span_start.label("object_span_start"),
                    TripletOrm.obj_span_end.label("object_span_end"),
                )
                .join(PredicateOrm)
                .join(
                    subject_entity,
                    TripletOrm.subject_id == subject_entity.id,
                )
                .join(
                    object_entity,
                    TripletOrm.object_id == object_entity.id,
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
