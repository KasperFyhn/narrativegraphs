from collections import defaultdict
from functools import partial
from typing import Callable, Iterable, List, Literal

import networkx
import networkx as nx
from networkx.algorithms import community
from sqlalchemy import Column, Integer, MetaData, Table, and_, or_
from sqlalchemy.orm import aliased

from narrativegraphs.db.cooccurrences import CooccurrenceOrm
from narrativegraphs.db.entities import EntityOrm
from narrativegraphs.db.relations import RelationOrm
from narrativegraphs.dto.entities import EntityLabel
from narrativegraphs.dto.filter import GraphFilter
from narrativegraphs.dto.graph import Community, Edge, Graph, Node, Relation
from narrativegraphs.service.common import SubService
from narrativegraphs.service.filter import (
    create_connection_conditions,
    create_cooccurrence_conditions,
    create_entity_conditions,
)

ConnectionType = Literal["relation", "cooccurrence"]


class GraphService(SubService):
    @staticmethod
    def _create_edges(
        connections: List[RelationOrm | CooccurrenceOrm],
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
                group.sort(key=lambda orm: orm.significance, reverse=True)
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

        elif isinstance(connections[0], CooccurrenceOrm):
            connections: List[CooccurrenceOrm]
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

    @staticmethod
    def _create_nodes(entities: Iterable[EntityOrm]):
        # Prepare response
        nodes = [
            Node(
                id=entity.id,
                label=entity.label,
                frequency=entity.frequency,
            )
            for entity in entities
        ]
        return nodes

    @staticmethod
    def _get_entity_ids_from_connection(
        orm: RelationOrm | CooccurrenceOrm,
    ) -> list[int]:
        if isinstance(orm, RelationOrm):
            return [orm.subject_id, orm.object_id]
        elif isinstance(orm, CooccurrenceOrm):
            return [orm.entity_one_id, orm.entity_two_id]
        else:
            raise NotImplementedError

    def _get_node_ids_temp_table(self, entity_ids: Iterable[int]) -> Table:
        with self._get_session_context() as db:
            conn = db.connection()
            metadata = MetaData()
            temp_ids = Table(
                "temp_node_ids",
                metadata,
                Column("id", Integer, primary_key=True),
                prefixes=["TEMPORARY"],
            )
            temp_ids.create(conn, checkfirst=True)

            conn.execute(temp_ids.delete())
            conn.execute(temp_ids.insert(), [{"id": nid} for nid in entity_ids])
            return temp_ids

    def _get_connections(
        self,
        connection_type: ConnectionType,
        entity_ids: set[int],
        graph_filter: GraphFilter,
        expand: bool = False,
    ) -> list[RelationOrm | CooccurrenceOrm]:
        connection_conditions = create_connection_conditions(
            connection_type, graph_filter
        )

        if connection_type == "relation":
            connection_orm_type = RelationOrm
            source_col = RelationOrm.subject_id
            target_col = RelationOrm.object_id
        elif connection_type == "cooccurrence":
            connection_orm_type = CooccurrenceOrm
            source_col = CooccurrenceOrm.entity_one_id
            target_col = CooccurrenceOrm.entity_two_id
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

        with self._get_session_context() as db:
            base_query = (
                db.query(connection_orm_type)
                .join(source_entity, source_col == source_entity.id)
                .join(target_entity, target_col == target_entity.id)
                .filter(
                    *connection_conditions,
                    *source_entity_conditions,
                    *target_entity_conditions,
                )
            )

            if len(entity_ids) < 1000:  # use in_ condition
                if connection_type == "relation":
                    connect_to_ids_conditions = [
                        RelationOrm.subject_id.in_(entity_ids),
                        RelationOrm.object_id.in_(entity_ids),
                    ]
                elif connection_type == "cooccurrence":
                    connect_to_ids_conditions = [
                        CooccurrenceOrm.entity_one_id.in_(entity_ids),
                        CooccurrenceOrm.entity_two_id.in_(entity_ids),
                    ]
                if expand:
                    id_filter = or_(*connect_to_ids_conditions)
                else:
                    id_filter = and_(*connect_to_ids_conditions)

                return base_query.filter(id_filter).all()

            else:  # use temp_table for join operations
                temp_ids = self._get_node_ids_temp_table(entity_ids)

                if expand:
                    source_query = base_query.join(
                        temp_ids, source_col == temp_ids.c.id
                    )
                    target_query = base_query.join(
                        temp_ids, target_col == temp_ids.c.id
                    )
                    return source_query.union(target_query).all()
                else:
                    temp_source = temp_ids.alias("temp_source")
                    temp_target = temp_ids.alias("temp_target")
                    return (
                        base_query.join(temp_source, source_col == temp_source.c.id)
                        .join(temp_target, target_col == temp_target.c.id)
                        .all()
                    )

    def _get_entities(self, entity_ids: set[int]) -> list[EntityOrm]:
        with self._get_session_context() as db:
            if len(entity_ids) < 1000:
                return db.query(EntityOrm).filter(EntityOrm.id.in_(entity_ids)).all()
            else:
                temp_ids = self._get_node_ids_temp_table(entity_ids)
                return (
                    db.query(EntityOrm)
                    .join(temp_ids, EntityOrm.id == temp_ids.c.id)
                    .all()
                )

    def _get_subgraph(
        self,
        entity_ids: set[int],
        connection_type: ConnectionType,
        graph_filter: GraphFilter,
        focus_entity_ids: set[int] = None,
    ) -> Graph:
        if focus_entity_ids is None:
            focus_entity_ids = set()
        with self._get_session_context():
            entities = self._get_entities(entity_ids)
            # Apply node limit if specified
            if graph_filter.limit_nodes is not None:
                # Prioritize focus entities, then sort by frequency
                sorted_entities = sorted(
                    entities,
                    key=lambda e: (e.id not in focus_entity_ids, -e.frequency),
                )
                entities = sorted_entities[: graph_filter.limit_nodes]
                entity_ids = {e.id for e in entities}

            connections = self._get_connections(
                connection_type, entity_ids, graph_filter
            )
            edges = self._create_edges(connections) if connections else []
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

            connected_entities = {
                id_ for edge in edges for id_ in [edge.from_id, edge.to_id]
            }
            entities = [
                e
                for e in entities
                # if connected by edges or an orphaned focus entity
                if e.id in connected_entities or e.id in focus_entity_ids
            ]
            nodes = self._create_nodes(entities)

            return Graph(edges=edges, nodes=nodes)

    def expand_from_focus_entities(
        self,
        focus_entity_ids: set[int],
        connection_type: ConnectionType,
        graph_filter: GraphFilter = GraphFilter(),
    ) -> Graph:
        with self._get_session_context():
            connections = self._get_connections(
                connection_type, focus_entity_ids, graph_filter, expand=True
            )
            connected_entities = set()
            for connection in connections:
                if connection_type == "relation":
                    connected_entities.add(connection.subject_id)
                    connected_entities.add(connection.object_id)
                elif connection_type == "cooccurrence":
                    connected_entities.add(connection.entity_one_id)
                    connected_entities.add(connection.entity_two_id)
            connected_entities.update(focus_entity_ids)

        return self._get_subgraph(
            connected_entities,
            connection_type,
            graph_filter,
            focus_entity_ids=focus_entity_ids,
        )

    def get_subgraph(
        self,
        entity_ids: set[int],
        connection_type: ConnectionType,
        graph_filter: GraphFilter = GraphFilter(),
    ) -> Graph:
        return self._get_subgraph(entity_ids, connection_type, graph_filter)

    def get_graph(
        self,
        connection_type: ConnectionType,
        graph_filter: GraphFilter = GraphFilter(),
    ):
        entity_conditions = create_entity_conditions(graph_filter)

        with self._get_session_context() as db:
            top_entity_ids = {
                row[0]
                for row in db.query(EntityOrm.id)
                .filter(and_(*entity_conditions))
                .order_by(EntityOrm.frequency.desc())
                .limit(graph_filter.limit_nodes)
                .all()
            }

            return self._get_subgraph(top_entity_ids, connection_type, graph_filter)

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
            args = dict(k=3)
            args.update(community_detection_method_args)
            community_detection_method = partial(community.k_clique_communities, **args)
        elif community_detection_method == "connected_components":
            args = dict()
            args.update(community_detection_method_args)
            community_detection_method = partial(networkx.connected_components, **args)

        # Build entity filter conditions
        entity_conditions = create_entity_conditions(graph_filter)

        # Build relation filter conditions
        coc_conditions = create_cooccurrence_conditions(graph_filter)
        coc_conditions.append(CooccurrenceOrm.pmi >= min_weight)

        with self._get_session_context() as db:
            entity_subquery = db.query(EntityOrm.id).filter(and_(*entity_conditions))

            # Get co-occurrences using subquery
            cooccurrences = (
                db.query(CooccurrenceOrm)
                .filter(
                    and_(*coc_conditions),
                    CooccurrenceOrm.entity_one_id.in_(entity_subquery),
                    CooccurrenceOrm.entity_two_id.in_(entity_subquery),
                )
                .all()
            )

            entities = db.query(EntityOrm).filter(and_(*entity_conditions)).all()
            entity_map = {entity.id: entity for entity in entities}
            entity_ids = list(entity_map.keys())

            graph = nx.Graph()
            graph.add_nodes_from(entity_ids)
            for co_occ in cooccurrences:
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
