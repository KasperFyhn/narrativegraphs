from narrativegraphs.db.relations import RelationOrm
from narrativegraphs.dto.common import (
    LabeledTextOccurrence,
    TextOccurrenceStats,
)


class RelationStats(TextOccurrenceStats):
    significance: float

    @classmethod
    def from_mixin(cls, orm: RelationOrm):
        base_data = TextOccurrenceStats.from_mixin(orm).model_dump()
        return cls(
            **base_data,
            significance=orm.significance,
        )


class RelationDetails(LabeledTextOccurrence):
    subject_id: int
    predicate_id: int
    object_id: int
    stats: RelationStats

    @classmethod
    def from_orm(cls, relation_orm: RelationOrm) -> "RelationDetails":
        return cls(
            id=relation_orm.id,
            label=relation_orm.label,
            stats=RelationStats.from_mixin(relation_orm),
            alt_labels=relation_orm.alt_labels,
            categories=relation_orm.category_dict,
            subject_id=relation_orm.subject_id,
            predicate_id=relation_orm.predicate_id,
            object_id=relation_orm.object_id,
        )
