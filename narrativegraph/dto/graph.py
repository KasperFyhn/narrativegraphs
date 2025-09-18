from fastapi_camelcase import CamelModel
from pydantic import Field


class Node(CamelModel):
    """Node in the graph"""

    id: int
    label: str
    frequency: int
    focus: bool = False


class Relation(CamelModel):
    """Individual relation within an edge group"""

    id: int
    label: str
    subject_label: str
    object_label: str


class Edge(CamelModel):
    """Edge in the graph representing grouped relations"""

    id: str
    label: str
    from_id: int = Field(serialization_alias="from", validation_alias="from_id")
    to_id: int = Field(serialization_alias="to", validation_alias="to_id")
    subject_label: str
    object_label: str
    total_frequency: int
    group: list[Relation]


class Graph(CamelModel):
    """Response containing graph data"""

    edges: list[Edge]
    nodes: list[Node]

