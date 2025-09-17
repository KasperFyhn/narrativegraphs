from fastapi_camelcase import CamelModel
from pydantic import Field

from narrativegraph.db.orms import RelationOrm
from narrativegraph.dto.common import Details


class Predicate(CamelModel):
    """Individual relation within an edge group"""

    id: int
    label: str
    subject_label: str
    object_label: str


class Edge(CamelModel):
    """Edge in the graph representing grouped relations"""

    id: str
    from_id: int = Field(serialization_alias="from", validation_alias="from_id")
    to_id: int = Field(serialization_alias="to", validation_alias="to_id")
    subject_label: str
    object_label: str
    label: str
    total_term_frequency: int
    group: list[Predicate]


def transform_relation_orm_to_details(relation: RelationOrm) -> Details:
    """Transform RelationOrm to Details DTO"""
    return Details(
        id=relation.id,
        label=relation.label,
        frequency=relation.term_frequency,
        doc_frequency=relation.doc_frequency,
        alt_labels=[],  # Empty as in original
        first_occurrence=relation.first_occurrence,
        last_occurrence=relation.last_occurrence,
        categories=relation.category_dict,
    )
