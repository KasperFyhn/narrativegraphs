"""Run k-clique and Louvain community detection and inspect qualitative samples."""

import random
from contextlib import redirect_stdout

from config import DB_PATH
from sharedutils import compute_communities, output_path, print_comm_with_contexts

from narrativegraphs import CooccurrenceGraph

model = CooccurrenceGraph.load(DB_PATH)

k_clique_comms_with_contexts, k_clique_big_comms, louvain_comms_with_contexts = (
    compute_communities(model)
)

with open(output_path("04_community_detection.txt"), "w") as f, redirect_stdout(f):
    print("--- K-clique ---")
    print(f"Communities (excluding giant): {len(k_clique_comms_with_contexts)}")
    print(f"Giant communities: {len(k_clique_big_comms)}")
    print("Giant community sizes:", *[len(c.members) for c in k_clique_big_comms])

    print("\n--- Louvain ---")
    print(f"Communities: {len(louvain_comms_with_contexts)}")

    random.seed(42)
    for name, comms in [
        ("k-clique", k_clique_comms_with_contexts),
        ("louvain", louvain_comms_with_contexts),
    ]:
        print(f"\n=== {name} sample ===")
        for comm, contexts in random.choices(comms, k=10):
            print_comm_with_contexts(comm, contexts)
