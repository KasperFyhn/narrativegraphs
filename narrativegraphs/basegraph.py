import logging
import os
from typing import TYPE_CHECKING, Literal

import networkx as nx
import pandas as pd
from sqlalchemy import text

from narrativegraphs.db.engine import get_engine
from narrativegraphs.service import QueryService

if TYPE_CHECKING:
    from narrativegraphs.server.backgroundserver import BackgroundServer

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("narrativegraphs")
_logger.setLevel(logging.INFO)


class BaseGraph(QueryService):
    """Base class for graph implementations.

    Provides shared functionality for database management, persistence,
    visualization, and access to entities, cooccurrences, and documents.

    Subclasses should set `_cooccurrence_only` to indicate whether they
    support relations/predicates or only co-occurrences.
    """

    _cooccurrence_only: bool = False  # Override in subclasses

    def __init__(
        self,
        sqlite_db_path: str = None,
        on_existing_db: Literal["stop", "overwrite", "reuse"] = "stop",
    ):
        """Initialize the base graph.

        Args:
            sqlite_db_path: Path to SQLite database file. If None, uses in-memory DB.
            on_existing_db: Behavior when database exists:
                - "stop": Raise error if DB contains data
                - "overwrite": Delete existing DB
                - "reuse": Use existing DB data
        """
        if sqlite_db_path and os.path.exists(sqlite_db_path):
            if on_existing_db == "overwrite":
                os.remove(sqlite_db_path)
            elif on_existing_db == "stop":
                temp_service = QueryService(get_engine(sqlite_db_path))
                if len(temp_service.documents.get_docs(limit=1)) > 0:
                    raise FileExistsError(
                        f"Database contains data. Use {self.__class__.__name__}.load() "
                        "or set on_existing_db to 'overwrite' or 'reuse'."
                    )

        super().__init__(get_engine(sqlite_db_path))

    @property
    def entities_(self) -> pd.DataFrame:
        """Entities as a pandas DataFrame."""
        return self.entities.as_df()

    @property
    def cooccurrences_(self) -> pd.DataFrame:
        """Co-occurrences as a pandas DataFrame."""
        return self.cooccurrences.as_df()

    @property
    def documents_(self) -> pd.DataFrame:
        """Documents as a pandas DataFrame."""
        return self.documents.as_df()

    @property
    def cooccurrence_graph_(self) -> nx.Graph:
        """The full cooccurrence graph as an undirected NetworkX graph."""
        cg = self.graph.get_graph("cooccurrence")
        g = nx.Graph()
        g.add_nodes_from((n.id, n) for n in cg.nodes)
        g.add_edges_from((e.from_id, e.to_id) for e in cg.edges)
        return g

    def serve_visualizer(
        self,
        port: int = 8001,
        block: bool = True,
        autostart: bool = True,
    ) -> "BackgroundServer | None":
        """Serve the visualizer application.

        Args:
            port: The port that the visualizer should be served on.
            block: If True (default), the function will block until the server is
                stopped. If False, the server will run in the background.
            autostart: If True (default), the server is started automatically. Only
                relevant for background servers.

        Returns:
            If not blocking, return a BackgroundServer object. If blocking, return
                None after termination.
        """
        from narrativegraphs.server.backgroundserver import BackgroundServer

        server = BackgroundServer(
            self._engine, port=port, cooccurrence_only=self._cooccurrence_only
        )
        if autostart:
            server.start(block=block)
        if not block:
            return server
        else:
            return None

    def save_to_file(self, file_path: str, overwrite: bool = True):
        """Save in-memory database to file.

        Args:
            file_path: Path to save the database to.
            overwrite: If True, overwrite existing file. If False, raise error.
        """
        if not file_path.endswith(".db"):
            file_path += ".db"

        if os.path.exists(file_path):
            if not overwrite:
                raise FileExistsError(
                    f"File exists: {file_path}. Set overwrite=True to replace."
                )
            else:
                os.remove(file_path)

        if str(self._engine.url) == "sqlite:///:memory:":
            with self.get_session_context() as session:
                session.execute(text(f"VACUUM main INTO '{file_path}'"))
        else:
            raise ValueError("Database is already file-based.")

    @classmethod
    def load(cls, file_path: str):
        """Load from a SQLite database file.

        Args:
            file_path: Path to a SQLite database to load from.

        Returns:
            A loaded object backed by the database.
        """
        if not file_path.endswith(".db"):
            file_path += ".db"

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Database not found: {file_path}")
        return cls(sqlite_db_path=file_path, on_existing_db="reuse")
