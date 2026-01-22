from collections import defaultdict
from functools import partial
from typing import Callable, Iterable, List, Literal

import networkx
import networkx as nx
from networkx.algorithms import community
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from narrativegraph.db.cooccurrences import CoOccurrenceOrm
from narrativegraph.db.entities import EntityOrm
from narrativegraph.db.relations import RelationOrm
from narrativegraph.dto.entities import EntityLabel
from narrativegraph.dto.filter import GraphFilter
from narrativegraph.dto.graph import Community, Edge, Graph, Node, Relation
from narrativegraph.service.common import SubService
from narrativegraph.service.filter import (
    create_co_occurrence_conditions,
    create_connection_conditions,
    create_entity_conditions,
)

ConnectionType = Literal["relation", "cooccurrence"]


class GraphService(SubService):
    @staticmethod
    def _create_edges(
        connections: List[RelationOrm | CoOccurrenceOrm],
    ) -> List[Edge]:
        """Group relations into edges and create Edge objects"""
        if isinstance(connections[0], RelationOrm):
            connections: List[RelationOrm]
            grouped_edges = defaultdict(list)

            for relation in connections:
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
                            label=r.label,
                            subject_label=r.subject.label,
                            object_label=r.object.label,
                        )
                        for r in group
                    ],
                )
                edges.append(edge)
            return edges

        elif isinstance(connections[0], CoOccurrenceOrm):
            connections: List[CoOccurrenceOrm]
            return [
                Edge(
                    id=cooc.id,
                    label=None,
                    from_id=cooc.entity_one_id,
                    to_id=cooc.entity_two_id,
                    subject_label=cooc.entity_one.label,
                    object_label=cooc.entity_two.label,
                    total_frequency=cooc.frequency,
                )
                for cooc in connections
            ]
        else:
            raise ValueError("Unknown connection type")

    def _create_nodes(self, entities: Iterable[EntityOrm], edges: list[Edge]):
        connected_entities = {
            id_ for edge in edges for id_ in [edge.from_id, edge.to_id]
        }

        # Prepare response
        nodes = [
            Node(
                id=entity.id,
                label=entity.label,
                frequency=entity.frequency,
            )
            for entity in entities
            if entity.id in connected_entities
        ]
        return nodes

    @staticmethod
    def _connecting_entity_ids_condition(
        connection_type: ConnectionType, entity_ids: list[int]
    ):
        if connection_type == "relation":
            connect_focus_entity = or_(
                RelationOrm.subject_id.in_(entity_ids),
                RelationOrm.object_id.in_(entity_ids),
            )

        elif connection_type == "cooccurrence":
            connect_focus_entity = or_(
                CoOccurrenceOrm.entity_one.in_(entity_ids),
                CoOccurrenceOrm.entity_two.in_(entity_ids),
            )
        else:
            raise NotImplementedError

        return connect_focus_entity

    @staticmethod
    def _get_entity_ids_from_connection(
        orm: RelationOrm | CoOccurrenceOrm,
    ) -> list[int]:
        if isinstance(orm, RelationOrm):
            return [orm.subject_id, orm.object_id]
        elif isinstance(orm, CoOccurrenceOrm):
            return [orm.entity_one_id, orm.entity_two_id]
        else:
            raise NotImplementedError

    def expand_from_focus_entities(
        self,
        focus_entity_ids: list[int],
        connection_type: ConnectionType,
        graph_filter: GraphFilter,
    ) -> Graph:
        with self._get_session_context() as db:
            # Connection conditions and DB references
            connection_conditions = create_connection_conditions(
                connection_type, graph_filter
            )
            connection_conditions.append(
                self._connecting_entity_ids_condition(
                    connection_type, focus_entity_ids
                ),
            )
            if connection_type == "relation":
                connection_orm_type = RelationOrm
                source_col = RelationOrm.subject_id
                target_col = RelationOrm.object_id
            elif connection_type == "cooccurrence":
                connection_orm_type = CoOccurrenceOrm
                source_col = CoOccurrenceOrm.entity_one_id
                target_col = CoOccurrenceOrm.entity_two_id
            else:
                raise NotImplementedError

            # Entity conditions and DB references
            source_entity = aliased(EntityOrm)
            target_entity = aliased(EntityOrm)
            source_entity_conditions = create_entity_conditions(
                graph_filter, alias=source_entity
            )
            target_entity_conditions = create_entity_conditions(
                graph_filter, alias=target_entity
            )

            connections_with_entities = (
                db.query(
                    connection_orm_type,
                    source_entity,
                    target_entity,
                )
                .join(source_entity, source_col == source_entity.id)
                .join(target_entity, target_col == target_entity.id)
                .filter(
                    and_(
                        *connection_conditions,
                        and_(*source_entity_conditions),
                        and_(*target_entity_conditions),
                    )
                )
                .all()
            )

            # Extract unique entities and connections
            connections = []
            entities_by_id: dict[int, EntityOrm] = {}

            for conn, source_entity, target_entity in connections_with_entities:
                connections.append(conn)
                entities_by_id[source_entity.id] = source_entity
                entities_by_id[target_entity.id] = target_entity

            # Apply node limit if specified
            if graph_filter.limit_nodes is not None:
                # Prioritize focus entities, then sort by frequency
                sorted_entities = sorted(
                    entities_by_id.values(),
                    key=lambda e: (e.id not in focus_entity_ids, -e.frequency),
                )
                entities = sorted_entities[: graph_filter.limit_nodes]
            else:
                entities = list(entities_by_id.values())

            edges = self._create_edges(connections)

            if graph_filter.limit_edges:
                # Sort edges by focus connection and frequency
                def edge_sort_key(edge):
                    from_focus = edge.from_id in focus_entity_ids
                    to_focus = edge.to_id in focus_entity_ids
                    focus_count = from_focus + to_focus
                    return (
                        -focus_count,
                        -edge.total_frequency,
                    )

                edges.sort(key=edge_sort_key)
                edges = edges[: graph_filter.limit_edges]

            nodes = self._create_nodes(entities, edges)

            return Graph(edges=edges, nodes=nodes)

    def get_graph(
        self,
        connection_type: ConnectionType,
        graph_filter: GraphFilter,
    ):
        entity_conditions = create_entity_conditions(graph_filter)
        connection_conditions = create_connection_conditions(
            connection_type, graph_filter
        )
        connection_orm_type = (
            RelationOrm if connection_type == "relation" else CoOccurrenceOrm
        )

        with self._get_session_context() as db:
            top_entities = (
                db.query(EntityOrm)
                .filter(and_(*entity_conditions))
                .order_by(EntityOrm.frequency.desc())
                .limit(graph_filter.limit_nodes)
                .all()
            )

            top_entity_ids = list({entity.id for entity in top_entities})

            connections = (
                db.query(connection_orm_type)
                .filter(
                    and_(
                        *connection_conditions,
                        self._connecting_entity_ids_condition(
                            connection_type, top_entity_ids
                        ),
                    )
                )
                .order_by(connection_orm_type.frequency.desc())  # noqa; dynamic ref
                .all()
            )

            # Create edges from relations
            edges = self._create_edges(connections)
            if graph_filter.limit_edges:
                edges.sort(key=lambda e: -e.total_frequency)
                edges = edges[: graph_filter.limit_edges]

            nodes = self._create_nodes(top_entities, edges)

            return Graph(edges=edges, nodes=nodes)

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
        min_weight: float = 2.0,
        community_detection_method: Literal[
            "louvain", "k_clique", "connected_components"
        ]
        | Callable[[nx.Graph], list[set[int]]] = "k_clique",
        community_detection_method_args: dict = None,
    ) -> list[Community]:
        if graph_filter is None:
            graph_filter = GraphFilter()
        if community_detection_method_args is None:
            community_detection_method_args = {}

        if community_detection_method == "louvain":
            args = dict(resolution=1.5)
            args.update(community_detection_method_args)
            community_detection_method = partial(community.louvain_communities, **args)
        elif community_detection_method == "k_clique":
            args = dict(k=4)
            args.update(community_detection_method_args)
            community_detection_method = partial(community.k_clique_communities, **args)
        elif community_detection_method == "connected_components":
            args = dict()
            args.update(community_detection_method_args)
            community_detection_method = partial(networkx.connected_components, **args)

        # Build entity filter conditions
        entity_conditions = create_entity_conditions(graph_filter)

        # Build relation filter conditions
        coc_conditions = create_co_occurrence_conditions(graph_filter)
        coc_conditions.append(CoOccurrenceOrm.pmi >= min_weight)

        with self._get_session_context() as db:
            entity_subquery = db.query(EntityOrm.id).filter(and_(*entity_conditions))

            # Get co-occurrences using subquery
            co_occurrences = (
                db.query(CoOccurrenceOrm)
                .filter(
                    and_(*coc_conditions),
                    CoOccurrenceOrm.entity_one_id.in_(entity_subquery),
                    CoOccurrenceOrm.entity_two_id.in_(entity_subquery),
                )
                .all()
            )

            entities = db.query(EntityOrm).filter(and_(*entity_conditions)).all()
            entity_map = {entity.id: entity for entity in entities}
            entity_ids = list(entity_map.keys())

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
                    edges=[(edge[0], edge[1]) for edge in graph.subgraph(comm).edges()],
                    **self._community_metrics(graph, comm),
                )
                for comm in result
            ]
