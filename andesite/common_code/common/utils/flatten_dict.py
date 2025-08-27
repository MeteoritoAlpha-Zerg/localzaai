from typing import Any


def flatten_dict(d: dict[str, Any], sep: str = ".") -> dict[str, Any]:
    """
    Flattens a nested dictionary into a single-level dictionary with dot-separated keys.
    List indices are included in the keys.

    Args:
        d (dict): The dictionary to flatten.
        sep (str): Separator between keys.

    Returns:
        dict: A flattened version of the input dictionary.
    """

    def _flatten(obj: dict | list | Any, parent_key: str = "") -> dict[str, Any]:
        items = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
                items.update(_flatten(v, new_key))
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_key = f"{parent_key}{sep}{idx}" if parent_key else str(idx)
                items.update(_flatten(item, new_key))
        else:
            items[parent_key] = obj
        return items

    return _flatten(d)
