from pathlib import Path
from typing import Iterable

from narrativegraph.db.engine import get_engine, setup_database, get_session
from narrativegraph.db.models import Document
from narrativegraph.db.orms import DocumentOrm


class DbService:

    def __init__(self, db_filepath: str | Path = None):
        # Setup
        self._engine = get_engine(db_filepath)
        setup_database(self._engine)

    def add_documents(self, documents: Iterable[Document]):
        with get_session(self._engine) as session:
            bulk = []
            for doc in documents:
                doc_orm = DocumentOrm(
                    **doc.to_dict(),
                )
                bulk.append(doc_orm)

                if len(bulk) >= 500:
                    session.bulk_save_objects(bulk)
                    bulk.clear()

            # save any remaining in the bulk
            session.bulk_save_objects(bulk)

            session.commit()






