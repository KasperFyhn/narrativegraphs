import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager, _GeneratorContextManager
from typing import Callable, Optional

import pandas as pd
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from narrativegraph.db.engine import setup_database, get_session_factory, Base
from narrativegraph.errors import EntryNotFoundError


class DbService:
    _local = threading.local()

    def __init__(self, engine: Engine):
        self._engine = engine
        setup_database(self._engine)
        self._session_factory = get_session_factory(self._engine)
        self._engine_id = str(id(self._engine))

    @contextmanager
    def get_session_context(self):
        name = "sess_" + self._engine_id
        if hasattr(self._local, name) and getattr(self._local, name) is not None:
            # Use the active keep-alive session
            yield getattr(self._local, name)
        else:
            # Create a new session
            session = self._session_factory()
            setattr(self._local, name, session)
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                setattr(self._local, name, None)
                session.close()

    @property
    def engine(self) -> Engine:
        return self._engine


class SubService:
    def __init__(
        self,
        get_session_context: Callable[[], _GeneratorContextManager[Session]],
    ):
        self.get_session_context = get_session_context


class OrmAssociatedService(SubService, ABC):
    _orm: type[Base] = None

    def as_df(self) -> pd.DataFrame:
        """Generic method that works with any ORM class"""
        with self.get_session_context() as sc:
            columns = [col.name for col in self._orm.__table__.columns.values()]
            column_list = ", ".join(columns)
            table_name = self._orm.__table__.name  # noqa

            query = f"SELECT {column_list} FROM {table_name}"
            return pd.read_sql(query, sc.connection())

    def by_id(self, id_: int):
        with self.get_session_context() as sc:
            entry = sc.query(self._orm).filter(self._orm.id == id_).first()  # noqa; the id ref works
            if entry is None:
                raise EntryNotFoundError(
                    f"No entry with id '{id_}' in table {self._orm.__tablename__}"
                )
            return entry

    @abstractmethod
    def by_ids(self, ids: list[int], limit: Optional[int] = None):
        with self.get_session_context() as sc:
            # FIXME: Error handling in case of missing docs?
            query = sc.query(self._orm).filter(self._orm.id.in_(ids))  # noqa; the id ref works
            if limit:
                query = query.limit(limit)
            return query.all()
