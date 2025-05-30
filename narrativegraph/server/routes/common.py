from narrativegraph.db.service import DbService
from fastapi import Request


def get_db_service(request: Request) -> DbService:
    return request.app.state.db_service