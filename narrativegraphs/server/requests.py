from typing import Literal, Optional

from fastapi_camelcase import CamelModel

from narrativegraphs import GraphFilter


class GraphQuery(CamelModel):
    connection_type: Literal["relation", "cooccurrence"] = "relation"
    focus_entities: Optional[set[int]] = None
    filter: Optional[GraphFilter] = None


class CommunitiesRequest(CamelModel):
    graph_filter: Optional[GraphFilter] = None
    weight_measure: Literal["pmi", "frequency"] = "pmi"
    min_weight: float = 2.0
    community_detection_method: Literal[
        "louvain", "k_clique", "connected_components"
    ] = "k_clique"
    community_detection_method_args: dict = None
