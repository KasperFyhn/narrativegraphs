from pydantic import validate_call


def _listify(item) -> list:
    if isinstance(item, list):
        return item
    return [item]


@validate_call(validate_return=True)
def _handle_list(categories: list[str | list[str]]) -> list[dict[str, list[str]]]:
    return [{"category": _listify(item)} for item in categories]


@validate_call(validate_return=True)
def _handle_list_of_dicts(
    categories: list[dict[str, str | list[str]]],
) -> list[dict[str, list[str]]]:
    return [{k: _listify(v) for k, v in cat_dict.items()} for cat_dict in categories]


@validate_call(validate_return=True)
def _handle_dict_with_lists(
    categories: dict[str, list[str | list[str]]],
) -> list[dict[str, list[str]]]:
    length_of_lists = len(list(categories.values())[0])
    return [
        {name: _listify(value_list[i]) for name, value_list in categories.items()}
        for i in range(length_of_lists)
    ]


@validate_call
def normalize_categories(
    categories: (
        list[str | list[str]]
        | list[dict[str, str | list[str]]]
        | dict[str, list[str | list[str]]]
    ),
) -> list[dict[str, list[str]]]:
    if not categories:
        return []

    if isinstance(categories, list):  # row style
        first_item = categories[0]
        if isinstance(first_item, (str, list)):
            return _handle_list(categories)
        elif isinstance(first_item, dict):
            return _handle_list_of_dicts(categories)
    elif isinstance(categories, dict):
        first_value = list(categories.values())[0]
        if not isinstance(first_value, list):
            raise ValueError("Values in categories as a dict must be lists")
        if not all(len(first_value) == len(other) for other in categories.values()):
            raise ValueError("Values in categories as a dict must have same length")
        return _handle_dict_with_lists(categories)

    raise ValueError("Something is terribly wrong with category input!")
