from pathlib import Path

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, declarative_base, DeclarativeMeta

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
