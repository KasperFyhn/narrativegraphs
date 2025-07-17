from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import and_, between, func, or_
from sqlalchemy.orm import Session, selectinload

from narrativegraph.db.orms import (
    RelationOrm,
    EntityOrm,
    DocumentCategory,
    EntityCategory,
    RelationCategory,
    DocumentOrm,
)
from narrativegraph.server.dtos import (
    GraphFilter,
    Edge,
    Node,
    DataBounds,
    RelationGroup,
)
from narrativegraph.server.routes.common import get_db_session

router = APIRouter()


def date_filter(model_class, graph_filter: GraphFilter) -> list:
    """Create date filtering conditions for entities/relations"""
    conditions = []
    if graph_filter.earliest_date:
        conditions.append(model_class.last_occurrence >= graph_filter.earliest_date)
    if graph_filter.latest_date:
        conditions.append(model_class.first_occurrence <= graph_filter.latest_date)
    return conditions


# Map model classes to their category models
_category_model_map = {
    EntityOrm: EntityCategory,
    RelationOrm: RelationCategory,
    DocumentOrm: DocumentCategory,
}

def category_filter(model_class, graph_filter: GraphFilter) -> list:
    """Create category filtering conditions"""
    if graph_filter.categories is None:
        return []

    category_model_class = _category_model_map[model_class]

    # Must have ANY of these categories (OR logic)
    or_conditions = []
    for cat_name, cat_values in graph_filter.categories.items():
        for cat_value in cat_values:
            or_conditions.append(
                model_class.categories.any(
                    and_(
                        category_model_class.name == cat_name,
                        category_model_class.value == cat_value,
                    )
                )
            )

    return [or_(*or_conditions)]


def term_frequency_filter(
    model_class, min_freq: Optional[int], max_freq: Optional[int]
) -> list:
    """Create term frequency filtering conditions"""
    conditions = []
    if min_freq is not None and max_freq is not None:
        conditions.append(between(model_class.term_frequency, min_freq, max_freq))
    elif min_freq is not None:
        conditions.append(model_class.term_frequency >= min_freq)
    elif max_freq is not None:
        conditions.append(model_class.term_frequency <= max_freq)
    return conditions


def entity_term_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create entity term frequency filter"""
    return term_frequency_filter(
        EntityOrm.term_frequency,
        graph_filter.minimum_node_frequency,
        graph_filter.maximum_node_frequency,
    )


def relation_term_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create relation term frequency filter"""
    return term_frequency_filter(
        RelationOrm,
        graph_filter.minimum_edge_frequency,
        graph_filter.maximum_edge_frequency,
    )


def entity_blacklist_filter(graph_filter: GraphFilter) -> list:
    """Filter out blacklisted entities"""
    conditions = []
    if graph_filter.blacklisted_entity_ids:
        conditions.append(~EntityOrm.id.in_(graph_filter.blacklisted_entity_ids))
    return conditions


def entity_whitelist_filter(graph_filter: GraphFilter) -> list:
    """Filter for whitelisted entities only"""
    conditions = []
    if graph_filter.whitelisted_entity_ids:
        conditions.append(EntityOrm.id.in_(graph_filter.whitelisted_entity_ids))
    return conditions


def entity_label_filter(graph_filter: GraphFilter) -> list:
    """Filter entities by label search"""
    conditions = []
    if graph_filter.label_search:
        conditions.append(EntityOrm.label.ilike(f"%{graph_filter.label_search}%"))
    return conditions


def combine_filters(*filter_lists: list) -> list:
    result = []
    for filter_list in filter_lists:
        result += filter_list
    return result


def create_edge_groups(relations: List[RelationOrm]) -> List[Edge]:
    """Group relations into edges and create Edge objects"""
    grouped_edges = defaultdict(list)

    for relation in relations:
        key = f"{relation.subject_id}->{relation.object_id}"
        grouped_edges[key].append(relation)

    edges = []
    for group in grouped_edges.values():
        # Sort by term frequency descending
        group.sort(key=lambda x: x.term_frequency, reverse=True)
        representative = group[0]

        # Create label from top 3 relations
        labels = [e.label for e in group[:3]]
        if len(group) > 3:
            labels.append("...")
        label = ", ".join(labels)

        total_frequency = sum(e.term_frequency for e in group)

        edge = Edge(
            id=f"{representative.subject.id}->{representative.object.id}",
            from_id=representative.subject.id,
            to_id=representative.object.id,
            subject_label=representative.subject.label,
            object_label=representative.object.label,
            label=label,
            total_term_frequency=total_frequency,
            group=[
                RelationGroup(
                    **{
                        "id": r.id,
                        "label": r.label,
                        "subject_label": r.subject.label,
                        "object_label": r.object.label,
                    }
                )
                for r in group
            ],
        )
        edges.append(edge)

    return edges


def get_focus_entities(
    graph_filter: GraphFilter, db, entity_conditions: List
) -> List[EntityOrm]:
    """Get focus entities based on whitelist or label search"""
    focus_conditions = []
    if graph_filter.whitelisted_entity_ids:
        focus_conditions.extend(entity_whitelist_filter(graph_filter))
    if graph_filter.label_search:
        focus_conditions.extend(entity_label_filter(graph_filter))

    focus_query = (
        db.query(EntityOrm)
        .filter(or_(*focus_conditions), *entity_conditions)
        .order_by(EntityOrm.term_frequency.desc())
        .limit(graph_filter.limit_nodes)
    )

    return focus_query.all()


