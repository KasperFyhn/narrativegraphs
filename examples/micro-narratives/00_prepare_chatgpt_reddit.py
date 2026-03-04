"""Prepare ChatGPT Reddit comments for the analysis pipeline.

Reads the raw JSONL dump, extracts text, identifiers, timestamps, subreddit
categories, and per-comment metadata, and writes a JSONL file consumed by
01_build_graph.py.
"""

import json
import os
from datetime import date

import pandas as pd
from config import DOCS_PATH, INPUT_GLOB

data = pd.read_json(INPUT_GLOB, lines=True)

os.makedirs(os.path.dirname(DOCS_PATH), exist_ok=True)
with open(DOCS_PATH, "w") as f:
    for _, row in data.iterrows():
        record = {
            "text": row["body"],
            "id": row["id"],
            "timestamp": date.fromtimestamp(row["created_utc"]).isoformat(),
            "category": row["subreddit"],
            "metadata": {
                "author": row["author"],
                "score": int(row["score"]),
                "parent_id": row["parent_id"],
            },
        }
        f.write(json.dumps(record) + "\n")

print(f"Wrote {len(data)} comments to {DOCS_PATH}")
