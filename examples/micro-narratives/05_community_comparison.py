"""Compare k-clique and Louvain community detection: sizes, overlap, membership."""

from collections import Counter
from contextlib import redirect_stdout

import matplotlib.pyplot as plt
import numpy as np
from config import DB_PATH
from sharedutils import compute_communities, output_path

from narrativegraphs import CooccurrenceGraph


def coverage(list_a: list[set], list_b: list[set]) -> float:
    scores = []
    lengths = []
    for a in list_a:
        if not a:
            continue
        best = max(len(a & b) / len(a) for b in list_b)
        scores.append(best)
        lengths.append(len(a))
    return sum(score * length for score, length in zip(scores, lengths)) / sum(lengths)


def best_overlap(a: set[int], list_b: list[set[int]]):
    best_index, best_score = None, 0
    for i, b in enumerate(list_b):
        score = len(a & b) / len(a)
        if score > best_score:
            best_index = i
            best_score = score
    return best_index, best_score


model = CooccurrenceGraph.load(DB_PATH)

k_clique_comms_with_contexts, k_clique_big_comms, louvain_comms_with_contexts = (
    compute_communities(model)
)

comms_by_method = {
    "k_clique": k_clique_comms_with_contexts,
    "louvain": louvain_comms_with_contexts,
}
sizes_by_method = {
    method: [len(comm.members) for comm, _ in comms]
    for method, comms in comms_by_method.items()
}

# --- Size distribution figure ---
fig, ax = plt.subplots(figsize=(14, 5))
for method, sizes in sizes_by_method.items():
    ax.hist(sizes, bins=30, alpha=0.5, label=method, density=True)
ax.set_xlabel("Community size")
ax.set_ylabel("Density")
ax.set_title("Community size distribution")
ax.legend()
plt.tight_layout()
fig.savefig(output_path("05_community_size_distribution.png"), bbox_inches="tight")
plt.close(fig)

# --- Text stats ---
k_clique_sets = [
    {e.id for e in comm.members} for comm, _ in k_clique_comms_with_contexts
]
louvain_sets = [{e.id for e in comm.members} for comm, _ in louvain_comms_with_contexts]
k_clique_big_sets = [{e.id for e in comm.members} for comm in k_clique_big_comms]

k_clique_membership_counter = Counter(
    e.id for comm, _ in k_clique_comms_with_contexts for e in comm.members
)

with open(output_path("05_community_comparison.txt"), "w") as f, redirect_stdout(f):
    for name, sizes in sizes_by_method.items():
        print(name)
        print("N:", len(sizes))
        print("Mean:", np.mean(sizes))
        print("Min:", np.min(sizes))
        print("Q1:", np.quantile(sizes, 0.25))
        print("Median:", np.median(sizes))
        print("Q3:", np.quantile(sizes, 0.75))
        print("Max:", np.max(sizes))
        print()

    print(
        "Mean k-clique membership per entity:",
        np.mean(list(k_clique_membership_counter.values())),
    )
    print(
        "Median k-clique membership per entity:",
        np.median(list(k_clique_membership_counter.values())),
    )

    print("\nk-clique covered by Louvain:", coverage(k_clique_sets, louvain_sets))
    print("Louvain covered by k-clique:", coverage(louvain_sets, k_clique_sets))
    if k_clique_big_sets:
        print(
            "Louvain covered by giant k-clique comm:",
            coverage(louvain_sets, k_clique_big_sets),
        )
