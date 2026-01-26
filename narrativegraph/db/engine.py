from pathlib import Path

from sqlalchemy import Column, Engine, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_Base = declarative_base()


class Base(_Base):
    __abstract__ = True
    id = Column(Integer, autoincrement=True, primary_key=True)


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
