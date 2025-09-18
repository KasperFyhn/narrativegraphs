from typing import Optional

from sqlalchemy import and_, or_, between
from narrativegraph.db.documents import DocumentCategory, DocumentOrm
from narrativegraph.db.relations import RelationCategory, RelationOrm
from narrativegraph.db.entities import EntityCategory, EntityOrm
from narrativegraph.dto.filter import GraphFilter


def date_filter(model_class, graph_filter: GraphFilter) -> list:
    """Create date filtering conditions for entities/relations"""
    conditions = []
    if graph_filter.earliest_date:
        conditions.append(model_class.last_occurrence >= graph_filter.earliest_date)
    if graph_filter.latest_date:
        conditions.append(model_class.first_occurrence <= graph_filter.latest_date)
    return conditions


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

    conditions = []
    for cat_name, cat_values in graph_filter.categories.items():
        # Must have any of this category's labels -- OR logic
        or_conditions = []
        for cat_value in cat_values:
            or_conditions.append(
                model_class.categories.any(
                    and_(
                        category_model_class.name == cat_name,
                        category_model_class.value == cat_value,
                    )
                )
            )
        conditions.append(or_(*or_conditions))

    return conditions


def frequency_filter(
    model_class, min_freq: Optional[int], max_freq: Optional[int]
) -> list:
    """Create term frequency filtering conditions"""
    conditions = []
    if min_freq is not None and max_freq is not None:
        conditions.append(between(model_class.frequency, min_freq, max_freq))
    elif min_freq is not None:
        conditions.append(model_class.frequency >= min_freq)
    elif max_freq is not None:
        conditions.append(model_class.frequency <= max_freq)
    return conditions


def entity_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create entity term frequency filter"""
    return frequency_filter(
        EntityOrm,
        graph_filter.minimum_node_frequency,
        graph_filter.maximum_node_frequency,
    )


def relation_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create relation term frequency filter"""
    return frequency_filter(
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

def create_entity_conditions(graph_filter: GraphFilter) -> list:
    return combine_filters(
        date_filter(EntityOrm, graph_filter),
        category_filter(EntityOrm, graph_filter),
        entity_frequency_filter(graph_filter),
        entity_blacklist_filter(graph_filter),
    )

def create_relation_conditions(graph_filter: GraphFilter) -> list:
    return combine_filters(
        date_filter(RelationOrm, graph_filter),
        category_filter(RelationOrm, graph_filter),
        relation_frequency_filter(graph_filter),
    )
