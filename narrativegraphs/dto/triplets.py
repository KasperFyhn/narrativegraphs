from typing import Optional

from fastapi_camelcase import CamelModel

from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.dto.common import SpanEntity, TextContext


class Triplet(CamelModel):
    subject: SpanEntity
    predicate: SpanEntity
    object: SpanEntity
    context: Optional[TextContext] = None

    @classmethod
    def from_orm(cls, triplet_orm: TripletOrm) -> "Triplet":
        return cls(
            subject=SpanEntity(
                id=triplet_orm.subject_id,
                start=triplet_orm.subj_span_start,
                end=triplet_orm.subj_span_end,
            ),
            predicate=SpanEntity(
                id=triplet_orm.predicate_id,
                start=triplet_orm.pred_span_start,
                end=triplet_orm.pred_span_end,
            ),
            object=SpanEntity(
                id=triplet_orm.object_id,
                start=triplet_orm.obj_span_start,
                end=triplet_orm.obj_span_end,
            ),
            context=TextContext(
                doc_id=triplet_orm.doc_id,
                text=triplet_orm.context,
                doc_offset=triplet_orm.context_offset,
            ),
        )

    @classmethod
    def from_orms(cls, triplet_orms: list[TripletOrm]) -> list["Triplet"]:
        return [cls.from_orm(orm) for orm in triplet_orms]
