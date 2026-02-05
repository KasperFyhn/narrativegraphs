from typing import Optional

from fastapi_camelcase import CamelModel

from narrativegraphs.db.triplets import TripletOrm
from narrativegraphs.dto.common import IdentifiableSpan, TextContext


class Triplet(CamelModel):
    subject: IdentifiableSpan
    predicate: IdentifiableSpan
    object: IdentifiableSpan
    context: Optional[TextContext] = None

    @classmethod
    def from_orm(cls, triplet_orm: TripletOrm) -> "Triplet":
        return cls(
            subject=IdentifiableSpan(
                id=triplet_orm.subject_id,
                text=triplet_orm.subj_span_text,
                start=triplet_orm.subj_span_start,
                end=triplet_orm.subj_span_end,
            ),
            predicate=IdentifiableSpan(
                id=triplet_orm.predicate_id,
                text=triplet_orm.pred_span_text,
                start=triplet_orm.pred_span_start,
                end=triplet_orm.pred_span_end,
            ),
            object=IdentifiableSpan(
                id=triplet_orm.object_id,
                text=triplet_orm.obj_span_text,
                start=triplet_orm.obj_span_start,
                end=triplet_orm.obj_span_end,
            ),
            context=TextContext(
                doc_id=triplet_orm.doc_id,
                text=triplet_orm.context,
                doc_offset=triplet_orm.context_offset,
            ),
        )

    @classmethod
    def from_orms(cls, triplet_orms: list[TripletOrm]) -> list["Triplet"]:
        return [cls.from_orm(orm) for orm in triplet_orms]


class TripletGroup(TextContext):
    triplets: list[Triplet]

    def combine(self, other: "TripletGroup") -> "TripletGroup":
        super().combine(other)
        self.triplets = sorted(
            self.triplets + other.triplets, key=lambda t: t.subject.start
        )
        return self

    @classmethod
    def from_triplet(cls, triplet: Triplet) -> "TripletGroup":
        orig_context = triplet.context
        triplet.context = None

        return cls(
            doc_id=orig_context.doc_id,
            text=orig_context.text,
            doc_offset=orig_context.doc_offset,
            triplets=[triplet],
        )

    def print_with_ansi_highlight(self) -> None:
        # ANSI color codes
        blue = "\033[94m"  # Subject
        yellow = "\033[93m"  # Predicate
        red = "\033[91m"  # Object
        purple = "\033[95m"  # Subject + Object overlap
        reset = "\033[0m"

        # Collect spans by type
        subject_spans = {
            (t.subject.start - self.doc_offset, t.subject.end - self.doc_offset)
            for t in self.triplets
        }
        predicate_spans = {
            (t.predicate.start - self.doc_offset, t.predicate.end - self.doc_offset)
            for t in self.triplets
        }
        object_spans = {
            (t.object.start - self.doc_offset, t.object.end - self.doc_offset)
            for t in self.triplets
        }

        # Create events with type information
        events = []
        for start, end in subject_spans:
            events.append((start, "subject", 1))
            events.append((end, "subject", -1))
        for start, end in predicate_spans:
            events.append((start, "predicate", 1))
            events.append((end, "predicate", -1))
        for start, end in object_spans:
            events.append((start, "object", 1))
            events.append((end, "object", -1))

        events.sort(
            key=lambda x: (x[0], -x[2])
        )  # Sort by position, then end before start

        result = []
        last_pos = 0
        active = {"subject": 0, "predicate": 0, "object": 0}

        for pos, span_type, delta in events:
            if pos > last_pos:
                # Determine color based on active spans
                if active["subject"] > 0 and active["object"] > 0:
                    color = purple
                elif active["subject"] > 0:
                    color = blue
                elif active["predicate"] > 0:
                    color = yellow
                elif active["object"] > 0:
                    color = red
                else:
                    color = ""

                # Add text segment
                if color:
                    result.append(f"{color}{self.text[last_pos:pos]}{reset}")
                else:
                    result.append(self.text[last_pos:pos])

            active[span_type] += delta
            last_pos = pos

        # Add remaining text
        if last_pos < len(self.text):
            result.append(self.text[last_pos:])

        print("".join(result))
