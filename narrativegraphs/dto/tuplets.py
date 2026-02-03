from typing import Optional

from fastapi_camelcase import CamelModel

from narrativegraphs.db.tuplets import TupletOrm
from narrativegraphs.dto.common import SpanEntity, TextContext


class Tuplet(CamelModel):
    entity_one: SpanEntity
    entity_two: SpanEntity
    context: Optional[TextContext] = None

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
            context=TextContext(
                doc_id=tuplet_orm.doc_id,
                text=tuplet_orm.context,
                doc_offset=tuplet_orm.context_offset,
            ),
        )

    @classmethod
    def from_orms(cls, tuplet_orms: list[TupletOrm]) -> list["Tuplet"]:
        return [cls.from_orm(orm) for orm in tuplet_orms]
