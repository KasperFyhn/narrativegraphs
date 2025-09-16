from pathlib import Path

from sqlalchemy import Engine

from narrativegraph.db.orms import (
    RelationOrm,
)
from narrativegraph.db.service.common import DbService
from narrativegraph.db.service.query.docs import DocService
from narrativegraph.db.service.query.entities import EntityService
from narrativegraph.db.service.query.relations import RelationService


class QueryService(DbService):

    def __init__(self, db_filepath: str | Path = None, engine: Engine = None):
        super().__init__(db_filepath=db_filepath, engine=engine)
        self.docs = DocService(lambda: self.get_session_context())
        self.entities = EntityService(lambda: self.get_session_context())
        self.relations = RelationService(lambda: self.get_session_context())

