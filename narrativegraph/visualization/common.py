import pydantic
from pydantic import BaseModel


class Node(BaseModel):
    id: int
    label: str
    weight: float = 1.0
    categories: list[str] = []


class Edge(BaseModel):
    source_id: int
    target_id: int
    label: str
    weight: float = 1.0
    categories: list[str] = []