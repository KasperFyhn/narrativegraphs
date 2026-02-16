import json
import time
from pathlib import Path

import kagglehub
import requests
from kagglehub import KaggleDatasetAdapter

data = kagglehub.dataset_load(
    KaggleDatasetAdapter.PANDAS,
    "armitaraz/chatgpt-reddit",
    "chatgpt-reddit-comments.csv",
).dropna()
comment_ids = data.comment_id


headers = {"User-Agent": "narrativegraphs/1.0"}
output_file = Path("input", "chatgpt-reddit-comments.jsonl")

# Figure out which IDs we already have
done = set()
if output_file.exists():
    with open(output_file) as f:
        for line in f:
            done.add(json.loads(line)["id"])
print(f"Already fetched: {len(done)}")

remaining = [cid for cid in comment_ids if cid not in done]
batches = [remaining[i : i + 100] for i in range(0, len(remaining), 100)]

with open(output_file, "a") as f:
    for i, batch in enumerate(batches):
        fullnames = ",".join(f"t1_{cid}" for cid in batch)
        resp = requests.get(
            f"https://www.reddit.com/api/info.json?id={fullnames}",
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        for child in data["data"]["children"]:
            f.write(json.dumps(child["data"]) + "\n")
        f.flush()
        print(f"Batch {i + 1}/{len(batches)} done")
        time.sleep(6)

print("Done")
