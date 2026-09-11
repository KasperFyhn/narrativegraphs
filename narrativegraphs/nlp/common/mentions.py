"""Locating every mention of an entity in a document.

Extractors report the entities that take part in what they extracted. That is
not the same as every mention: a relation stated three times comes back once
from a generative model, and a rule-based extractor only reports the entities
of the relations it found. Recording just those understates the text, and the
frequency-based statistics built on mention counts — co-occurrence, PMI,
community detection — are skewed by the shortfall.
"""

import re

from narrativegraphs.nlp.common.annotation import SpanAnnotation

Span = tuple[int, int]


def find_all_occurrences(text: str, surface: str) -> list[Span]:
    """Every place `surface` occurs in `text`, as character offsets.

    Matching is case-insensitive, tolerates differing whitespace, and respects
    word boundaries, so "ring" does not match inside "ringing".
    """
    if not surface or not surface.strip():
        return []

    pattern = r"\s+".join(re.escape(token) for token in surface.split())
    if _is_word_character(surface[:1]):
        pattern = r"\b" + pattern
    if _is_word_character(surface[-1:]):
        pattern = pattern + r"\b"

    return [
        (match.start(), match.end())
        for match in re.finditer(pattern, text, re.IGNORECASE)
    ]


def expand_to_all_occurrences(
    text: str, entities: list[SpanAnnotation]
) -> list[SpanAnnotation]:
    """Add every other mention of the given entities' surface forms.

    The entities passed in are returned unchanged and in full: downstream
    population looks triplets up by their exact spans, so those must survive.
    Added mentions never overlap one another or an original, and longer
    surface forms claim their text first, so "the ring" wins over "ring".

    Args:
        text: the document the entities were found in
        entities: the entities an extractor reported

    Returns:
        the original entities followed by the additional mentions
    """
    claimed = [(e.start_char, e.end_char) for e in entities]
    additional = []

    surfaces = sorted({e.text for e in entities}, key=len, reverse=True)
    for surface in surfaces:
        for start, end in find_all_occurrences(text, surface):
            if any(
                start < taken_end and end > taken_start
                for taken_start, taken_end in claimed
            ):
                continue
            claimed.append((start, end))
            additional.append(
                SpanAnnotation(text=text[start:end], start_char=start, end_char=end)
            )

    return list(entities) + additional


def _is_word_character(character: str) -> bool:
    return bool(character) and (character.isalnum() or character == "_")
