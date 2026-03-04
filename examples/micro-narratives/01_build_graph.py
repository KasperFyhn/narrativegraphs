"""Load text sections and build (or reload) the CooccurrenceGraph."""

import glob
import os.path
import re
from contextlib import redirect_stdout

from config import DB_PATH, INPUT_GLOB, SECTION_SPLIT_PATTERN
from sharedutils import output_path

from narrativegraphs import CooccurrenceGraph
from narrativegraphs.nlp.entities import SpacyEntityExtractor
from narrativegraphs.nlp.mapping import SubgramStemmingMapper

docs = []
section_splitter = re.compile(SECTION_SPLIT_PATTERN)
for file in glob.glob(INPUT_GLOB):
    with open(file) as f:
        text = f.read()
        sections = section_splitter.split(text)
        for section in sections:
            section = section.strip()
            if section:
                docs.append(section)

if os.path.exists(DB_PATH):
    model = CooccurrenceGraph.load(DB_PATH)
else:
    model = CooccurrenceGraph(
        entity_extractor=SpacyEntityExtractor(
            model_name="en_core_web_lg",
            named_entities=True,
            noun_chunks=(2, None),
        ),
        entity_mapper=SubgramStemmingMapper(
            head_word_type="noun",
            min_subgram_length=2,
            min_subgram_frequency=2,
            min_subgram_frequency_ratio=2,
        ),
        sqlite_db_path=DB_PATH,
        n_cpu=1,
    ).fit(docs, timestamps_ordinal=list(range(len(docs))))

with open(output_path("01_build_graph.txt"), "w") as f, redirect_stdout(f):
    print(f"Input files: {len(glob.glob(INPUT_GLOB))}")
    print(f"Sections: {len(docs)}")
    print(f"Entities: {len(model.entities_)}")
    print(f"Cooccurrences: {len(model.cooccurrences_)}")

# Uncomment to launch the interactive visualizer:
# model.serve_visualizer()
