"""Typology of micro-narratives by spike count and temporal spread."""

from contextlib import redirect_stdout

from config import DB_PATH
from sharedutils import (
    compute_communities,
    multi_spike_df,
    multi_spike_heatmap,
    output_path,
    print_comm_with_contexts,
    print_micro_narratives,
    spike_analysis,
)

from narrativegraphs import CooccurrenceGraph

model = CooccurrenceGraph.load(DB_PATH)

k_clique_comms_with_contexts, _, louvain_comms_with_contexts = compute_communities(
    model
)

k_clique_spikes, k_clique_spread = spike_analysis(k_clique_comms_with_contexts, model)
louvain_spikes, louvain_spread = spike_analysis(louvain_comms_with_contexts, model)


# --- Single-spike samples ---
def single_spike_sample(comms_with_contexts, spike_values):
    for (comm, contexts), sv in zip(comms_with_contexts, spike_values):
        if sv > 1:
            continue
        print_comm_with_contexts(comm, contexts)


with open(output_path("06_single_spike_k_clique.txt"), "w") as f, redirect_stdout(f):
    print("K-clique single-spike comms:", sum(1 for sv in k_clique_spikes if sv == 1))
    single_spike_sample(k_clique_comms_with_contexts, k_clique_spikes)

with open(output_path("06_single_spike_louvain.txt"), "w") as f, redirect_stdout(f):
    print("Louvain single-spike comms:", sum(1 for sv in louvain_spikes if sv == 1))
    single_spike_sample(louvain_comms_with_contexts, louvain_spikes)


k_clique_df = multi_spike_df(k_clique_spikes, k_clique_spread)
louvain_df = multi_spike_df(louvain_spikes, louvain_spread)

# --- Heatmaps ---
multi_spike_heatmap(
    k_clique_df,
    save_path=output_path("06_kclique_spread_vs_spikes.png"),
)
multi_spike_heatmap(
    louvain_df,
    save_path=output_path("06_louvain_spread_vs_spikes.png"),
)


# Each entry: (output filename, k-clique args, louvain args)
# Args: (min_spread, max_spread, min_spikes, max_spikes)
typology_cells = [
    ("06_episodic_low_spread.txt", (2, 10, 2, 4)),
    ("06_episodic_sustained.txt", (2, 30, 4, 30)),
    ("06_echoing_moderate_spread.txt", (10, 100, 2, 4)),
    ("06_echoing_high_spread.txt", (100, 1000, 2, 4)),
    ("06_recurring_moderate_spread.txt", (30, 100, 4, 16)),
    ("06_recurring_high_spread.txt", (100, 1000, 4, 16)),
    ("06_recurring_many_spikes.txt", (100, 1000, 16, 100)),
]

for filename, k_args in typology_cells:
    with open(output_path(filename), "w") as f, redirect_stdout(f):
        print("--- k-clique ---")
        print_micro_narratives(k_clique_comms_with_contexts, k_clique_df, *k_args)
