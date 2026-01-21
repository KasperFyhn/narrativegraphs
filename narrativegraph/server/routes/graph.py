from typing import Optional

from fastapi import APIRouter, Depends

from narrativegraph.dto.filter import DataBounds, GraphFilter
from narrativegraph.dto.graph import Community
from narrativegraph.server.routes.common import get_query_service
from narrativegraph.service import QueryService

router = APIRouter()


@router.post("/")
async def get_graph(
    graph_filter: GraphFilter, service: QueryService = Depends(get_query_service)
):
    """Get graph data with entities and relations based on filters"""
    return service.graph.get_relation_graph(graph_filter)


@router.post("/communities")
async def get_communities(
    graph_filter: Optional[GraphFilter] = None,
    service: QueryService = Depends(get_query_service),
) -> list[Community]:
    return service.graph.find_communities(graph_filter)


@router.get("/bounds")
async def get_bounds(service: QueryService = Depends(get_query_service)) -> DataBounds:
    return service.get_bounds()
