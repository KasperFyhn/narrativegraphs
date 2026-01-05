from narrativegraph.db.relations import RelationOrm
from narrativegraph.dto.common import (
    LabeledTextOccurrence,
    TextOccurrenceStats,
)


class RelationDetails(LabeledTextOccurrence):
    @classmethod
    def from_orm(cls, relation_orm: RelationOrm) -> "RelationDetails":
        return cls(
            id=relation_orm.id,
            label=relation_orm.label,
            stats=TextOccurrenceStats.from_mixin(relation_orm),
            alt_labels=relation_orm.alt_labels,
            categories=relation_orm.category_dict,
        )
