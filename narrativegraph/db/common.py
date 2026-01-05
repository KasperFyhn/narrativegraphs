from collections import defaultdict

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped


def combine_category_dicts(*dicts: dict[str, list[str]]) -> dict[str, list[str]]:
    result = defaultdict(set)
    for d in dicts:
        for name, values in d.items():
            result[name].update(values)
    return {name: list(values) for name, values in result.items()}


class CategoryMixin:
    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, index=True)
    name = Column(String)
    value = Column(String)

    @classmethod
    def from_categorizable(
        cls, item_id, categorizable_objs: list["CategorizableMixin"]
    ) -> list["CategoryMixin"]:
        categories = combine_category_dicts(
            *[cat_obj.category_dict for cat_obj in categorizable_objs]
        )
        return [
            cls(
                target_id=item_id,  # noqa
                name=cat_name,  # noqa
                value=cat_value,  # noqa
            )
            for cat_name, cat_values in categories.items()
            for cat_value in cat_values
        ]


class CategorizableMixin:
    categories: Mapped[list[CategoryMixin]]

    @hybrid_property
    def category_dict(self) -> dict[str, list[str]]:
        result = defaultdict(set)
        for cat in self.categories:
            result[cat.name].add(cat.value)
        return {name: list(values) for name, values in result.items()}


class HasAltLabels:
    @property
    def alt_labels(self) -> list[str]:
        return []
