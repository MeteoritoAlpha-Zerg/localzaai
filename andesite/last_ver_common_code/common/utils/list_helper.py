from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T")


def find_insertion_index(
    sorted_list: List[T],
    item: T,
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> int:
    """
    Performs a binary search to find at what index a given item should be inserted into the sorted list.

    The `sorted_list` sort direction is expected to match the direction of the `reverse` parameter. (e.g. if `reverse = True` the list must be sorted in reverse)
    """
    if key is None:
        key = lambda x: x  # noqa: E731

    low, high = 0, len(sorted_list)
    while low < high:
        mid = (low + high) // 2
        if (key(item) < key(sorted_list[mid])) ^ reverse:  # type: ignore[operator]
            high = mid
        else:
            low = mid + 1

    return low


def insert_and_maintain_order(
    sorted_list: List[T],
    item: T,
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> None:
    """
    Performs an in-place insertion while maintaining the sorted list's order.

    The `sorted_list` sort direction is expected to match the direction of the `reverse` parameter. (e.g. if `reverse = True` the list must be sorted in reverse)
    """
    index = find_insertion_index(sorted_list, item, key, reverse)
    sorted_list.insert(index, item)
