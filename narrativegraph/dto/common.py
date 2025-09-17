from datetime import date
from typing import Optional

from fastapi_camelcase import CamelModel


class Details(CamelModel):
    id: int
    label: str
    frequency: int
    doc_frequency: int
    # alt_labels: list[str]
    first_occurrence: Optional[date]
    last_occurrence: Optional[date]
    categories: dict[str, list[str]]
