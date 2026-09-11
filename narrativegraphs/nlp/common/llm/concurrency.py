"""Running one call per document without waiting for them one at a time.

LLM requests are I/O-bound, so these use threads and keep only a bounded
window of items in flight, which also keeps generator inputs lazy.
"""

from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
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


def map_completed(
    fn: Callable[[_T], _R], items: Iterable[_T], max_workers: int = 4
) -> Generator[tuple[int, _R], None, None]:
    """Apply `fn` concurrently, yielding (index, result) as each call completes.

    As in `map_ordered`, at most `max_workers` items are in flight and no more
    of `items` is consumed than that. The difference is that a finished result
    is handed over immediately rather than waiting behind an earlier item that
    is still running, which is what lets a caller store annotations for a
    document as soon as it comes back.
    """
    if max_workers <= 1:
        for index, item in enumerate(items):
            yield index, fn(item)
        return

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        indexed = enumerate(items)
        pending = {
            executor.submit(fn, item): index
            for index, item in islice(indexed, max_workers)
        }
        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                yield pending.pop(future), future.result()
                next_item = next(indexed, None)
                if next_item is not None:
                    index, item = next_item
                    pending[executor.submit(fn, item)] = index
