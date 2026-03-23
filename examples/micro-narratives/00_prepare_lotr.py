"""Prepare LotR text files for the analysis pipeline.

Splits raw text files into sections (paragraphs / scenes) using the configured
regex, assigns each section an ordinal timestamp, and writes a JSONL file
consumed by 01_build_graph.py.
"""

import glob
import json
import os
import re

out_path = "input/lotr_docs.jsonl"

section_splitter = re.compile(r"(?<=\S)\n\n(?=\S)|\n{3}")

docs = []
for file in sorted(glob.glob("input/0*.txt")):
    with open(file) as f:
        text = f.read()
    for section in section_splitter.split(text):
        section = section.strip()
        if section:
            docs.append(section)

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    for i, text in enumerate(docs):
        f.write(json.dumps({"text": text, "timestamp_ordinal": i}) + "\n")

print(f"Wrote {len(docs)} sections to {out_path}")
