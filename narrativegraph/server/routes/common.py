from typing import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from narrativegraph.db.engine import get_session


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
