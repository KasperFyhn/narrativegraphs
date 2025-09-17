from datetime import date
from typing import Optional

from fastapi_camelcase import CamelModel


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
