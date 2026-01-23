from narrativegraph.db.relations import RelationOrm
from narrativegraph.dto.common import (
    LabeledTextOccurrence,
    TextOccurrenceStats,
)


class RelationDetails(LabeledTextOccurrence):
    subject_id: int
    predicate_id: int
    object_id: int

    @classmethod
    def from_orm(cls, relation_orm: RelationOrm) -> "RelationDetails":
        return cls(
            id=relation_orm.id,
            label=relation_orm.label,
            stats=TextOccurrenceStats.from_mixin(relation_orm),
            alt_labels=relation_orm.alt_labels,
            categories=relation_orm.category_dict,
            subject_id=relation_orm.subject_id,
            predicate_id=relation_orm.predicate_id,
            object_id=relation_orm.object_id,
        )
