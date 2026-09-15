"""Running one call per document without waiting for them one at a time.

LLM requests are I/O-bound, so these use threads and keep only a bounded
window of items in flight, which also keeps generator inputs lazy.
"""

from collections import deque
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
from typing import Callable, Generator, Iterable, TypeVar

_T = TypeVar("_T")
_R = TypeVar("_R")

_SENTINEL = object()


def map_ordered(
    fn: Callable[[_T], _R], items: Iterable[_T], max_workers: int = 4
) -> Generator[_R, None, None]:
    """Apply `fn` concurrently, yielding results in input order.

    LLM calls are I/O-bound, so threads rather than processes. Only
    `max_workers` items are pulled from `items` ahead of the results being
    consumed, which keeps generator inputs lazy.
    """
    if max_workers <= 1:
        for item in items:
            yield fn(item)
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        iterator = iter(items)
        pending = deque(
            executor.submit(fn, item) for item in islice(iterator, max_workers)
        )
        while pending:
            yield pending.popleft().result()
            next_item = next(iterator, _SENTINEL)
            if next_item is not _SENTINEL:
                pending.append(executor.submit(fn, next_item))
