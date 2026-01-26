from typing import Optional

from fastapi_camelcase import CamelModel
from pydantic import Field

from narrativegraphs.dto.entities import EntityLabel


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

    id: str | int
    from_id: int = Field(serialization_alias="from", validation_alias="from_id")
    to_id: int = Field(serialization_alias="to", validation_alias="to_id")
    subject_label: str
    object_label: str
    total_frequency: int
    label: Optional[str] = None
    group: Optional[list[Relation]] = None


class Graph(CamelModel):
    """Response containing graph data"""

    edges: list[Edge]
    nodes: list[Node]


class Community(CamelModel):
    """Community in the graph"""

    members: list[EntityLabel]
    edges: list[tuple[int, int]]
    score: float
    density: float
    avg_pmi: float
    conductance: float
