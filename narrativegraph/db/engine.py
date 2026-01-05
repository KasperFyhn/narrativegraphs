from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


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


def get_session_factory(engine: Engine = None) -> sessionmaker:
    return sessionmaker(bind=engine)
