"""Typology of micro-narratives by spike count and temporal spread."""

from contextlib import redirect_stdout

from config import DB_PATH
from sharedutils import (
    compute_communities,
    multi_spike_df,
    multi_spike_heatmap,
    output_path,
    print_comm_with_contexts,
    spike_analysis,
)

from narrativegraphs import CooccurrenceGraph

model = CooccurrenceGraph.load(DB_PATH)

k_clique_comms_with_contexts, _, louvain_comms_with_contexts = compute_communities(
    model
)

k_clique_spikes, k_clique_spread = spike_analysis(k_clique_comms_with_contexts)
louvain_spikes, louvain_spread = spike_analysis(louvain_comms_with_contexts)

# --- Heatmaps ---
multi_spike_heatmap(
    multi_spike_df(k_clique_spikes, k_clique_spread),
    save_path=output_path("06_kclique_spread_vs_spikes.png"),
)
multi_spike_heatmap(
    multi_spike_df(louvain_spikes, louvain_spread),
    save_path=output_path("06_louvain_spread_vs_spikes.png"),
)


# --- Single-spike samples ---
def single_spike_sample(comms_with_contexts, spike_values, n_print=5):
    printed = 0
    for (comm, contexts), sv in zip(comms_with_contexts, spike_values):
        if sv > 1:
            continue
        print_comm_with_contexts(comm, contexts)
        printed += 1
        if printed >= n_print:
            break


with open(output_path("06_typology_single_spike.txt"), "w") as f, redirect_stdout(f):
    print(
        "K-clique single-spike communities:",
        sum(1 for sv in k_clique_spikes if sv == 1),
    )
    print(
        "Louvain single-spike communities:", sum(1 for sv in louvain_spikes if sv == 1)
    )

    print("\n--- K-clique single-spike sample ---\n")
    single_spike_sample(k_clique_comms_with_contexts, k_clique_spikes)

    print("\n--- Louvain single-spike sample ---\n")
    single_spike_sample(louvain_comms_with_contexts, louvain_spikes)
