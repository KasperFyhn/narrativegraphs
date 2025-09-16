import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from narrativegraph.db.engine import get_engine, setup_database, get_session_factory


class _PassthroughContext:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        pass


class DbService:

    def __init__(self, db_filepath: str | Path = None):
        # Setup
        self._engine = get_engine(db_filepath)
        setup_database(self._engine)
        self._session_factory = get_session_factory(self._engine)
        self._local = threading.local()  # Thread-local storage

    @contextmanager
    def open_session(self):
        if hasattr(self._local, "session") and self._local.session is not None:
            # Use the active keep-alive session
            yield self._local.session
        else:
            # Create a new session
            session = self._session_factory()
            self._local.session = session
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                self._local.session = None
                session.close()

    @property
    def engine(self) -> Engine:
        return self._engine
