from collections import defaultdict
from typing import List

from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload

from narrativegraph.db.relations import RelationOrm
from narrativegraph.db.entities import EntityOrm
from narrativegraph.dto.filter import GraphFilter
from narrativegraph.service.common import SubService
from narrativegraph.dto.graph import Node, Edge, Relation
from narrativegraph.service.filter import (
    create_relation_conditions,
    create_entity_conditions,
    entity_whitelist_filter,
    entity_label_filter,
)


class GraphService(SubService):

    @staticmethod
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
            labels = [e.predicate.label for e in group[:3]]
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
                    Relation(
                        id=r.id,
                        label=r.predicate.label,
                        subject_label=r.subject.label,
                        object_label=r.object.label,
                    )
                    for r in group
                ],
            )
            edges.append(edge)

        return edges

    def _get_focus_entities(
        self, graph_filter: GraphFilter, entity_conditions: List
    ) -> List[EntityOrm]:
        """Get focus entities based on whitelist or label search"""
        with self.get_session_context() as db:

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

    def _get_connected_entities(
        self,
        focus_entity_ids: list[int],
        graph_filter: GraphFilter,
        entity_conditions: List,
        relation_conditions: List,
    ) -> list[EntityOrm]:
        """Get entities connected to focus entities"""
        with self.get_session_context() as db:
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
            extra_conditions = entity_conditions + [
                EntityOrm.id.in_(connected_entity_ids)
            ]

            extra_query = (
                db.query(EntityOrm)
                .filter(and_(*extra_conditions))
                .order_by(EntityOrm.term_frequency.desc())
                .limit(graph_filter.limit_nodes - len(focus_entity_ids))
            )

            return extra_query.all()

    def get_graph(self, graph_filter: GraphFilter):
        """Get graph data with entities and relations based on filters"""

        # Build entity filter conditions
        entity_conditions = create_entity_conditions(graph_filter)

        # Build relation filter conditions
        relation_conditions = create_relation_conditions(graph_filter)

        focus_entity_ids = []

        with self.get_session_context() as db:

            # Handle focus entities (whitelist or label search)
            if graph_filter.whitelisted_entity_ids or graph_filter.label_search:
                focus_entities = self._get_focus_entities(
                    graph_filter, entity_conditions
                )

                focus_entity_ids = [e.id for e in focus_entities]

                # Get connected entities if we need more
                extra_entities = []
                if len(focus_entities) < graph_filter.limit_nodes:
                    extra_entities = self._get_connected_entities(
                        focus_entity_ids,
                        graph_filter,
                        entity_conditions,
                        relation_conditions,
                    )

                # Combine focus and extra entities
                entities = [{"entity": e, "focus": True} for e in focus_entities] + [
                    {"entity": e, "focus": False} for e in extra_entities
                ]

            else:  # No focus entities, get top entities by frequency
                query = (
                    db.query(EntityOrm)
                    .filter(and_(*entity_conditions))
                    .order_by(EntityOrm.term_frequency.desc())
                    .limit(graph_filter.limit_nodes)
                )
                top_entities = query.all()
                entities = [{"entity": e, "focus": False} for e in top_entities]

            entity_ids = [item["entity"].id for item in entities]

            # Get relations between entities
            relation_query_conditions = [
                and_(
                    *relation_conditions,
                    RelationOrm.subject_id.in_(entity_ids),
                    RelationOrm.object_id.in_(entity_ids),
                )
            ]

            relations: list[RelationOrm] = (
                db.query(RelationOrm)
                .options(
                    selectinload(RelationOrm.subject), selectinload(RelationOrm.object)
                )
                .filter(or_(*relation_query_conditions))
                .all()
            )

            # Create edges from relations
            edges = self.create_edge_groups(relations)

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
