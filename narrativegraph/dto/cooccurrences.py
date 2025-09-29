from narrativegraph.db.cooccurrences import CoOccurrenceOrm
from narrativegraph.dto.common import (
    TextOccurrenceStats,
    TextOccurrence,
)


class CoOccurrenceStats(TextOccurrenceStats):
    pmi: float

    @classmethod
    def from_mixin(cls, orm: CoOccurrenceOrm):
        base_data = TextOccurrenceStats.from_mixin(orm).model_dump()
        return cls(
            **base_data,
            pmi=orm.pmi,
        )


class CoOccurrenceDetails(TextOccurrence):

    @classmethod
    def from_orm(cls, co_occurrence_orm: CoOccurrenceOrm) -> "CoOccurrenceDetails":
        return cls(
            id=co_occurrence_orm.id,
            stats=CoOccurrenceStats.from_mixin(co_occurrence_orm),
            categories=co_occurrence_orm.category_dict,
        )
