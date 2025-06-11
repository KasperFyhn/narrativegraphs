from fastapi import Request
from sqlalchemy.orm import Session

from narrativegraph.db.engine import get_session


def get_db_session(request: Request) -> Session:
    return get_session(request.app.state.db_engine)