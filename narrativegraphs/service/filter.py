from typing import Literal, Optional

from sqlalchemy import and_, between, inspect, or_
from sqlalchemy.orm.util import AliasedClass

from narrativegraphs.db.cooccurrences import CooccurrenceCategory, CooccurrenceOrm
from narrativegraphs.db.documents import DocumentCategory, DocumentOrm
from narrativegraphs.db.entities import EntityCategory, EntityOrm
from narrativegraphs.db.relations import RelationCategory, RelationOrm
from narrativegraphs.dto.filter import GraphFilter

EntityAlias = type[EntityOrm] | AliasedClass[EntityOrm]


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
    CooccurrenceOrm: CooccurrenceCategory,
}


def category_filter(model_class, graph_filter: GraphFilter) -> list:
    """Create category filtering conditions"""
    if graph_filter.categories is None:
        return []
    if isinstance(model_class, AliasedClass):
        category_model_class = _category_model_map[inspect(model_class).class_]
    else:
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


def frequency_filter(field, min_freq: Optional[int], max_freq: Optional[int]) -> list:
    """Create term frequency filtering conditions"""
    conditions = []
    if min_freq is not None and max_freq is not None:
        conditions.append(between(field, min_freq, max_freq))
    elif min_freq is not None:
        conditions.append(field >= min_freq)
    elif max_freq is not None:
        conditions.append(field <= max_freq)
    return conditions


def entity_frequency_filter(model_class, graph_filter: GraphFilter) -> list:
    """Create entity term frequency filter"""
    return frequency_filter(
        model_class.frequency,
        graph_filter.minimum_node_frequency,
        graph_filter.maximum_node_frequency,
    )


def relation_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create relation term frequency filter"""
    return frequency_filter(
        RelationOrm.frequency,
        graph_filter.minimum_edge_frequency,
        graph_filter.maximum_edge_frequency,
    )


def cooccurrence_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create relation term frequency filter"""
    return frequency_filter(
        CooccurrenceOrm.frequency,
        graph_filter.minimum_edge_frequency,
        graph_filter.maximum_edge_frequency,
    )


def entity_doc_frequency_filter(alias: EntityAlias, graph_filter: GraphFilter) -> list:
    """Create entity term frequency filter"""
    return frequency_filter(
        alias.doc_frequency,
        graph_filter.minimum_node_doc_frequency,
        graph_filter.maximum_node_doc_frequency,
    )


def relation_doc_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create relation term frequency filter"""
    return frequency_filter(
        RelationOrm.doc_frequency,
        graph_filter.minimum_edge_doc_frequency,
        graph_filter.maximum_edge_doc_frequency,
    )


def cooccurrence_doc_frequency_filter(graph_filter: GraphFilter) -> list:
    """Create relation term frequency filter"""
    return frequency_filter(
        CooccurrenceOrm.doc_frequency,
        graph_filter.minimum_edge_doc_frequency,
        graph_filter.maximum_edge_doc_frequency,
    )


def entity_blacklist_filter(alias: EntityAlias, graph_filter: GraphFilter) -> list:
    """Filter out blacklisted entities"""
    conditions = []
    if graph_filter.blacklisted_entity_ids:
        conditions.append(~alias.id.in_(graph_filter.blacklisted_entity_ids))
    return conditions


def combine_filters(*filter_lists: list) -> list:
    result = []
    for filter_list in filter_lists:
        result += filter_list
    return result


def create_entity_conditions(
    graph_filter: GraphFilter, alias: EntityAlias = EntityOrm
) -> list:
    return combine_filters(
        date_filter(alias, graph_filter),
        category_filter(alias, graph_filter),
        entity_frequency_filter(alias, graph_filter),
        entity_doc_frequency_filter(alias, graph_filter),
        entity_blacklist_filter(alias, graph_filter),
    )


def create_relation_conditions(graph_filter: GraphFilter) -> list:
    return combine_filters(
        date_filter(RelationOrm, graph_filter),
        category_filter(RelationOrm, graph_filter),
        relation_frequency_filter(graph_filter),
        relation_doc_frequency_filter(graph_filter),
    )


def create_cooccurrence_conditions(graph_filter: GraphFilter) -> list:
    return combine_filters(
        date_filter(CooccurrenceOrm, graph_filter),
        category_filter(CooccurrenceOrm, graph_filter),
        cooccurrence_frequency_filter(graph_filter),
        cooccurrence_doc_frequency_filter(graph_filter),
    )


def create_connection_conditions(
    connection_type: Literal["relation", "cooccurrence"], graph_filter: GraphFilter
) -> list:
    if connection_type == "relation":
        return create_relation_conditions(graph_filter)
    elif connection_type == "cooccurrence":
        return create_cooccurrence_conditions(graph_filter)
    else:
        raise ValueError("Invalid connection type")
