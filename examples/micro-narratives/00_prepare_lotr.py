"""Prepare LotR text files for the analysis pipeline.

Splits raw text files into sections (paragraphs / scenes) using the configured
regex, assigns each section an ordinal timestamp, and writes a JSONL file
consumed by 01_build_graph.py.
"""

import glob
import json
import os
import re

from config import DOCS_PATH, INPUT_GLOB, SECTION_SPLIT_PATTERN

section_splitter = re.compile(SECTION_SPLIT_PATTERN)

docs = []
for file in sorted(glob.glob(INPUT_GLOB)):
    with open(file) as f:
        text = f.read()
    for section in section_splitter.split(text):
        section = section.strip()
        if section:
            docs.append(section)

os.makedirs(os.path.dirname(DOCS_PATH), exist_ok=True)
with open(DOCS_PATH, "w") as f:
    for i, text in enumerate(docs):
        f.write(json.dumps({"text": text, "timestamp_ordinal": i}) + "\n")

print(f"Wrote {len(docs)} sections to {DOCS_PATH}")
