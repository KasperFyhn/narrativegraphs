from narrativegraphs.db.cooccurrences import CooccurrenceOrm
from narrativegraphs.dto.common import (
    TextOccurrence,
    TextOccurrenceStats,
)


class CooccurrenceStats(TextOccurrenceStats):
    pmi: float

    @classmethod
    def from_mixin(cls, orm: CooccurrenceOrm):
        base_data = TextOccurrenceStats.from_mixin(orm).model_dump()
        return cls(
            **base_data,
            pmi=orm.pmi,
        )


class CooccurrenceDetails(TextOccurrence):
    entity_one_id: int
    entity_two_id: int
    stats: CooccurrenceStats

    @classmethod
    def from_orm(cls, cooccurrence_orm: CooccurrenceOrm) -> "CooccurrenceDetails":
        return cls(
            id=cooccurrence_orm.id,
            stats=CooccurrenceStats.from_mixin(cooccurrence_orm),
            categories=cooccurrence_orm.category_dict,
            entity_one_id=cooccurrence_orm.entity_one_id,
            entity_two_id=cooccurrence_orm.entity_two_id,
        )
