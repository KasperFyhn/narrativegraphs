from fastapi_camelcase import CamelModel

from narrativegraph.db.entities import EntityOrm
from narrativegraph.dto.common import Details


class EntityLabel(CamelModel):
    id: int
    label: str


class EntityLabelsRequest(CamelModel):
    ids: list[int]


class EntityDetails(Details):
    pass

def transform_entity_orm_to_details(entity: EntityOrm) -> Details:
    """Transform EntityOrm to Details DTO"""
    return EntityDetails(
        id=entity.id,
        label=entity.label,
        frequency=entity.term_frequency,
        doc_frequency=entity.doc_frequency,
        first_occurrence=entity.first_occurrence,
        last_occurrence=entity.last_occurrence,
        categories=entity.category_dict,
    )
