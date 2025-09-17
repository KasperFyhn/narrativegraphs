from fastapi_camelcase import CamelModel

from narrativegraph.dto.entities import Node
from narrativegraph.dto.relations import Edge


class GraphResponse(CamelModel):
    """Response containing graph data"""

    edges: list[Edge]
    nodes: list[Node]