def get_connected_entities(
    focus_entity_ids: List[int],
    graph_filter: GraphFilter,
    db,
    entity_conditions: List,
    relation_conditions: List,
) -> List[EntityOrm]:
    """Get entities connected to focus entities"""
    # Find relations involving focus entities
    connections = (
        db.query(RelationOrm)
        .filter(
            and_(
                *relation_conditions,
                or_(
                    RelationOrm.subject_id.in_(focus_entity_ids),
                    RelationOrm.object_id.in_(focus_entity_ids),
                ),
            )
        )
        .all()
    )

    # Get connected entity IDs (excluding focus entities)
    connected_entity_ids = set()
    for conn in connections:
        connected_entity_ids.update([conn.subject_id, conn.object_id])

    connected_entity_ids = [
        eid for eid in connected_entity_ids if eid not in focus_entity_ids
    ]

    if not connected_entity_ids:
        return []

    # Query connected entities
    extra_conditions = entity_conditions + [EntityOrm.id.in_(connected_entity_ids)]

    extra_query = (
        db.query(EntityOrm)
        .filter(and_(*extra_conditions))
        .order_by(EntityOrm.term_frequency.desc())
        .limit(graph_filter.limit_nodes - len(focus_entity_ids))
    )

    return extra_query.all()


@router.post("/")
async def get_graph(graph_filter: GraphFilter, db: Session = Depends(get_db_session)):
    """Get graph data with entities and relations based on filters"""

    # Build entity filter conditions
    entity_conditions = combine_filters(
        date_filter(EntityOrm, graph_filter),
        category_filter(EntityOrm, graph_filter),
        entity_term_frequency_filter(graph_filter),
        entity_blacklist_filter(graph_filter),
    )

    # Build relation filter conditions
    relation_conditions = combine_filters(
        date_filter(RelationOrm, graph_filter),
        category_filter(RelationOrm, graph_filter),
        relation_term_frequency_filter(graph_filter),
    )

    focus_entity_ids = []

    # Handle focus entities (whitelist or label search)
    if graph_filter.whitelisted_entity_ids or graph_filter.label_search:
        focus_entities = get_focus_entities(graph_filter, db, entity_conditions)
        actual_focus_entities = True

    else:  # No focus entities, get top entities by frequency
        query = (
            db.query(EntityOrm)
            .filter(and_(*entity_conditions))
            .order_by(EntityOrm.term_frequency.desc())
            .limit(10)
        )
        focus_entities = query.all()
        actual_focus_entities = False

    focus_entity_ids = [e.id for e in focus_entities]

    # Get connected entities if we need more
    extra_entities = []
    if len(focus_entities) < graph_filter.limit_nodes:
        extra_entities = get_connected_entities(
            focus_entity_ids, graph_filter, db, entity_conditions, relation_conditions
        )

    # Combine focus and extra entities
    entities = [
        {"entity": e, "focus": actual_focus_entities} for e in focus_entities
    ] + [{"entity": e, "focus": False} for e in extra_entities]
    entity_ids = [item["entity"].id for item in entities]

    # Get relations between entities
    relation_query_conditions = [
        and_(
            *relation_conditions,
            RelationOrm.subject_id.in_(entity_ids),
            RelationOrm.object_id.in_(entity_ids),
        )
    ]

    # If we have focus entities, prioritize relations between them
    if focus_entity_ids:
        relation_query_conditions.insert(
            0,
            and_(
                *relation_conditions,
                RelationOrm.subject_id.in_(focus_entity_ids),
                RelationOrm.object_id.in_(focus_entity_ids),
            ),
        )

    relations = (
        db.query(RelationOrm)
        .options(selectinload(RelationOrm.subject), selectinload(RelationOrm.object))
        .filter(or_(*relation_query_conditions))
        .all()
    )

    # Create edges from relations
    edges = create_edge_groups(relations)

    # Sort edges by focus connection and frequency
    def edge_sort_key(edge):
        connects_focus = (
            edge.from_id in focus_entity_ids and edge.to_id in focus_entity_ids
        )
        return not connects_focus, -edge.total_term_frequency

    edges.sort(key=edge_sort_key)
    edges = edges[: graph_filter.limit_edges]

    # Prepare response
    nodes = [
        Node(
            id=item["entity"].id,
            label=item["entity"].label,
            term_frequency=item["entity"].term_frequency,
            focus=item["focus"],
        )
        for item in entities
    ]

    return {"edges": edges, "nodes": nodes}


def _compile_categories(db: Session) -> dict[str, list[str]]:
    categories = defaultdict(set)
    for doc_category in db.query(DocumentCategory).all():
        categories[doc_category.name].add(doc_category.value)
    return {name: list(values) for name, values in categories.items()}


@router.get("/bounds")
async def get_bounds(db: Session = Depends(get_db_session)) -> DataBounds:
    return DataBounds(
        minimum_possible_node_frequency=db.query(
            func.min(EntityOrm.term_frequency)
        ).scalar(),
        maximum_possible_node_frequency=db.query(
            func.max(EntityOrm.term_frequency)
        ).scalar(),
        minimum_possible_edge_frequency=db.query(
            func.min(RelationOrm.term_frequency)
        ).scalar(),
        maximum_possible_edge_frequency=db.query(
            func.max(RelationOrm.term_frequency)
        ).scalar(),
        categories=_compile_categories(db),
        earliest_date=db.query(func.min(EntityOrm.first_occurrence)).scalar() or None,
        latest_date=db.query(func.max(EntityOrm.last_occurrence)).scalar() or None,
    )
