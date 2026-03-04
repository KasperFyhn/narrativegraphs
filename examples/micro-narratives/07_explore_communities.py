"""Interactive exploration of micro-narratives by typology cell.

Each typology cell writes to a separate file in output/.
Typology prototypes:
  - Episodic:  low spread
  - Echoing:   high spread, few spikes  (re-activation of something from much earlier)
  - Recurring: high spread, many spikes (motifs, sub-plots)
"""

from contextlib import redirect_stdout

from config import DB_PATH
from sharedutils import (
    compute_communities,
    multi_spike_df,
    output_path,
    print_micro_narratives,
    spike_analysis,
)

from narrativegraphs import CooccurrenceGraph

model = CooccurrenceGraph.load(DB_PATH)

k_clique_comms_with_contexts, _, louvain_comms_with_contexts = compute_communities(
    model
)

k_clique_spikes, k_clique_spread = spike_analysis(k_clique_comms_with_contexts)
louvain_spikes, louvain_spread = spike_analysis(louvain_comms_with_contexts)

k_clique_df = multi_spike_df(k_clique_spikes, k_clique_spread)
louvain_df = multi_spike_df(louvain_spikes, louvain_spread)

# Each entry: (output filename, k-clique args, louvain args)
# Args: (min_spread, max_spread, min_spikes, max_spikes)
typology_cells = [
    (
        "07_episodic_low_spread.txt",
        (2, 10, 2, 4),
        (2, 4, 2, 4),
    ),
    (
        "07_echoing_moderate_spread.txt",
        (10, 100, 2, 4),
        (10, 100, 2, 4),
    ),
    (
        "07_echoing_high_spread.txt",
        (100, 1000, 2, 4),
        (100, 1000, 2, 4),
    ),
    (
        "07_recurring_local.txt",
        (2, 30, 4, 100),
        (2, 100, 4, 100),
    ),
    (
        "07_recurring_high_spread.txt",
        (100, 1000, 4, 16),
        (2, 100, 4, 16),
    ),
    (
        "07_recurring_many_spikes_kclique.txt",
        (100, 1000, 16, 100),
        None,  # k-clique only; Louvain has too few communities at this scale
    ),
]

for filename, k_args, l_args in typology_cells:
    with open(output_path(filename), "w") as f, redirect_stdout(f):
        print("--- k-clique ---")
        print_micro_narratives(k_clique_comms_with_contexts, k_clique_df, *k_args)
        if l_args is not None:
            print("--- louvain ---")
            print_micro_narratives(louvain_comms_with_contexts, louvain_df, *l_args)
