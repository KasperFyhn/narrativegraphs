from typing import Optional

from fastapi_camelcase import CamelModel

from narrativegraphs.db.tuplets import TupletOrm
from narrativegraphs.dto.common import IdentifiableSpan, TextContext


class Tuplet(CamelModel):
    entity_one: IdentifiableSpan
    entity_two: IdentifiableSpan
    context: Optional[TextContext] = None

    @classmethod
    def from_orm(cls, tuplet_orm: TupletOrm) -> "Tuplet":
        return cls(
            entity_one=IdentifiableSpan(
                id=tuplet_orm.entity_one_id,
                text=tuplet_orm.entity_one_span_text,
                start=tuplet_orm.entity_one_span_start,
                end=tuplet_orm.entity_one_span_end,
            ),
            entity_two=IdentifiableSpan(
                id=tuplet_orm.entity_two_id,
                text=tuplet_orm.entity_two_span_text,
                start=tuplet_orm.entity_two_span_start,
                end=tuplet_orm.entity_two_span_end,
            ),
            context=TextContext(
                doc_id=tuplet_orm.doc_id,
                text=tuplet_orm.context
                if tuplet_orm.context
                else tuplet_orm.document.text,
                doc_offset=tuplet_orm.context_offset if tuplet_orm.context else 0,
            ),
        )

    @classmethod
    def from_orms(cls, tuplet_orms: list[TupletOrm]) -> list["Tuplet"]:
        return [cls.from_orm(orm) for orm in tuplet_orms]


class TupletGroup(TextContext):
    tuplets: list[Tuplet]

    def combine(self, other: "TupletGroup") -> "TupletGroup":
        super().combine(other)
        self.tuplets = sorted(
            self.tuplets + other.tuplets, key=lambda t: t.entity_one.start
        )
        return self

    @classmethod
    def from_tuplet(cls, tuplet: Tuplet) -> "TupletGroup":
        orig_context = tuplet.context
        tuplet.context = None

        return cls(
            doc_id=orig_context.doc_id,
            text=orig_context.text,
            doc_offset=orig_context.doc_offset,
            tuplets=[tuplet],
        )

    def print_with_ansi_highlight(self) -> None:
        entity_spans = {
            (e.start - self.doc_offset, e.end - self.doc_offset)
            for tuplet in self.tuplets
            for e in [tuplet.entity_one, tuplet.entity_two]
        }

        # ANSI color codes
        highlight = "\033[93m"  # Yellow
        reset = "\033[0m"

        # Sort spans to process them in order
        sorted_spans = sorted(entity_spans)

        # Build highlighted text
        result = []
        last_end = 0

        for start, end in sorted_spans:
            # Add text before this span
            result.append(self.text[last_end:start])
            # Add highlighted span
            result.append(f"{highlight}{self.text[start:end]}{reset}")
            last_end = end

        # Add remaining text
        result.append(self.text[last_end:])

        print(
            f"ID: {self.doc_id}, OFFSET: {self.doc_offset}", "".join(result), sep="\n"
        )
