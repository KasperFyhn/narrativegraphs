from fastapi import APIRouter, Depends, Request

from narrativegraphs.dto.filter import DataBounds
from narrativegraphs.dto.graph import Community
from narrativegraphs.server.requests import CommunitiesRequest, GraphQuery
from narrativegraphs.server.routes.common import get_query_service
from narrativegraphs.service import QueryService
from narrativegraphs.service.graph import ConnectionType

router = APIRouter()


@router.post("")
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


@router.get("/types")
async def get_types(request: Request) -> list[ConnectionType]:
    if request.app.state.cooccurrence_only:
        return ["cooccurrence"]
    else:
        return ["relation", "cooccurrence"]


@router.get("/bounds/{connection_type}")
async def get_bounds(
    connection_type: ConnectionType, service: QueryService = Depends(get_query_service)
) -> DataBounds:
    return service.get_bounds(connection_type)


@router.post("/communities")
async def get_communities(
    request: CommunitiesRequest,
    service: QueryService = Depends(get_query_service),
) -> list[Community]:
    return service.graph.find_communities(
        request.graph_filter,
        request.weight_measure,
        request.min_weight,
        request.community_detection_method,
        request.community_detection_method_args,
    )
