from typing import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from narrativegraphs.service import QueryService


def get_db_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.create_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_query_service(request: Request) -> Generator[QueryService, None, None]:
    return request.app.state.query_service
