from fastapi_camelcase import CamelModel

from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.db.tuplets import TupletOrm


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
                id=triplet_orm.predicate_id,
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


class Tuplet(CamelModel):
    entity_one: SpanEntity
    entity_two: SpanEntity

    @classmethod
    def from_orm(cls, tuplet_orm: TupletOrm) -> "Tuplet":
        return cls(
            entity_one=SpanEntity(
                id=tuplet_orm.entity_one_id,
                start=tuplet_orm.entity_one_span_start,
                end=tuplet_orm.entity_one_span_end,
            ),
            entity_two=SpanEntity(
                id=tuplet_orm.entity_two_id,
                start=tuplet_orm.entity_two_span_start,
                end=tuplet_orm.entity_two_span_end,
            ),
        )

    @classmethod
    def from_orms(cls, tuplet_orms: list[TupletOrm]) -> list["Tuplet"]:
        return [cls.from_orm(orm) for orm in tuplet_orms]
