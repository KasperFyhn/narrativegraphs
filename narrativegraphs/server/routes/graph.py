from typing import Optional

from fastapi import APIRouter, Depends

from narrativegraphs.dto.filter import DataBounds, GraphFilter, GraphQuery
from narrativegraphs.dto.graph import Community
from narrativegraphs.server.routes.common import get_query_service
from narrativegraphs.service import QueryService

router = APIRouter()


@router.post("/")
async def get_graph(
    query: GraphQuery,
    service: QueryService = Depends(get_query_service),
):
    """Get graph data with entities and relations based on filters"""
    if query.focus_entities:
        return service.graph.expand_from_focus_entities(
            query.focus_entities,
            query.connection_type,
            query.filter,
        )
    else:
        return service.graph.get_graph(query.connection_type, query.filter)


@router.post("/communities")
async def get_communities(
    graph_filter: Optional[GraphFilter] = None,
    service: QueryService = Depends(get_query_service),
) -> list[Community]:
    return service.graph.find_communities(graph_filter)


@router.get("/bounds")
async def get_bounds(service: QueryService = Depends(get_query_service)) -> DataBounds:
    return service.get_bounds()
