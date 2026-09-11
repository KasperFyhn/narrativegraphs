"""Getting a model's answer back into the source text.

An LLM returns strings, but the rest of the package addresses entities by
their character offsets in the document, so every surface form a model returns
has to be located in the text again. What cannot be located is dropped, which
also means hallucinated and paraphrased spans never reach the database.
"""

import re
from typing import Optional

Span = tuple[int, int]


def align_span(
    text: str, surface: str, start: int = 0, end: Optional[int] = None
) -> Optional[Span]:
    """Locate `surface` in `text[start:end]` and return its character offsets.

    Models reproduce surface forms with small deviations — casing normalized,
    line breaks collapsed into spaces — so matching is attempted in decreasing
    order of strictness: verbatim, case-insensitive, then whitespace-flexible.

    Returns:
        (start_char, end_char) of the first match, or None if there is none
    """
    if not surface or not surface.strip():
        return None
    if end is None:
        end = len(text)
    if start >= end:
        return None

    found = text.find(surface, start, end)
    if found != -1:
        return found, found + len(surface)

    pattern = re.compile(
        r"\s+".join(re.escape(token) for token in surface.split()), re.IGNORECASE
    )
    match = pattern.search(text, start, end)
    if match is not None:
        return match.start(), match.end()

    return None


def align_sequence(
    text: str, surfaces: list[str], window: Optional[Span] = None
) -> Optional[list[Span]]:
    """Locate several surface forms that are expected to appear in order.

    A document usually mentions the same entity more than once, so anchoring on
    the first occurrence of each part in isolation tends to stitch together
    spans from unrelated sentences. Instead, each part is searched for after the
    end of the previous one, first inside `window` (typically the sentence the
    model quoted as evidence) and then in the document as a whole.

    Returns:
        one (start_char, end_char) per surface form, or None if any of them
        could not be located at all
    """
    windows = [window] if window is not None else []
    windows.append((0, len(text)))

    for start, end in windows:
        spans = _align_in_order(text, surfaces, start, end)
        if spans is None:
            # The parts may all be there but not in the order the model listed
            # them, as in passive constructions and inversions.
            spans = _align_independently(text, surfaces, start, end)
        if spans is not None:
            return spans

    return None


def _align_in_order(
    text: str, surfaces: list[str], start: int, end: int
) -> Optional[list[Span]]:
    spans = []
    cursor = start
    for surface in surfaces:
        span = align_span(text, surface, cursor, end)
        if span is None:
            return None
        spans.append(span)
        cursor = span[1]
    return spans


def _align_independently(
    text: str, surfaces: list[str], start: int, end: int
) -> Optional[list[Span]]:
    spans = [align_span(text, surface, start, end) for surface in surfaces]
    if any(span is None for span in spans):
        return None
    return spans
