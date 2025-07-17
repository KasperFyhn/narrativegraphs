from pydantic import validate_call


@validate_call(validate_return=True)
def _handle_list_of_strings(categories: list[str]) -> list[dict[str, list[str]]]:
    return [{"category": [item]} for item in categories]


@validate_call(validate_return=True)
def _handle_list_of_list_of_strings(
    categories: list[list[str]],
) -> list[dict[str, list[str]]]:
    return [{"category": item} for item in categories]


@validate_call(validate_return=True)
def _handle_list_of_dicts_with_string_values(
    categories: list[dict[str, str]],
) -> list[dict[str, list[str]]]:
    return [{k: [v] for k, v in cat_dict.items()} for cat_dict in categories]


@validate_call(validate_return=True)
def _handle_list_of_dicts_with_list_values(
    categories: list[dict[str, list[str]]],
) -> list[dict[str, list[str]]]:
    return [{k: v for k, v in cat_dict.items()} for cat_dict in categories]


@validate_call(validate_return=True)
def _handle_dict_with_list_of_string_values(
    categories: dict[str, list[str]],
) -> list[dict[str, list[str]]]:
    length_of_lists = len(list(categories.values())[0])
    return [
        {name: [value_list[i]] for name, value_list in categories.items()}
        for i in range(length_of_lists)
    ]

@validate_call(validate_return=True)
def _handle_dict_with_list_of_list_of_string_values(
    categories: dict[str, list[list[str]]],
) -> list[dict[str, list[str]]]:
    length_of_lists = len(list(categories.values())[0])
    return [
        {name: value_list[i] for name, value_list in categories.items()}
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
        if isinstance(first_item, str):
            return _handle_list_of_strings(categories)
        elif isinstance(first_item, list):
            return _handle_list_of_list_of_strings(categories)
        elif isinstance(first_item, dict):
            first_value = list(first_item.values())[0]
            if isinstance(first_value, str):
                categories: list[dict[str, str]]
                return _handle_list_of_dicts_with_string_values(categories)
            elif isinstance(first_value, list):
                return _handle_list_of_dicts_with_list_values(categories)
    elif isinstance(categories, dict):
        first_value = list(categories.values())[0]
        if not isinstance(first_value, list):
            raise ValueError("Values in categories as a dict must be lists")
        if not all(len(first_value) == len(other) for other in categories.values()):
            raise ValueError("Values in categories as a dict must have same length")
        first_item = first_value[0]
        if isinstance(first_item, str):
            return _handle_dict_with_list_of_string_values(categories)
        elif isinstance(first_item, list):
            return _handle_dict_with_list_of_list_of_string_values(categories)

    raise ValueError("Something is terribly wrong with category input!")
