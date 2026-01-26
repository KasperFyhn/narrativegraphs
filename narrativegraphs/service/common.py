import threading
from abc import ABC, abstractmethod
from contextlib import _GeneratorContextManager, contextmanager
from typing import Any, Callable, Optional

import pandas as pd
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from narrativegraphs.db.common import CategoryMixin
from narrativegraphs.db.engine import Base, get_session_factory, setup_database
from narrativegraphs.errors import EntryNotFoundError


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


class SubService:
    def __init__(
        self,
        get_session_context: Callable[[], _GeneratorContextManager[Session]],
    ):
        self._get_session_context = get_session_context


class OrmAssociatedService(SubService, ABC):
    _orm: type[Base] = None
    _category_orm: type[CategoryMixin] = None

    def _add_category_columns(self, df: pd.DataFrame = None):
        with self._get_session_context() as session:
            categories_df = pd.read_sql(
                select(
                    self._category_orm.target_id,
                    self._category_orm.name,
                    self._category_orm.value,
                ),
                session.get_bind(),
            )
            pivot = (
                categories_df.groupby(["target_id", "name"])["value"]
                .apply(list)
                .unstack(fill_value=[])
                .reset_index()
            )
            if df is None:
                return pivot
            else:
                return df.merge(
                    pivot, left_on="id", right_on="target_id", how="left"
                ).drop(columns="target_id")

    @abstractmethod
    def as_df(self) -> pd.DataFrame:
        pass

    def _get_by_id_and_transform(self, id_: int, transform: Callable[[Any], Any]):
        with self._get_session_context() as sc:
            entry = sc.query(self._orm).get(id_)
            if entry is None:
                raise EntryNotFoundError(
                    f"No entry with id '{id_}' in table {self._orm.__tablename__}"
                )
            return transform(entry)

    @abstractmethod
    def get_single(self, id_: int):
        pass

    def _get_multiple_by_ids_and_transform(
        self, transform: Callable[[Any], Any], ids: list[int] = None, limit: int = None
    ):
        with self._get_session_context() as sc:
            query = sc.query(self._orm)
            if ids is not None:
                query = query.filter(self._orm.id.in_(ids))
                # FIXME: what to do in case of missing entries?
            if limit:
                query = query.limit(limit)
            entries = query.all()
            return [transform(entry) for entry in entries]

    @abstractmethod
    def get_multiple(self, ids: list[int] = None, limit: Optional[int] = None):
        pass
