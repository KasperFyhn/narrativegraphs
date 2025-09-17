from fastapi_camelcase import CamelModel

from narrativegraph.db.orms import EntityOrm
from narrativegraph.dto.common import Details


class Node(CamelModel):
    """Node in the graph"""

    id: int
    label: str
    term_frequency: int
    focus: bool = False


class EntityLabel(CamelModel):
    id: int
    label: str


class EntityLabelsRequest(CamelModel):
    ids: list[int]


def transform_entity_orm_to_details(entity: EntityOrm) -> Details:
    """Transform EntityOrm to Details DTO"""
    return Details(
        id=entity.id,
        label=entity.label,
        frequency=entity.term_frequency,
        doc_frequency=entity.doc_frequency,
        alt_labels=[],  # Empty as in original
        first_occurrence=entity.first_occurrence,
        last_occurrence=entity.last_occurrence,
        categories=entity.category_dict,
    )
