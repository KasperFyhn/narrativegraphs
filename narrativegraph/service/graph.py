from collections import defaultdict
from functools import partial
from typing import Callable, List, Literal

import networkx as nx
from networkx.algorithms import community
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload

from narrativegraph.db.cooccurrences import CoOccurrenceOrm
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.relations import RelationOrm
from narrativegraph.dto.entities import EntityLabel
from narrativegraph.dto.filter import GraphFilter
from narrativegraph.dto.graph import Community, Edge, Node, Relation
from narrativegraph.service.common import SubService
from narrativegraph.service.filter import (
    create_co_occurrence_conditions,
    create_entity_conditions,
    create_relation_conditions,
    entity_label_filter,
    entity_whitelist_filter,
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
            group.sort(key=lambda x: x.frequency, reverse=True)
            representative = group[0]

            # Create label from top 3 relations
            labels = [e.predicate.label for e in group[:3]]
            if len(group) > 3:
                labels.append("...")
            label = ", ".join(labels)

            total_frequency = sum(e.frequency for e in group)

            edge = Edge(
                id=f"{representative.subject.id}->{representative.object.id}",
                from_id=representative.subject.id,
                to_id=representative.object.id,
                subject_label=representative.subject.label,
                object_label=representative.object.label,
                label=label,
                total_frequency=total_frequency,
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
                .order_by(EntityOrm.frequency.desc())
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
                .order_by(EntityOrm.frequency.desc())
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
                    .order_by(EntityOrm.frequency.desc())
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
                return not connects_focus, -edge.total_frequency

            edges.sort(key=edge_sort_key)
            edges = edges[: graph_filter.limit_edges]

            # Prepare response
            nodes = [
                Node(
                    id=item["entity"].id,
                    label=item["entity"].label,
                    frequency=item["entity"].frequency,
                    focus=item["focus"],
                )
                for item in entities
            ]

            return {"edges": edges, "nodes": nodes}

    @staticmethod
    def _community_metrics(graph: nx.Graph, comm: set[int]):
        subgraph = graph.subgraph(comm)

        # Internal density
        possible_edges = len(comm) * (len(comm) - 1) / 2
        density = (
            subgraph.number_of_edges() / possible_edges if possible_edges > 0 else 0
        )

        # Average internal PMI
        avg_pmi = (
            sum(graph[u][v]["weight"] for u, v in subgraph.edges())
            / subgraph.number_of_edges()
            if subgraph.number_of_edges() > 0
            else 0
        )

        # Conductance (boundary edges / total edges touching community)
        boundary = sum(
            1
            for node in comm
            for neighbor in graph.neighbors(node)
            if neighbor not in comm
        )
        total = boundary + 2 * subgraph.number_of_edges()
        conductance = boundary / total if total > 0 else 0

        return {
            "score": density * (1 - conductance),
            "density": density,
            "avg_pmi": avg_pmi,
            "conductance": conductance,
        }

    def find_communities(
        self,
        graph_filter: GraphFilter = None,
        weight_measure: Literal["pmi", "frequency"] = "pmi",
        community_detection_method: Literal["louvain", "k_clique"]
        | Callable[[nx.Graph], list[set[int]]] = "k_clique",
    ) -> list[Community]:
        if graph_filter is None:
            graph_filter = GraphFilter()

        if community_detection_method == "louvain":
            community_detection_method = partial(community.louvain_communities)
        elif community_detection_method == "k_clique":
            community_detection_method = partial(community.k_clique_communities)

        # Build entity filter conditions
        entity_conditions = create_entity_conditions(graph_filter)

        # Build relation filter conditions
        coc_conditions = create_co_occurrence_conditions(graph_filter)

        with self.get_session_context() as db:
            query = db.query(EntityOrm).filter(and_(*entity_conditions))
            entities = query.all()
            entity_map = {entity.id: entity for entity in entities}
            entity_ids = list(entity_map.keys())

            # Get relations between entities
            coc_query_conditions = and_(
                *coc_conditions,
                CoOccurrenceOrm.entity_one_id.in_(entity_ids),
                CoOccurrenceOrm.entity_two_id.in_(entity_ids),
            )

            co_occurrences: list[CoOccurrenceOrm] = (
                db.query(CoOccurrenceOrm).filter(coc_query_conditions).all()
            )

            graph = nx.Graph()
            graph.add_nodes_from(entity_ids)
            for co_occ in co_occurrences:
                if weight_measure == "frequency":
                    weight = co_occ.frequency
                elif weight_measure == "pmi":
                    weight = co_occ.pmi

                graph.add_edge(
                    co_occ.entity_one_id, co_occ.entity_two_id, weight=weight
                )

            result = community_detection_method(graph)

            return [
                Community(
                    members=[
                        EntityLabel.from_orm(entity_map[entity]) for entity in comm
                    ],
                    **self._community_metrics(graph, comm),
                )
                for comm in result
            ]
