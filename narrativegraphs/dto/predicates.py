from narrativegraphs.db.predicates import PredicateOrm
from narrativegraphs.dto.common import (
    LabeledTextOccurrence,
    TextOccurrenceStats,
)


class PredicateDetails(LabeledTextOccurrence):
    @classmethod
    def from_orm(cls, predicate_orm: PredicateOrm) -> "PredicateDetails":
        return cls(
            id=predicate_orm.id,
            label=predicate_orm.label,
            stats=TextOccurrenceStats.from_mixin(predicate_orm),
            alt_labels=predicate_orm.alt_labels,
            categories=predicate_orm.category_dict,
        )
