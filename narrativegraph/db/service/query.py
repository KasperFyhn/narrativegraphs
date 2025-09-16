from typing import Type

import pandas as pd

from narrativegraph.db.dtos import Document, transform_orm_to_dto, Node
from narrativegraph.db.orms import (
    DocumentOrm,
    RelationOrm,
    EntityOrm,
    Base,
)
from narrativegraph.db.service.common import DbService


class QueryService(DbService):

    def get_orm_df(self, orm_class) -> pd.DataFrame:
        """Generic method that works with any ORM class"""
        with self.open_session() as sc:
            columns = [col.name for col in orm_class.__table__.columns]
            column_list = ", ".join(c for c in columns)
            table_name = orm_class.__table__.name

            query = f"SELECT {column_list} FROM {table_name}"
            return pd.read_sql(query, sc.connection())

    def get_docs(self, ) -> list[Document]:
        with self.open_session() as sc:
            return [transform_orm_to_dto(d) for d in sc.query(DocumentOrm).all()]

    def get_triplets(self, ):
        with self.open_session() as sc:
            pass

    def get_relations(
        self, n: int = None, 
    ) -> list[RelationOrm]:
        with self.open_session() as sc:
            return sc.query(RelationOrm).limit(n).all()

    def get_entities(self, ) -> list[Node]:
        with self.open_session() as sc:
            return [
                Node(id=e.id, label=e.label, term_frequency=e.term_frequency)
                for e in sc.query(EntityOrm).all()
            ]

    def get_entities_df(self, ) -> pd.DataFrame:
        with self.open_session() as sc:
            return self.get_orm_df(EntityOrm)
