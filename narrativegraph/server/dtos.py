from datetime import date
from typing import Optional

from fastapi_camelcase import CamelModel
from pydantic import Field

from narrativegraph.db.orms import DocumentOrm, EntityOrm, RelationOrm


class DataBounds(CamelModel):
    minimum_possible_node_frequency: int
    maximum_possible_node_frequency: int
    minimum_possible_edge_frequency: int
    maximum_possible_edge_frequency: int
    categories: Optional[dict[str, list[str]]] = None
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None


class GraphFilter(CamelModel):
    limit_nodes: int
    limit_edges: int
    only_supernodes: Optional[bool] = None
    minimum_node_frequency: Optional[int] = None
    maximum_node_frequency: Optional[int] = None
    minimum_edge_frequency: Optional[int] = None
    maximum_edge_frequency: Optional[int] = None
    label_search: Optional[str] = None
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None
    whitelisted_entity_ids: Optional[set[str]] = None
    blacklisted_entity_ids: Optional[set[str]] = None
    categories: Optional[dict[str, list[str]]] = None


class RelationGroup(CamelModel):
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
    group: list[RelationGroup]


class SubNode(CamelModel):
    """Subnode within a supernode"""

    id: int
    label: str
    term_frequency: int


class Node(CamelModel):
    """Node in the graph"""

    id: int
    label: str
    term_frequency: int
    focus: bool = False
    subnodes: Optional[list[SubNode]] = None


class GraphResponse(CamelModel):
    """Response containing graph data"""

    edges: list[Edge]
    nodes: list[Node]


class SpanEntity(CamelModel):
    id: int
    start: int
    end: int


class Triplet(CamelModel):
    subject: SpanEntity
    predicate: SpanEntity
    object: SpanEntity


class Document(CamelModel):
    id: int
    text: str
    timestamp: str
    triplets: list[Triplet]
    categories: dict[str, list[str]]


class DocsRequest(CamelModel):
    ids: list[int]
    limit: Optional[int] = None


def transform_orm_to_dto(doc_orm: DocumentOrm) -> Document:
    """Transform ORM model to DTO"""
    return Document(
        id=doc_orm.id,
        text=doc_orm.text,
        timestamp=doc_orm.timestamp.isoformat() if doc_orm.timestamp else "",
        triplets=[
            Triplet(
                subject=SpanEntity(
                    id=triplet_orm.subject_id,
                    start=triplet_orm.subj_span_start,
                    end=triplet_orm.subj_span_end,
                ),
                predicate=SpanEntity(
                    id=triplet_orm.relation_id,
                    start=triplet_orm.pred_span_start,
                    end=triplet_orm.pred_span_end,
                ),
                object=SpanEntity(
                    id=triplet_orm.object_id,
                    start=triplet_orm.obj_span_start,
                    end=triplet_orm.obj_span_end,
                ),
            )
            for triplet_orm in doc_orm.triplets
        ],
        categories=doc_orm.category_dict,
    )


class Details(CamelModel):
    id: int
    label: str
    frequency: int
    doc_frequency: int
    alt_labels: list[str]
    first_occurrence: Optional[date]
    last_occurrence: Optional[date]
    categories: dict[str, list[str]]


class EntityLabel(CamelModel):
    id: int
    label: str


class EntityLabelsRequest(CamelModel):
    ids: list[int]


# Business logic functions
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
