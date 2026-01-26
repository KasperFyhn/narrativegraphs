from fastapi_camelcase import CamelModel

from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.dto.common import (
    LabeledTextOccurrence,
    TextOccurrenceStats,
)


class EntityLabel(CamelModel):
    id: int
    label: str

    @classmethod
    def from_orm(cls, entity_orm: EntityOrm) -> "EntityLabel":
        return cls(id=entity_orm.id, label=entity_orm.label)


class EntityLabelsRequest(CamelModel):
    ids: list[int]


class EntityDetails(LabeledTextOccurrence):
    @classmethod
    def from_orm(cls, entity_orm: EntityOrm) -> "EntityDetails":
        return cls(
            id=entity_orm.id,
            label=entity_orm.label,
            stats=TextOccurrenceStats.from_mixin(entity_orm),
            alt_labels=entity_orm.alt_labels,
            categories=entity_orm.category_dict,
        )
