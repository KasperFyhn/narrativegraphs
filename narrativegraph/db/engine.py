from pathlib import Path

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session

from narrativegraph.db.orms import Base


def get_engine(filepath: str | Path = None) -> Engine:
    if filepath is None:
        location = ":memory:"
    elif isinstance(filepath, str):
        location = filepath
    else:
        location = filepath.as_posix()
    engine = create_engine("sqlite:///" + location)
    return engine


def setup_database(engine: Engine):
    Base.metadata.create_all(engine)


def get_session(engine: Engine = None) -> Session:
    session = Session(bind=engine)
    return session
