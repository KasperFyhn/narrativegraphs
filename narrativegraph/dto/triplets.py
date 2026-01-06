from fastapi_camelcase import CamelModel

from narrativegraph.db.triplets import TripletOrm


class SpanEntity(CamelModel):
    id: int
    start: int
    end: int


class Triplet(CamelModel):
    subject: SpanEntity
    predicate: SpanEntity
    object: SpanEntity

    @classmethod
    def from_orm(cls, triplet_orm: TripletOrm) -> "Triplet":
        return cls(
            subject=SpanEntity(
                id=triplet_orm.subject_id,
                start=triplet_orm.subj_span_start,
                end=triplet_orm.subj_span_end,
            ),
            predicate=SpanEntity(
                id=triplet_orm.relation_id,
                start=triplet_orm.pred_span_start,
                end=triplet_orm.pred_span_end,
            ),
            object=SpanEntity(
                id=triplet_orm.object_id,
                start=triplet_orm.obj_span_start,
                end=triplet_orm.obj_span_end,
            ),
        )

    @classmethod
    def from_orms(cls, triplet_orms: list[TripletOrm]) -> list["Triplet"]:
        return [cls.from_orm(orm) for orm in triplet_orms]
