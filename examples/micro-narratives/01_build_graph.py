"""Build or reload the CooccurrenceGraph from the prepared docs JSONL."""

import json
import os.path
from contextlib import redirect_stdout

from config import COREF, DB_PATH, DOCS_PATH, N_CPU
from sharedutils import output_path

from narrativegraphs import CooccurrenceGraph, SubgramLemmatizationMapper
from narrativegraphs.nlp.entities import SpacyEntityExtractor

with open(DOCS_PATH) as f:
    rows = [json.loads(line) for line in f]

docs = [r["text"] for r in rows]

if "timestamp_ordinal" in rows[0]:
    fit_kwargs = {"timestamps_ordinal": [r["timestamp_ordinal"] for r in rows]}
else:
    from datetime import date

    fit_kwargs = {
        "doc_ids": [r["id"] for r in rows],
        "timestamps": [date.fromisoformat(r["timestamp"]) for r in rows],
        "categories": [r["category"] for r in rows],
        "metadata": [r.get("metadata", {}) for r in rows],
    }

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if os.path.exists(DB_PATH):
    model = CooccurrenceGraph.load(DB_PATH)
else:
    model = CooccurrenceGraph(
        entity_extractor=SpacyEntityExtractor(
            model_name="en_core_web_lg",
            named_entities=True,
            noun_chunks=(2, None),
            coref_resolver=COREF,
        ),
        entity_mapper=SubgramLemmatizationMapper(
            head_word_type="noun",
            min_subgram_length=2,
            min_subgram_frequency=2,
            min_subgram_frequency_ratio=2,
        ),
        sqlite_db_path=DB_PATH,
        n_cpu=N_CPU,
    ).fit(docs, **fit_kwargs)

with open(output_path("01_build_graph.txt"), "w") as f, redirect_stdout(f):
    print(f"Documents: {len(docs)}")
    print(f"Entities: {len(model.entities_)}")
    print(f"Cooccurrences: {len(model.cooccurrences_)}")
